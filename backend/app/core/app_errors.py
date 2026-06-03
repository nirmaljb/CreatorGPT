from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AppError:
    code: str
    message: str
    scope: str
    retryable: bool
    video_id: str | None = None
    field: str | None = None
    retry_after_seconds: int | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "scope": self.scope,
            "retryable": self.retryable,
        }
        if self.video_id:
            data["video_id"] = self.video_id
        if self.field:
            data["field"] = self.field
        if self.retry_after_seconds is not None:
            data["retry_after_seconds"] = self.retry_after_seconds
        return data


class AppErrorHTTPException(Exception):
    def __init__(self, status_code: int, error: AppError, headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self.error = error
        self.headers = headers or {}
        super().__init__(error.message)


class PipelineAppException(RuntimeError):
    def __init__(self, error: AppError, raw_error: BaseException | None = None) -> None:
        self.error = error
        self.raw_error = raw_error
        super().__init__(error.message)


def error_response_payload(error: AppError) -> dict[str, Any]:
    return {"error": error.to_dict(), "detail": error.message}


def validation_error(
    message: str,
    video_id: str | None = None,
    field: str | None = None,
    code: str = "VALIDATION_INVALID_URL",
) -> AppError:
    return AppError(code=code, message=message, scope="field", retryable=False, video_id=video_id, field=field)


def busy_error(max_concurrent_ingestions: int) -> AppError:
    return AppError(
        code="INGEST_BUSY",
        message=(
            "Too many ingestions are already running. "
            f"Limit: {max_concurrent_ingestions} concurrent ingestion(s). Try again shortly."
        ),
        scope="request",
        retryable=True,
    )


def rate_limit_error(max_sessions_per_hour: int, retry_after_seconds: int) -> AppError:
    return AppError(
        code="INGEST_RATE_LIMITED",
        message=(f"Session rate limit reached for this IP. Limit: {max_sessions_per_hour} session(s) per hour."),
        scope="request",
        retryable=True,
        retry_after_seconds=retry_after_seconds,
    )


def session_not_found_error() -> AppError:
    return AppError(
        code="SESSION_NOT_FOUND",
        message="Session not found.",
        scope="session",
        retryable=False,
    )


def session_not_ready_error(status: str) -> AppError:
    return AppError(
        code="SESSION_NOT_READY",
        message=f"Session is {status}, not completed.",
        scope="session",
        retryable=True,
    )


def stale_ingest_error() -> AppError:
    return AppError(
        code="INGEST_STALLED",
        message=(
            "Ingestion stalled because the background worker stopped before completion. Start a new ingest session."
        ),
        scope="session",
        retryable=True,
    )


def stale_video_ingest_error(video_id: str) -> AppError:
    return AppError(
        code="INGEST_STALLED",
        message=(
            "Ingestion stalled because the background worker stopped before this video finished. "
            "Start a new ingest session."
        ),
        scope="video",
        retryable=True,
        video_id=video_id,
    )


def _lower_error_text(exc: BaseException) -> str:
    return str(exc or "").lower()


def _youtube_access_error(video_id: str | None = None) -> AppError:
    return AppError(
        code="INGEST_YOUTUBE_ACCESS",
        message=(
            "YouTube video could not be accessed. It may be unavailable, private, restricted, "
            "or require yt-dlp cookies. Configure YTDLP_COOKIES_PATH with an exported Netscape "
            "cookies file and start a new ingest session."
        ),
        scope="video",
        retryable=True,
        video_id=video_id,
    )


def classify_ingest_error(
    exc: BaseException,
    stage: str,
    platform: str | None = None,
    video_id: str | None = None,
) -> AppError:
    normalized_platform = (platform or "").lower().strip()
    normalized_stage = stage.lower().strip()
    text = _lower_error_text(exc)

    if normalized_stage == "metadata":
        if normalized_platform == "instagram":
            return AppError(
                code="INGEST_INSTAGRAM_ACCESS",
                message=("Instagram Reel could not be accessed. It may be private, unavailable, or require cookies."),
                scope="video",
                retryable=True,
                video_id=video_id,
            )
        if normalized_platform == "youtube":
            return _youtube_access_error(video_id)

    if normalized_platform == "youtube" and any(
        marker in text for marker in ("cookies", "login", "sign in", "confirm you're not a bot", "captcha")
    ):
        return _youtube_access_error(video_id)

    if normalized_platform == "instagram" and any(
        marker in text for marker in ("private", "unavailable", "cookies", "login", "sign in")
    ):
        return AppError(
            code="INGEST_INSTAGRAM_ACCESS",
            message=("Instagram Reel could not be accessed. It may be private, unavailable, or require cookies."),
            scope="video",
            retryable=True,
            video_id=video_id,
        )

    if normalized_stage in {"transcript", "download", "transcription"}:
        return AppError(
            code="INGEST_TRANSCRIPT_FAILED",
            message="Transcript could not be generated for this video. Check the URL or retry the ingest.",
            scope="video",
            retryable=True,
            video_id=video_id,
        )

    if normalized_stage in {"vector", "embedding"}:
        return AppError(
            code="INGEST_VECTOR_STORE_FAILED",
            message="Transcript chunks could not be stored for search. Retry after the vector store is reachable.",
            scope="video",
            retryable=True,
            video_id=video_id,
        )

    return AppError(
        code="INGEST_FAILED",
        message="Ingestion failed before both videos were ready. Retry with the same URLs or edit the inputs.",
        scope="video" if video_id else "session",
        retryable=True,
        video_id=video_id,
    )


def session_error_from_video_error(error: AppError) -> AppError:
    video_label = f"Video {error.video_id}" if error.video_id else "a video"
    return AppError(
        code=error.code,
        message=f"Ingestion cannot continue because {video_label} failed. {error.message}",
        scope="session",
        retryable=error.retryable,
        video_id=error.video_id,
        retry_after_seconds=error.retry_after_seconds,
    )


def classify_session_ingest_error(exc: BaseException) -> AppError:
    if isinstance(exc, PipelineAppException):
        return session_error_from_video_error(exc.error)
    return AppError(
        code="INGEST_FAILED",
        message="Ingestion failed before both videos were ready. Retry with the same URLs or edit the inputs.",
        scope="session",
        retryable=True,
    )


def classify_chat_error(exc: BaseException, stage: str) -> AppError:
    normalized_stage = stage.lower().strip()
    if normalized_stage == "retrieval":
        return AppError(
            code="CHAT_RETRIEVAL_FAILED",
            message="Transcript evidence could not be retrieved for this question. Try again shortly.",
            scope="chat",
            retryable=True,
        )
    if normalized_stage == "provider":
        return AppError(
            code="CHAT_PROVIDER_FAILED",
            message="The chat model could not finish the answer. Try again shortly.",
            scope="chat",
            retryable=True,
        )
    if normalized_stage == "persistence":
        return AppError(
            code="CHAT_PERSISTENCE_FAILED",
            message="The answer streamed, but chat history could not be saved. Refresh and try again if needed.",
            scope="chat",
            retryable=True,
        )
    return AppError(
        code="CHAT_FAILED",
        message="Chat failed before an answer could be completed. Try again shortly.",
        scope="chat",
        retryable=True,
    )
