import json

from fastapi import HTTPException, status
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.metrics import record_redis_operation
from app.modules.courses.repository import CourseCatalogRepository
from app.modules.courses.schemas import SectionAvailability
from app.modules.platform.redis_client import get_redis_client


def section_availability_cache_key(section_id: int) -> str:
    return f"section:{section_id}:availability"


def section_availability_channel(section_id: int) -> str:
    return f"section:{section_id}:availability"


def get_cached_or_calculated_availability(db: Session, section_id: int) -> SectionAvailability:
    """Read availability from Redis first, then fall back to the database."""

    client = get_redis_client()
    cache_key = section_availability_cache_key(section_id)
    if client is not None:
        try:
            cached = client.get(cache_key)
            if cached:
                record_redis_operation("availability_cache", "hit")
                return SectionAvailability.model_validate_json(cached)
            record_redis_operation("availability_cache", "miss")
        except RedisError:
            record_redis_operation("availability_cache", "error")

    availability = calculate_section_availability(db, section_id)
    cache_section_availability(availability)
    return availability


def calculate_section_availability(db: Session, section_id: int) -> SectionAvailability:
    repo = CourseCatalogRepository(db)
    section = repo.get_section(section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found.")

    enrolled_count = repo.count_active_enrollments(section.id)
    waitlist_count = repo.count_waitlist_entries(section.id)
    return SectionAvailability(
        section_id=section.id,
        capacity=section.capacity,
        enrolled_count=enrolled_count,
        remaining_seats=max(section.capacity - enrolled_count, 0),
        waitlist_count=waitlist_count,
        status=section.status,
    )


def cache_section_availability(availability: SectionAvailability) -> None:
    client = get_redis_client()
    if client is None:
        return

    try:
        client.setex(
            section_availability_cache_key(availability.section_id),
            settings.REDIS_CACHE_TTL_SECONDS,
            availability.model_dump_json(),
        )
        record_redis_operation("availability_cache", "set")
    except RedisError:
        record_redis_operation("availability_cache", "error")


def publish_section_availability(availability: SectionAvailability) -> None:
    client = get_redis_client()
    if client is None:
        return

    try:
        message = availability.model_dump()
        message["type"] = "section_availability_changed"
        client.publish(section_availability_channel(availability.section_id), json.dumps(message))
        record_redis_operation("availability_pubsub", "published")
    except RedisError:
        record_redis_operation("availability_pubsub", "error")
