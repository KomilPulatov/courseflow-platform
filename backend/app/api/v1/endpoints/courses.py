from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_courses():
    return [
        {
            "id": 1,
            "code": "CSE3010",
            "title": "Database Application and Design",
            "credits": 3,
        }
    ]
