from http import HTTPStatus


class ProfessorError(Exception):
    code = "professor_error"
    message = "Professor operation failed."
    status_code = HTTPStatus.BAD_REQUEST

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class RoomNotInPoolError(ProfessorError):
    code = "room_not_in_pool"
    message = "The selected room is not in the allocated pool for this section."


class RoomCapacityError(ProfessorError):
    code = "room_capacity_too_small"
    message = "Room capacity is smaller than section capacity."


class RoomConflictError(ProfessorError):
    code = "room_conflict"
    message = "Room is already occupied at this section's scheduled time."


class SectionNotAssignedError(ProfessorError):
    code = "section_not_assigned"
    message = "This section is not assigned to you."
