from fastapi import APIRouter

router = APIRouter()


@router.post("/enroll")
def enroll_student():
    return {
        "message": "Enrollment endpoint placeholder",
        "status": "pending_implementation",
    }
