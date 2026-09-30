import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.database import init_db, SessionLocal
from app.services.seed_service import seed_database_from_csv
from app.services.fixture_generator import generate_all_scenario_fixtures

from app.api.health import router as health_router
from app.api.receiving import router as receiving_router
from app.api.purchase_orders import router as po_router
from app.api.seed import router as seed_router
from app.api.scenarios import router as scenarios_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    init_db()
    # Seed default dataset if database is freshly initialized
    db = SessionLocal()
    try:
        seed_database_from_csv(db)
        generate_all_scenario_fixtures()
    finally:
        db.close()
    yield


app = FastAPI(
    title="INBOUNDSHIELD AI — Receiving Manager",
    description="Evidence-First AI Receiving Manager for Commerce Context Stream (Cube Buildathon)",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware for React / Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health_router)
app.include_router(receiving_router)
app.include_router(po_router)
app.include_router(seed_router)
app.include_router(scenarios_router)

# Mount fixtures and uploads for media
os.makedirs("fixtures", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
app.mount("/fixtures", StaticFiles(directory="fixtures"), name="fixtures")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Mount frontend dist if built
dist_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")
