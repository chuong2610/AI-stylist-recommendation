import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    user_id: str
    title: str | None = None


class SessionResponse(BaseModel):
    id: uuid.UUID
    user_id: str
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class MessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    intent: str | None
    # Reads the ORM attribute metadata_ (SQLAlchemy reserves .metadata) but
    # serializes as plain "metadata" in API responses.
    metadata: dict[str, Any] | None = Field(
        None, validation_alias="metadata_", serialization_alias="metadata"
    )
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class ChatResponse(BaseModel):
    message: MessageResponse
    # Present only when intent == outfit_recommendation
    outfit_plan: dict[str, Any] | None = None
