document.addEventListener('DOMContentLoaded', async () => {
  const backendUrlInput = document.getElementById('backend-url');
  const healthDot = document.getElementById('health-dot');
  const loading = document.getElementById('health-loading');
  const errorMsg = document.getElementById('health-error');
  const content = document.getElementById('health-content');

  // Load saved URL or default
  const savedUrl = localStorage.getItem('backendUrl') || 'http://localhost:8000';
  if (backendUrlInput) {
    backendUrlInput.value = savedUrl;
    backendUrlInput.addEventListener('change', (e) => {
      localStorage.setItem('backendUrl', e.target.value);
      checkHealth(e.target.value);
    });
  }

  async function checkHealth(url) {
    if (loading) loading.style.display = 'flex';
    if (errorMsg) errorMsg.style.display = 'none';
    if (content) content.style.display = 'none';
    if (healthDot) healthDot.style.backgroundColor = '#e5e7eb'; // default gray

    try {
      const response = await fetch(`${url}/health`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      
      const docsCount = document.getElementById('docs-count') || document.getElementById('home-docs-count');
      if (docsCount) docsCount.textContent = (data.documents_count || 0).toLocaleString();
      
      const chunksCount = document.getElementById('chunks-count') || document.getElementById('home-chunks-count');
      if (chunksCount) chunksCount.textContent = (data.chunks_count || 0).toLocaleString();
      
      const evalsCount = document.getElementById('evals-count') || document.getElementById('home-evals-count');
      if (evalsCount) evalsCount.textContent = (data.eval_runs_count || 0).toLocaleString();
      
      const envBadge = document.getElementById('env-badge');
      const envMessage = document.getElementById('env-message');
      if (envBadge) {
        envBadge.textContent = data.environment;
        if (data.environment === 'production') {
          envBadge.style.backgroundColor = '#fef2f2';
          envBadge.style.color = '#dc2626';
          if (envMessage) envMessage.textContent = 'Production Mode: Local models disabled.';
        } else {
          envBadge.style.backgroundColor = 'var(--color-linen)';
          envBadge.style.color = 'var(--color-forest-ink)';
          if (envMessage) envMessage.textContent = 'Local models active.';
        }
      }

      const llmBackend = document.getElementById('llm-backend');
      if (llmBackend) llmBackend.textContent = data.llm_backend || 'Ollama (Local)';

      if (loading) loading.style.display = 'none';
      if (content) content.style.display = 'block';
      if (healthDot) healthDot.style.backgroundColor = 'var(--color-forest-ink)'; // green/healthy
      
      // Update gauges on home page
      const g1 = document.getElementById('home-gauge-1');
      if (g1) { g1.textContent = "100%"; g1.style.borderColor = "var(--color-forest-ink)"; }
      const g2 = document.getElementById('home-gauge-2');
      if (g2) { g2.textContent = "SYNC"; g2.style.borderColor = "var(--color-forest-ink)"; }
      const g3 = document.getElementById('home-gauge-3');
      if (g3) { g3.textContent = "PASS"; g3.style.borderColor = "var(--color-forest-ink)"; }

    } catch (e) {
      if (loading) loading.style.display = 'none';
      if (errorMsg) {
        errorMsg.textContent = `Cannot connect to backend. Make sure the FastAPI server is running on ${url}`;
        errorMsg.style.display = 'block';
      }
      if (healthDot) healthDot.style.backgroundColor = '#dc2626'; // red/disconnected
      
      const g1 = document.getElementById('home-gauge-1');
      if (g1) { g1.textContent = "ERR"; g1.style.borderColor = "#dc2626"; }
      const g2 = document.getElementById('home-gauge-2');
      if (g2) { g2.textContent = "ERR"; g2.style.borderColor = "#dc2626"; }
      const g3 = document.getElementById('home-gauge-3');
      if (g3) { g3.textContent = "ERR"; g3.style.borderColor = "#dc2626"; }
    }
  }

  checkHealth(savedUrl);
});
