from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CloudResource
from app.schemas import (
    CloudResourceCreate,
    CloudResourceUpdate,
    CloudResourceResponse,
    FinOpsStatsResponse,
)

router = APIRouter(prefix="/api/resources", tags=["Cloud Resources"])


@router.get("/stats", response_model=FinOpsStatsResponse)
def get_resource_stats(db: Session = Depends(get_db)):
    """Aggregate FinOps KPI metrics across all active cloud resources."""
    resources = db.query(CloudResource).filter(CloudResource.status != "Terminated").all()
    total_count = len(resources)

    if total_count == 0:
        return FinOpsStatsResponse(
            total_monthly_spend=0.0,
            potential_savings=0.0,
            idle_count=0,
            over_provisioned_count=0,
            optimal_count=0,
            total_count=0,
            optimization_health_pct=100.0,
        )

    total_monthly_spend = round(sum(r.monthly_cost for r in resources), 2)
    potential_savings = round(
        sum(r.monthly_cost for r in resources if r.status in ("Idle", "Over-provisioned")),
        2,
    )
    idle_count = sum(1 for r in resources if r.status == "Idle")
    over_provisioned_count = sum(1 for r in resources if r.status == "Over-provisioned")
    optimal_count = sum(1 for r in resources if r.status == "Optimal")
    optimization_health_pct = round((optimal_count / total_count) * 100.0, 1)

    return FinOpsStatsResponse(
        total_monthly_spend=total_monthly_spend,
        potential_savings=potential_savings,
        idle_count=idle_count,
        over_provisioned_count=over_provisioned_count,
        optimal_count=optimal_count,
        total_count=total_count,
        optimization_health_pct=optimization_health_pct,
    )


@router.get("", response_model=List[CloudResourceResponse])
def list_resources(
    status_filter: Optional[str] = Query(None, alias="status"),
    provider: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List cloud infrastructure resources with optional filtering."""
    query = db.query(CloudResource)
    if status_filter:
        query = query.filter(CloudResource.status == status_filter)
    if provider:
        query = query.filter(CloudResource.provider == provider)
    if environment:
        query = query.filter(CloudResource.environment == environment)
    return query.order_by(CloudResource.id.desc()).all()


@router.get("/{resource_id}", response_model=CloudResourceResponse)
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    """Retrieve a single cloud resource by ID."""
    resource = db.query(CloudResource).filter(CloudResource.id == resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cloud resource with id {resource_id} not found",
        )
    return resource


@router.post("", response_model=CloudResourceResponse, status_code=status.HTTP_201_CREATED)
def create_resource(payload: CloudResourceCreate, db: Session = Depends(get_db)):
    """Create and audit a new cloud infrastructure resource."""
    new_resource = CloudResource(**payload.model_dump())
    db.add(new_resource)
    db.commit()
    db.refresh(new_resource)
    return new_resource


@router.put("/{resource_id}", response_model=CloudResourceResponse)
def update_resource(
    resource_id: int,
    payload: CloudResourceUpdate,
    db: Session = Depends(get_db),
):
    """Update status, cost, owner, or metadata for an existing cloud resource."""
    resource = db.query(CloudResource).filter(CloudResource.id == resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cloud resource with id {resource_id} not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(resource, field, value)

    db.commit()
    db.refresh(resource)
    return resource


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    """Remove a cloud resource record from the audit ledger."""
    resource = db.query(CloudResource).filter(CloudResource.id == resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cloud resource with id {resource_id} not found",
        )
    db.delete(resource)
    db.commit()
    return None