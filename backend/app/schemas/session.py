from pydantic import BaseModel, Field

class SessionInitiateRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="User-provided name")
    group: str = Field("experimental", description="Assigned experiment group")

class SessionInitiateResponse(BaseModel):
    participant_id: str = Field(..., description="System-generated unique ID (UUID) for the participant")
    username: str
    is_new_user: bool