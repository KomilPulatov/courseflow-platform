from typing import Protocol


class AvailabilityPublisher(Protocol):
    def publish_section_changed(self, section_id: int) -> None: ...


class RegistrationEventPublisher(Protocol):
    def publish_registration_event(self, event_type: str, payload: dict) -> None: ...


class NoopAvailabilityPublisher:
    def publish_section_changed(self, section_id: int) -> None:
        return None


class NoopRegistrationEventPublisher:
    def publish_registration_event(self, event_type: str, payload: dict) -> None:
        return None
