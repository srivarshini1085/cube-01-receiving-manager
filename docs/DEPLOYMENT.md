# INBOUNDSHIELD AI — Deployment & Infrastructure Guide

---

## 1. System Requirements

* **Python:** 3.11+ (Python 3.13 tested and verified)
* **Node.js:** 18+ (Node 22 tested with npm)
* **Database:** MySQL 8+ (Enterprise) or SQLite (Local development / CI)

---

## 2. Local Full-Stack Execution

### Step 1: Backend Setup
```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 2: Frontend Setup
```bash
cd frontend
npm install
npm run build
```
Open **`http://localhost:8000`** in your browser to access the complete application.

---

## 3. Database Configuration (MySQL 8+)

To connect to an active MySQL 8+ server:
1. Configure credentials in `backend/.env`:
   ```bash
   DATABASE_URL=mysql+pymysql://inbound_user:strongpassword@localhost:3306/inboundshield
   ```
2. Run database migrations:
   ```bash
   alembic upgrade head
   ```
3. If no MySQL database URL is provided, the application automatically initializes a self-contained local SQLite database (`inboundshield.db`) with Foreign Key pragmas enabled.

---

## 4. Storage Provider Options (Section 7)

Configure `STORAGE_PROVIDER` in `.env`:
* **`local` (Default):** Writes image binaries to disk in `uploads/{org_id}/` and serves via `/api/v1/inspections/{id}/images/{img_id}/bytes`.
* **`data_uri` (Serverless / Vercel):** Ideal for ephemeral serverless lambdas. Encodes photographs as resilient inline Data URIs, guaranteeing previews never fail or 404.

---

## 5. Vision AI Provider Configuration (Section 11)

Configure `VISION_PROVIDER` in `.env`:
* **`hybrid` (Recommended):** Uses Google Gemini 2.5 Flash if `GEMINI_API_KEY` is present; seamlessly falls back to local Perceptual Computer Vision if offline.
* **`gemini`:** Strictly uses Gemini Multimodal Vision API.
* **`local_cv`:** Operates 100% offline using PIL and image statistics (Laplacian variance, saturation, color histograms).

---

## 6. Vercel Cloud Deployment

The repository includes a production-ready `vercel.json`:
```json
{
  "services": {
    "frontend": {
      "root": "frontend/",
      "framework": "vite"
    },
    "backend": {
      "root": "backend/",
      "entrypoint": "app.main:app"
    }
  },
  "rewrites": [
    { "source": "/api/:path*", "destination": { "service": "backend" } },
    { "source": "/(.*)", "destination": { "service": "frontend" } }
  ]
}
```
Set environment variables in the Vercel dashboard:
* `STORAGE_PROVIDER=data_uri`
* `APP_ENV=production`
* `GEMINI_API_KEY=<your-key>`
