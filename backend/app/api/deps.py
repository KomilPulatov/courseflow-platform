from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.models import Student
from app.db.session import get_db

DbSession = Annotated[Session, Depends(get_db)]

optional_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_student_id(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(optional_bearer_scheme),
    ] = None,
    x_student_id: Annotated[int | None, Header(alias="X-Student-Id", gt=0)] = None,
    db: DbSession = None,
) -> int:
    if db is None:  # pragma: no cover - FastAPI injects this in normal use
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if credentials is not None:
        try:
            payload = decode_access_token(credentials.credentials)
            if payload.get("role") != "student":
                raise ValueError("not a student token")
            user_id = int(payload["sub"])
        except (InvalidTokenError, KeyError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid student token",
            ) from exc
        student = db.query(Student).filter(Student.user_id == user_id).first()
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found",
            )
        return student.id

    if x_student_id is not None:
        return x_student_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Student authentication required",
    )
