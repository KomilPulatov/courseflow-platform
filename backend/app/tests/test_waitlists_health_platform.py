from app.db.models import Notification
from app.modules.platform.rate_limiter import TokenBucket
from app.tests.factories import seed_registration_case


def test_waitlist_endpoints_and_dependency_health(client, db_session) -> None:
    seed = seed_registration_case(db_session)

    health = client.get("/api/v1/health/dependencies")
    assert health.status_code == 200
    assert health.json()["checks"]["postgres"] == "ok"

    created = client.post(
        "/api/v1/waitlists",
        headers={"X-Student-Id": str(seed["student_id"])},
        json={"section_id": seed["section_id"]},
    )
    assert created.status_code == 201
    waitlist_id = created.json()["waitlist_entry_id"]

    listed = client.get("/api/v1/waitlists/me", headers={"X-Student-Id": str(seed["student_id"])})
    assert listed.status_code == 200
    assert listed.json()[0]["waitlist_entry_id"] == waitlist_id

    cancelled = client.delete(
        f"/api/v1/waitlists/{waitlist_id}",
        headers={"X-Student-Id": str(seed["student_id"])},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


def test_token_bucket_refills_and_rejects() -> None:
    bucket = TokenBucket(capacity=2, refill_rate_per_second=1, tokens=2, last_refill_at=0)

    assert bucket.allow(now=0)
    assert bucket.allow(now=0)
    assert not bucket.allow(now=0)
    assert bucket.allow(now=1)


def test_student_notifications_endpoint(client, db_session) -> None:
    seed = seed_registration_case(db_session)
    db_session.add(
        Notification(
            student_id=seed["student_id"],
            event_type="WaitlistPromoted",
            message="You were promoted.",
            payload={"section_id": seed["section_id"]},
            status="unread",
        )
    )
    db_session.commit()

    response = client.get(
        "/api/v1/notifications/me",
        headers={"X-Student-Id": str(seed["student_id"])},
    )

    assert response.status_code == 200
    assert response.json()[0]["event_type"] == "WaitlistPromoted"
