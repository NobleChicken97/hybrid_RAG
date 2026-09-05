# AWS Deployment

## LIVE DEPLOYMENT RECORD (Lightsail — in progress since 2026-09-05)

> Read this first. The EC2 `t4g.small` runbook below is SUPERSEDED — the
> deployment decision changed to Lightsail (see `docs/prod.md`). The box-level
> steps (Docker, clone, compose) are provider-agnostic and still valid; the
> "Launch the instance" step is not — use the record below instead.

- Provider / service: AWS Lightsail
- Instance name: `hybrid-rag-prod`
- Blueprint: Ubuntu 22.04 LTS (OS Only — no app blueprint; 24.04 was planned but 22.04 is what shipped — irrelevant, stack runs in Docker)
- Docker: CE 29.8.0 + compose plugin 5.5.1 from Docker's official repo (`docker-compose-plugin` is not in Ubuntu 22.04's default repos)
- Plan type: general_purpose, 4 GB RAM / 2 vCPU tier
- Network: dual-stack (public IPv4 + IPv6)
- Automatic snapshots: ON (daily — cheapest DR for local ChromaDB/SQLite state)
- SSH key pair (Lightsail account): `trakplus-lightsail`
- Local copy of the private key: `C:\Users\arpan.ARPAN\.ssh\trakplus-lightsail.pem`
- SSH user: `ubuntu`
- Static IP: `65.2.210.233` (attached 2026-09-05)
- Domain / A record → static IP: `rag.noblechicken.me` → `65.2.210.233` (Namecheap A record, TTL Automatic; verified via nslookup 2026-09-05)
- TLS: Caddy automatic Let's Encrypt once the domain resolves to the box
- LLM keys on the box: `GEMINI_API_KEY` + `GROQ_API_KEY` (matches config defaults: gemini flash-lite primary, groq fallback)
- Eval guard: `EVAL_TOKEN` (random hex, appended to box `.env`) — prod `POST /eval/run` requires header `x-eval-token: <token>`, else 403. Empty locally = open (dev/tests unaffected).
- Prod eval: full Groq-backed run pending (Gemini free bucket too small for ~100 calls); run ID to be recorded in todos when done
- Status: LIVE 2026-09-05 — build green (backend + web Healthy, Caddy TLS issued for rag.noblechicken.me); prod ingest verified (`Sample FastAPI Guide`, 20 chunks); live prod query verified (correct answer + 2 citations + retrieval debug, gemini backend). Remaining: prod eval re-run, restart persistence check, README live-URL update. Known issue: web UI styling judged poor — redesign IMPLEMENTED 2026-09-05 (dark-first design system, Jost/Mulish/JetBrains Mono, build green) but NOT YET DEPLOYED — box still serves the old UI until `git pull` + `up -d --build` is run there.

SSH from the dev machine (PowerShell):

```powershell
ssh -i C:\Users\arpan.ARPAN\.ssh\trakplus-lightsail.pem ubuntu@<STATIC_IP>
```

---

## Original EC2 runbook (superseded — kept for reference)

Target: **EC2 `t4g.small`** (2 vCPU ARM Graviton, 2 GB RAM, us-east-1 pricing)
— compute ≈ **$12.27/mo** + 20 GB gp3 disk ≈ **$1.60/mo** = **~$13.90/mo**, inside the $10–15 budget.

> Why not bigger: the stack needs ~4 GB comfortably, but with 2 GB **plus 2 GB swap**
> (step 4) it runs fine for a demo. Why not Lightsail: the 2 GB tier is $20/mo — over budget.

---

## 1. Launch the instance (AWS Console, ~5 min)

1. **EC2 → Instances → Launch instances**
   - Name: `hybrid-rag`
   - **AMI**: Ubuntu Server 24.04 LTS, **Arm64** (important — t4g is ARM)
   - **Instance type**: `t4g.small`
   - **Key pair**: Create new → download the `.pem` file, keep it safe
   - **Network**: default VPC; **Edit security group**:
     - SSH (22) → Source: *My IP*
     - HTTP (80) → Source: *Anywhere-IPv4* (`0.0.0.0/0`)
     - HTTPS (443) → Source: *Anywhere-IPv4* (`0.0.0.0/0`)
   - **Storage**: 20 GB `gp3`
2. Launch, then note the **Public IPv4 address**.

## 2. Connect + prep the box (one time, ~3 min)

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<PUBLIC_IP>
```

Add 2 GB swap (2 GB RAM alone is tight with the models loaded):

```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile \
  && sudo mkswap /swapfile && sudo swapon /swapfile \
  && echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Install Docker:

```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-v2
sudo usermod -aG docker ubuntu   # then log out and back in
```

## 3. Get the code + secrets onto the server

From **your machine** (not the server): push this repo to GitHub, then copy your
`.env` (it is gitignored — keys must travel separately):

```bash
scp -i your-key.pem .env ubuntu@<PUBLIC_IP>:~/hybrid-rag/.env
```

On the **server**:

```bash
git clone https://github.com/<you>/<repo>.git hybrid-rag
cd hybrid-rag
# (if you scp'd .env before cloning, move it into place instead)
```

## 4. Build and start (first build ~5–10 min on t4g)

```bash
docker compose -f deploy/docker-compose.yml up -d --build
docker compose -f deploy/docker-compose.yml ps       # all 3 services Up/healthy
curl -s http://localhost/health                      # (or via caddy) http://localhost:8000/health from inside
```

Then open **`http://<PUBLIC_IP>`** — that's the Next.js UI; browser API calls
go to the same origin under `/api/*`, which Caddy strips and proxies to the
backend over the internal Docker network (no CORS or hostname issues).

Verify: `docker compose -f deploy/docker-compose.yml logs -f backend` shows
`[Embedder] Model loaded` once, then `Uvicorn running`.

## 5. Optional: HTTPS with a free domain

1. Get a free hostname at [duckdns.org](https://duckdns.org) (e.g. `arpan-rag.duckdns.org` → your EC2 IP).
2. In `deploy/.env` next to the compose file: `DOMAIN=arpan-rag.duckdns.org`
3. `docker compose -f deploy/docker-compose.yml up -d caddy` → Caddy auto-issues
   and renews a Let's Encrypt certificate. Done — `https://arpan-rag.duckdns.org`.

## Ongoing costs

| Item | ~$/month |
|---|---|
| t4g.small (always-on) | 12.27 |
| 20 GB gp3 root volume | 1.60 |
| Data transfer (demo traffic) | ~0 |
| **Total** | **~13.90** |

Your credits cover this. To stop billing while idle:
`sudo shutdown now` (stopped instances pay only for disk, ~$1.60/mo) — restart from the console later; data persists on the volume.

## Updating the deployment

```bash
cd ~/hybrid-rag && git pull
docker compose -f deploy/docker-compose.yml up -d --build
```

## Troubleshooting

- **Backend restarts / OOM**: confirm swap is on (`free -h` shows 2G swap).
- **502 from Caddy**: `docker compose -f deploy/docker-compose.yml logs web` — the UI is usually up but backend not yet healthy; wait for the healthcheck.
- **Rollback to Streamlit**: `frontend/` is still in the repo/image; re-add a `streamlit` service (pre-cutover compose had one on `:8501`) and point the Caddyfile's fallback `reverse_proxy` back at `streamlit:8501`.
- **Port 80/443 unreachable**: check the instance's security group allows 80+443 from `0.0.0.0/0` and your DuckDNS IP matches.
