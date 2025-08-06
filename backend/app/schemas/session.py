from pydantic import BaseModel, Field

class SessionInitiateRequest(BaseModel):
    participant_id: str = Field(..., description="System-generated unique ID (UUID) for the participant")
    group: str = Field("experimental", description="Assigned experiment group")

class SessionInitiateResponse(BaseModel):
    participant_id: str = Field(..., description="System-generated unique ID (UUID) for the participant")
    is_new_user: bool