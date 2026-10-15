from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.database import Base


class CloudResource(Base):
    __tablename__ = "cloud_resources"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    resource_name = Column(String(120), nullable=False, index=True)
    provider = Column(String(32), nullable=False, index=True)  # AWS, GCP, Azure
    service_type = Column(String(64), nullable=False)  # EKS, EC2, RDS, S3, NAT-Gateway
    region = Column(String(64), nullable=False, default="ap-south-1")
    environment = Column(String(32), nullable=False)  # production, staging, dev
    monthly_cost = Column(Float, nullable=False)
    status = Column(String(32), nullable=False, default="Optimal", index=True)  # Optimal, Idle, Over-provisioned, Terminated
    owner_team = Column(String(64), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )