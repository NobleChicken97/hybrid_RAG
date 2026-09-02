"""
Convenience script to run both the FastAPI backend and Streamlit frontend.

Usage:
    python run.py          # Both backend + frontend
    python run.py backend  # Only backend
    python run.py frontend # Only frontend
"""

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def run_backend():
    """Start the FastAPI backend with uvicorn."""
    return subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
        ],
        cwd=str(PROJECT_ROOT),
    )


def run_frontend():
    """Start the Streamlit frontend."""
    return subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run",
            "frontend/app.py",
            "--server.port", "8501",
            "--server.headless", "true",
        ],
        cwd=str(PROJECT_ROOT),
    )


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    processes = []

    try:
        if mode in ("both", "backend"):
            print("[Runner] Starting FastAPI backend on http://localhost:8000")
            processes.append(run_backend())
            time.sleep(2)

        if mode in ("both", "frontend"):
            print("[Runner] Starting Streamlit frontend on http://localhost:8501")
            processes.append(run_frontend())

        print("\n[Runner] Services running. Press Ctrl+C to stop.\n")

        # Wait for any process to exit
        for p in processes:
            p.wait()

    except KeyboardInterrupt:
        print("\n[Runner] Shutting down...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.wait()
        print("[Runner] All services stopped.")


if __name__ == "__main__":
    main()
