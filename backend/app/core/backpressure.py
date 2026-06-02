import logging
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import Request

logger = logging.getLogger(__name__)

_ingest_lock = threading.Lock()
_active_ingestions = 0

_session_rate_lock = threading.Lock()
_session_attempts_by_ip: dict[str, deque[datetime]] = defaultdict(deque)


def try_acquire_ingest_slot(max_concurrent_ingestions: int) -> bool:
    global _active_ingestions
    with _ingest_lock:
        if _active_ingestions >= max_concurrent_ingestions:
            logger.warning(
                "Ingest backpressure active active_ingestions=%s max_concurrent_ingestions=%s",
                _active_ingestions,
                max_concurrent_ingestions,
            )
            return False
        _active_ingestions += 1
        logger.info(
            "Acquired ingest slot active_ingestions=%s max_concurrent_ingestions=%s",
            _active_ingestions,
            max_concurrent_ingestions,
        )
        return True


def release_ingest_slot() -> None:
    global _active_ingestions
    with _ingest_lock:
        if _active_ingestions <= 0:
            logger.warning("Tried to release ingest slot but no active ingestion was recorded")
            return
        _active_ingestions -= 1
        logger.info("Released ingest slot active_ingestions=%s", _active_ingestions)


def active_ingestions() -> int:
    with _ingest_lock:
        return _active_ingestions


def client_ip_from_request(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def check_session_rate_limit(
    client_ip: str,
    max_sessions_per_hour: int,
    now: datetime | None = None,
) -> tuple[bool, int, int]:
    current_time = now or datetime.now(timezone.utc)
    cutoff = current_time - timedelta(hours=1)

    with _session_rate_lock:
        attempts = _session_attempts_by_ip[client_ip]
        while attempts and attempts[0] <= cutoff:
            attempts.popleft()

        if len(attempts) >= max_sessions_per_hour:
            retry_at = attempts[0] + timedelta(hours=1)
            retry_after_seconds = max(1, int((retry_at - current_time).total_seconds()))
            logger.warning(
                "Session rate limit active client_ip=%s attempts=%s max_sessions_per_hour=%s retry_after_seconds=%s",
                client_ip,
                len(attempts),
                max_sessions_per_hour,
                retry_after_seconds,
            )
            return False, retry_after_seconds, len(attempts)

        attempts.append(current_time)
        logger.info(
            "Recorded session attempt client_ip=%s attempts_in_last_hour=%s max_sessions_per_hour=%s",
            client_ip,
            len(attempts),
            max_sessions_per_hour,
        )
        return True, 0, len(attempts)


def reset_backpressure_state() -> None:
    global _active_ingestions
    with _ingest_lock:
        _active_ingestions = 0
    with _session_rate_lock:
        _session_attempts_by_ip.clear()
