from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.models import Student, User
from app.db.session import get_db

optional_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_student_id(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(optional_bearer_scheme),
    ] = None,
    x_student_id: Annotated[int | None, Header(alias="X-Student-Id", gt=0)] = None,
) -> int:
    # Production-style requests should use JWT. The header fallback keeps Swagger demos
    # and simple tests easy while the frontend/auth integration is still growing.
    if credentials is not None:
        return _student_id_from_token(db, credentials.credentials)

    if x_student_id is not None:
        return x_student_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Provide a student bearer token or X-Student-Id header.",
    )


def _student_id_from_token(db: Session, token: str) -> int:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from exc

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    if user.role != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students only.")

    # The registration service works with student profile IDs, not user IDs.
    student = db.query(Student).filter(Student.user_id == user.id).first()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found.",
        )
    return student.id
