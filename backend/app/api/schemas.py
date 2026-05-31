from typing import Literal

from pydantic import BaseModel, Field, model_validator


class VideoInput(BaseModel):
    platform: Literal["youtube", "instagram"]
    url: str = Field(min_length=8)
    video_id: Literal["A", "B"] | None = None


class IngestRequest(BaseModel):
    videos: list[VideoInput] | None = None
    youtube_url: str | None = None
    instagram_url: str | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> "IngestRequest":
        if self.videos is not None and len(self.videos) != 2:
            raise ValueError("Exactly two videos are required")
        videos = self.normalized_videos()
        if len(videos) != 2:
            raise ValueError("Exactly two videos are required")
        if {video.video_id for video in videos} != {"A", "B"}:
            raise ValueError("Videos must resolve to one Video A and one Video B")
        return self

    def normalized_videos(self) -> list[VideoInput]:
        if self.videos:
            ordered = self.videos[:2]
            return [
                VideoInput(
                    platform=video.platform,
                    url=video.url,
                    video_id=video.video_id or ("A" if index == 0 else "B"),
                )
                for index, video in enumerate(ordered)
            ]

        if self.youtube_url and self.instagram_url:
            return [
                VideoInput(platform="youtube", url=self.youtube_url, video_id="A"),
                VideoInput(platform="instagram", url=self.instagram_url, video_id="B"),
            ]

        return []


class IngestResponse(BaseModel):
    session_id: str
    status: str


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=8)
    message: str = Field(min_length=1)
