from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    youtube_url: str = Field(min_length=8)
    instagram_url: str = Field(min_length=8)


class IngestResponse(BaseModel):
    session_id: str
    status: str


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=8)
    message: str = Field(min_length=1)
