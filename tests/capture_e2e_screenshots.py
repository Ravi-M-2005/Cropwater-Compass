"""
E2E Browser Screenshot Capture Script
Boots backend and frontend, visits each module with headless Chrome/Edge,
and captures high-resolution screenshots to the artifact directory.
"""
import os
import sys
import time
import subprocess
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = Path(os.environ.get("CROPWATER_ARTIFACT_DIR", PROJECT_ROOT / "docs" / "images"))

# Chrome or Edge executable
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

PYTHON_EXE = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
NODE_PATH = os.path.expandvars(r"%LOCALAPPDATA%\Programs\nodejs")


def wait_for_url(url, timeout=15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as res:
                if res.status in (200, 304):
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main():
    print(f"Artifact directory: {ARTIFACT_DIR}")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Start FastAPI backend on 8000
    print("Starting FastAPI backend...")
    env = os.environ.copy()
    backend_proc = subprocess.Popen(
        [str(PYTHON_EXE), "-m", "uvicorn", "backend.app.main:app", "--port", "8000"],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # 2. Start Vite preview on 5173
    print("Starting Vite frontend server on port 5173...")
    env["PATH"] = f"{NODE_PATH};{env.get('PATH', '')}"
    npm_cmd = os.path.join(NODE_PATH, "npm.cmd")
    frontend_proc = subprocess.Popen(
        f'"{npm_cmd}" run preview -- --host 127.0.0.1 --port 5173',
        cwd=str(PROJECT_ROOT / "frontend"),
        env=env,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    try:
        # Wait for both servers
        print("Waiting for backend (http://127.0.0.1:8000/api/health)...")
        if not wait_for_url("http://127.0.0.1:8000/api/health", 15):
            print("ERROR: Backend did not start in time!")
            return 1
        print("Backend is online!")

        print("Waiting for frontend (http://127.0.0.1:5173)...")
        if not wait_for_url("http://127.0.0.1:5173", 15):
            print("ERROR: Frontend did not start in time!")
            return 1
        print("Frontend is online!")

        # Allow hydration
        time.sleep(2)

        # 3. Capture screenshots
        modules = [
            ("dashboard_screenshot.png", "http://localhost:5173/#dashboard"),
            ("prediction_screenshot.png", "http://localhost:5173/#predict"),
            ("models_screenshot.png", "http://localhost:5173/#models"),
            ("explainability_screenshot.png", "http://localhost:5173/#explainability"),
            ("weather_screenshot.png", "http://localhost:5173/#weather"),
            ("dataset_screenshot.png", "http://localhost:5173/#dataset"),
            ("history_screenshot.png", "http://localhost:5173/#history"),
            ("reports_screenshot.png", "http://localhost:5173/#reports"),
        ]

        for filename, url in modules:
            out_file = ARTIFACT_DIR / filename
            print(f"Capturing: {filename} from {url}...")
            cmd = [
                CHROME_PATH,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--window-size=1280,850",
                f"--screenshot={str(out_file)}",
                url
            ]
            subprocess.run(cmd, timeout=12, check=False)
            if out_file.exists():
                print(f"  -> Successfully captured {filename} ({out_file.stat().st_size / 1024:.1f} KB)")
            else:
                print(f"  -> Warning: Failed to save {filename}")

        print("All screenshots successfully captured!")

    finally:
        print("Stopping servers...")
        try:
            backend_proc.terminate()
            backend_proc.kill()
        except Exception:
            pass
        try:
            frontend_proc.terminate()
            frontend_proc.kill()
            # Kill any orphaned node/vite processes on 5173
            subprocess.run(["cmd.exe", "/c", "taskkill /f /im node.exe"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main() or 0)
