"""
sync API endpoints

post /v1/sync  — run the ins scrape job synchronously
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.sync.schemas import SyncJobResponse, SyncRequest
from app.modules.sync.simple_scraper import run_sync_simple

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=SyncJobResponse, status_code=status.HTTP_200_OK)
def run_sync(
    body: SyncRequest,
    db: DbSession,
) -> SyncJobResponse:
    try:
        run_sync_simple(db, body.user_id, body.username, body.password)
        return SyncJobResponse(job_id="simple-sync", status="done")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Sync is failed: {str(e)}"
        ) from e
