# Cropwater Compass – Setup & Execution Guide
## Complete Installation, Configuration, and Testing Manual

---

## 1. System Requirements & Prerequisites

- **Operating System**: Windows 10/11, Ubuntu 20.04+, or macOS
- **Python**: Python 3.13 (or Python 3.11+)
- **Node.js**: v18.0.0 or v20.0.0+ with npm (v9+)
- **Git**: v2.30+
- **Memory**: Minimum 4 GB RAM (8 GB recommended for training)

---

## 2. Repository Cloning & Environment Setup

### Step 1: Clone the Repository
```powershell
git clone https://github.com/Ravi-M-2005/Cropwater-Compass.git
cd Cropwater-Compass
```

---

## 3. Backend Setup (FastAPI & Machine Learning)

The backend uses Python 3.13 with an isolated virtual environment (`.venv`).

### Step 1: Activate Virtual Environment
On **Windows (PowerShell)**:
```powershell
.\.venv\Scripts\Activate.ps1
```
*(If execution policies block scripts, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`)*

On **Linux / macOS (Bash)**:
```bash
source .venv/bin/activate
```

### Step 2: Install Python Dependencies
```powershell
pip install -r backend/requirements.txt
```
Key libraries installed:
- `fastapi`, `uvicorn`, `pydantic`
- `pandas`, `numpy`, `scikit-learn`
- `xgboost`, `torch` (CPU), `shap`
- `pytest`, `requests`, `python-multipart`

### Step 3: Run Automated Test Suite
Ensure all 27 unit, integration, and E2E tests pass:
```powershell
python -m pytest -v
```
Expected output:
```text
======================= 27 passed in ~14s =======================
```

### Step 4: (Optional) Retrain Machine Learning Models
To retrain XGBoost, ANN, and LSTM models and regenerate SHAP explainers:
```powershell
python ml/train.py
```
Model binaries and metrics are saved to `ml/saved_models/`.

### Step 5: Start FastAPI Server
```powershell
python -m uvicorn backend.app.main:app --reload --port 8000
```
- API Base: [http://localhost:8000](http://localhost:8000)
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Interactive ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Healthcheck Endpoint: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 4. Frontend Setup (React, Vite, TypeScript, Tailwind)

### Step 1: Ensure Node.js & npm are in PATH
If using the local portable Node.js installation on Windows:
```powershell
$env:PATH = "$env:LOCALAPPDATA\Programs\nodejs;$env:PATH"
```
Verify versions:
```powershell
node -v   # e.g., v20.18.0
npm -v    # e.g., 10.8.2
```

### Step 2: Navigate to Frontend Directory & Install Packages
```powershell
cd frontend
npm install
```

### Step 3: Start Vite Development Server
```powershell
npm run dev
```
The application will launch on:
- [http://localhost:5173](http://localhost:5173)

### Step 4: Production Build Verification
To compile TypeScript and create an optimized production build:
```powershell
npm run build
```
Assets are built into `frontend/dist/`.

To preview the production build locally:
```powershell
npm run preview
```

---

## 5. End-to-End Application Verification

Once both servers are running:
1. Open [http://localhost:5173](http://localhost:5173) in your browser.
2. Confirm the green **System Online** status badge appears in the top navigation.
3. Navigate to **Irrigation Prediction**:
   - Select **Wheat**, **Mid-Season**, **Loamy** soil, and **Drip** irrigation.
   - Click **Live Weather Auto-Fill** to fetch meteorological parameters.
   - Click **Calculate Irrigation Requirement**.
   - Confirm the result card displays the exact water requirement in **Litres** (e.g. `124,500 Litres`), $m^3$, and $mm$.
4. Navigate to **ML Model Comparison** and confirm live benchmarks for XGBoost, ANN, and LSTM match the saved evaluation metrics.
5. Navigate to **Explainability** and inspect the SHAP feature importance chart.
6. Navigate to **Dataset Management** and upload a CSV file or download the sample template.
7. Navigate to **Prediction History** to inspect your saved prediction.
8. Navigate to **Reports** and test the **Print / Save PDF Report** view.

---

## 6. Troubleshooting & Common Questions

### Q: Port 8000 or 5173 is already in use
**Fix**: Terminate the lingering process or specify an alternate port:
```powershell
# For backend
python -m uvicorn backend.app.main:app --reload --port 8080

# For frontend
npm run dev -- --port 3000
```

### Q: Node or npm not recognized on Windows
**Fix**: Ensure Node.js is added to your PowerShell session:
```powershell
$env:PATH = "$env:LOCALAPPDATA\Programs\nodejs;$env:PATH"
```

### Q: SQLite database locking error
**Fix**: Cropwater Compass uses SQLite WAL (Write-Ahead Logging) mode and manages context managers cleanly. Ensure only one write operation runs concurrently. The database file is located at `backend/data/cropwater.db`.
