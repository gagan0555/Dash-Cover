# 🚀 Dash-Cover: Local Testing & Setup Guide

This guide provides instructions to successfully run the Dash-Cover project on your local machine, along with troubleshooting steps for common issues you might encounter.

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your machine:

1. **Python 3.9 or higher** — Required for the FastAPI backend.
2. **Node.js (v18+) & App Manager (npm)** — Required for the React/Vite frontend.
3. **Git** — For cloning the repository.

---

## 🛠️ Installation & Setup

Dash-Cover is divided into two parts: a Python backend and a React frontend. You will need to open **two separate terminal windows** to run both simultaneously.

### 1. Backend Setup (FastAPI)

Open your first terminal and navigate to the project root, then proceed into the `backend` directory:

```bash
cd backend
```

**Step A: Create and activate a virtual environment**
- **Windows:** `python -m venv venv` then `venv\Scripts\activate`
- **Mac/Linux:** `python3 -m venv venv` then `source venv/bin/activate`

**Step B: Install Dependencies**
```bash
pip install -r requirements.txt
```

**Step C: Start the Python Server**
```bash
uvicorn main:app --reload
```
*The backend should now be running on `http://127.0.0.1:8000`*

### 2. Frontend Setup (React/Vite)

Open your second terminal and navigate to the `frontend` directory:

```bash
cd frontend
```

**Step A: Install Node Dependencies**
```bash
npm install
```

**Step B: Start the Development Server**
```bash
npm run dev
```
*The frontend should now be running on `http://localhost:5173`*

Open `http://localhost:5173` in your browser to view the application!

---

## ⚠️ Common Errors & Troubleshooting

### 1. `uvicorn is not recognized as an internal or external command`
**Cause:** Your Python virtual environment is not activated, or uvicorn wasn't installed correctly.
**Fix:** Make sure you see `(venv)` preceding your terminal entry line. Run `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux) before running the uvicorn command.

### 2. "Network Error" / CORS Issues / Data Not Loading on Dashboard
**Cause:** The frontend is unable to reach the backend.
**Fix:** 
- Verify that your backend terminal is actively running and hasn't crashed.
- Check `frontend/src/config.js` or API calls to ensure the `API_BASE_URL` is pointing correctly to `http://localhost:8000`/`http://127.0.0.1:8000`.

### 3. "Port 8000 is already in use" or "Port 5173 is in use"
**Cause:** Another application (or an old instance of Dash-Cover) is already running on those ports.
**Fix:** Kill the process running on that port. 
- *To run on a different port (Backend):* `uvicorn main:app --reload --port 8001`
- *To run on a different port (Frontend):* `npm run dev -- --port 5174`

### 4. Supabase Client Credentials Error
**Cause:** The `supabase_client.py` is actively checking for environment variables (`SUPABASE_URL`, `SUPABASE_KEY`) that you haven't set yet.
**Fix:** Since the current build uses simulated mock data stores for testing, you can ignore these warnings. If it completely crashes, verify that there is an empty `.env` or dummy credentials supplied in a `.env` file within the `backend/` folder.

### 5. `npm ERR! code ERESOLVE` during Frontend install
**Cause:** Conflicting dependency versions between specific React packages (often Leaflet or Framer Motion).
**Fix:** Run `npm install --legacy-peer-deps` to bypass the strict dependency tree check.

### 6. Zone Risk Map appearing Blank / Only showing text
**Cause:** Leaflet Maps can occasionally fail to cache tiles locally if Strict Mode drops initialization. 
**Fix:** Ensure you have an active internet connection (the map tiles are pulled live from `cartocdn.com`). Perform a hard refresh (`Ctrl + F5` or `Cmd + Shift + R`) on the Admin Panel page. 
