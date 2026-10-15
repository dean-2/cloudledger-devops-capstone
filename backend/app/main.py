from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine, SessionLocal, get_db, Base
from app.models import CloudResource
from app.routes import router as resources_router

INITIAL_SEED_DATA = [
    {
        "resource_name": "prod-eks-worker-pool-ap-south-1",
        "provider": "AWS",
        "service_type": "EKS",
        "region": "ap-south-1",
        "environment": "production",
        "monthly_cost": 1480.00,
        "status": "Optimal",
        "owner_team": "Platform-SRE",
    },
    {
        "resource_name": "billing-rds-postgres-multi-az",
        "provider": "AWS",
        "service_type": "RDS",
        "region": "ap-south-1",
        "environment": "production",
        "monthly_cost": 920.50,
        "status": "Over-provisioned",
        "owner_team": "Payments-Core",
    },
    {
        "resource_name": "staging-nat-gateway-mumbai-a",
        "provider": "AWS",
        "service_type": "NAT-Gateway",
        "region": "ap-south-1",
        "environment": "staging",
        "monthly_cost": 340.00,
        "status": "Idle",
        "owner_team": "DevEx-Infra",
    },
    {
        "resource_name": "analytics-gke-gpu-inference",
        "provider": "GCP",
        "service_type": "GKE",
        "region": "asia-south1",
        "environment": "staging",
        "monthly_cost": 1150.75,
        "status": "Idle",
        "owner_team": "ML-Data-Platform",
    },
    {
        "resource_name": "compliance-audit-archive-s3",
        "provider": "AWS",
        "service_type": "S3",
        "region": "ap-south-1",
        "environment": "production",
        "monthly_cost": 185.25,
        "status": "Optimal",
        "owner_team": "SecOps-Governance",
    },
]


def seed_initial_resources():
    """Ensure tables exist and populate 5 initial FinOps records if empty."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing_count = db.query(CloudResource).count()
        if existing_count == 0:
            for item in INITIAL_SEED_DATA:
                db.add(CloudResource(**item))
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_initial_resources()
    yield


app = FastAPI(
    title="CloudLedger FinOps API",
    description="Cloud Infrastructure Cost-Auditing & FinOps Governance Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=True)

app.include_router(resources_router)


@app.get("/", tags=["System"])
def root_metadata():
    """Return service metadata and operational status."""
    return {
        "service": "CloudLedger FinOps API",
        "version": "1.0.0",
        "domain": "FinOps & Cloud Infrastructure Cost-Auditing",
        "default_region": "ap-south-1",
        "status": "operational",
    }


@app.get("/health", tags=["System"])
def health_check():
    """Kubernetes liveness probe endpoint."""
    return {"status": "healthy", "service": "cloudledger-backend"}


@app.get("/ready", tags=["System"])
def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe verifying active PostgreSQL connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "READY", "database": "connected"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not ready: {str(exc)}",
        )