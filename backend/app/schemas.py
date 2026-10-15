from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CloudResourceBase(BaseModel):
    resource_name: str = Field(..., min_length=2, max_length=120, examples=["prod-eks-node-group"])
    provider: str = Field(..., examples=["AWS", "GCP", "Azure"])
    service_type: str = Field(..., examples=["EKS", "EC2", "RDS", "S3", "NAT-Gateway"])
    region: str = Field(default="ap-south-1", examples=["ap-south-1"])
    environment: str = Field(..., examples=["production", "staging", "dev"])
    monthly_cost: float = Field(..., ge=0.0, examples=[1420.50])
    status: str = Field(default="Optimal", examples=["Optimal", "Idle", "Over-provisioned", "Terminated"])
    owner_team: str = Field(..., min_length=2, max_length=64, examples=["Platform-SRE"])


class CloudResourceCreate(CloudResourceBase):
    pass


class CloudResourceUpdate(BaseModel):
    resource_name: Optional[str] = Field(None, min_length=2, max_length=120)
    provider: Optional[str] = None
    service_type: Optional[str] = None
    region: Optional[str] = None
    environment: Optional[str] = None
    monthly_cost: Optional[float] = Field(None, ge=0.0)
    status: Optional[str] = None
    owner_team: Optional[str] = Field(None, min_length=2, max_length=64)


class CloudResourceResponse(CloudResourceBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FinOpsStatsResponse(BaseModel):
    total_monthly_spend: float
    potential_savings: float
    idle_count: int
    over_provisioned_count: int
    optimal_count: int
    total_count: int
    optimization_health_pct: float