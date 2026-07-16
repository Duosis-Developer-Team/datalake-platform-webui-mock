from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query, Request

from app.core.time_filter import TimeFilter
from app.models.schemas import CustomerResources
from app.services.customer_service import CustomerService

router = APIRouter()


def get_db(request: Request) -> CustomerService:
    return request.app.state.db


@router.get("/customers", response_model=List[str])
def list_customers(db: CustomerService = Depends(get_db)):
    return db.get_customer_list()


@router.get("/customers/{customer_name}/resources", response_model=CustomerResources)
def customer_resources(
    customer_name: str,
    tf: TimeFilter = Depends(),
    db: CustomerService = Depends(get_db),
):
    return db.get_customer_resources(customer_name, tf.to_dict())


@router.get("/customers/{customer_name}/s3/vaults", response_model=dict[str, Any])
def customer_s3_vaults(
    customer_name: str,
    tf: TimeFilter = Depends(),
    db: CustomerService = Depends(get_db),
):
    return db.get_customer_s3_vaults(customer_name, tf.to_dict())


@router.get("/customers/{customer_name}/backup/{vendor}/unique-jobs", response_model=dict[str, Any])
def customer_unique_jobs(
    customer_name: str,
    vendor: str,
    tf: TimeFilter = Depends(),
):
    from src.services.mock_data import backup as mock_backup

    return mock_backup.get_customer_unique_jobs(customer_name, vendor, tf.to_dict())


@router.get("/customers/{customer_name}/backup/{vendor}/unique-jobs/table", response_model=dict[str, Any])
def customer_unique_jobs_table(
    customer_name: str,
    vendor: str,
    tf: TimeFilter = Depends(),
    page: int = Query(1),
    page_size: int = Query(50),
    search: str = Query(""),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    policy_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
):
    from src.services.mock_data import backup as mock_backup

    def _split(v: Optional[str]) -> list[str] | None:
        if not v:
            return None
        return [x.strip() for x in v.split(",") if x.strip()]

    return mock_backup.get_customer_unique_jobs_table(
        customer_name,
        vendor,
        tf.to_dict(),
        page=page,
        page_size=page_size,
        search=search,
        statuses=_split(status),
        types=_split(type),
        policy_types=_split(policy_type),
        categories=_split(category),
        platforms=_split(platform),
    )
