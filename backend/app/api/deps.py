from typing import Annotated

from fastapi import Header


def get_current_student_id(
    x_student_id: Annotated[int, Header(alias="X-Student-Id", gt=0)],
) -> int:
    return x_student_id
