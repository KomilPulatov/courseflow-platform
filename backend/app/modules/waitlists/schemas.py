from pydantic import BaseModel, Field


class WaitlistCreate(BaseModel):
    section_id: int = Field(gt=0)


class WaitlistItem(BaseModel):
    waitlist_entry_id: int
    section_id: int
    position: int
    status: str


class WaitlistDeleteResponse(BaseModel):
    status: str
    waitlist_entry_id: int
