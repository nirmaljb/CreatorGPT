import logging
import re
from typing import Any

from yt_dlp.cookies import SUPPORTED_BROWSERS, SUPPORTED_KEYRINGS

from backend.app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

_BROWSER_SPEC_RE = re.compile(
    r"""
    (?P<name>[^+:]+)
    (?:\s*\+\s*(?P<keyring>[^:]+))?
    (?:\s*:\s*(?!:)(?P<profile>.+?))?
    (?:\s*::\s*(?P<container>.+))?
    """,
    re.VERBOSE,
)


def parse_cookies_from_browser(value: str) -> tuple[str, str | None, str | None, str | None]:
    spec = value.strip()
    match = _BROWSER_SPEC_RE.fullmatch(spec)
    if match is None:
        raise ValueError("Invalid YTDLP_COOKIES_FROM_BROWSER value. Expected BROWSER[+KEYRING][:PROFILE][::CONTAINER].")

    browser_name, keyring, profile, container = match.group("name", "keyring", "profile", "container")
    browser_name = browser_name.lower().strip()
    keyring = keyring.upper().strip() if keyring else None

    if browser_name not in SUPPORTED_BROWSERS:
        raise ValueError(
            f'Unsupported YTDLP_COOKIES_FROM_BROWSER browser "{browser_name}". '
            f"Supported browsers are: {', '.join(sorted(SUPPORTED_BROWSERS))}."
        )
    if keyring is not None and keyring not in SUPPORTED_KEYRINGS:
        raise ValueError(
            f'Unsupported YTDLP_COOKIES_FROM_BROWSER keyring "{keyring}". '
            f"Supported keyrings are: {', '.join(sorted(SUPPORTED_KEYRINGS))}."
        )

    return (
        browser_name,
        profile.strip() if profile else None,
        keyring,
        container.strip() if container else None,
    )


def yt_dlp_options(base_options: dict[str, Any], settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    options = dict(base_options)
    cookies_path = settings.ytdlp_cookies_path.strip()
    cookies_from_browser = settings.ytdlp_cookies_from_browser.strip()

    if cookies_path:
        options["cookiefile"] = cookies_path
        logger.info("yt-dlp cookie file authentication is enabled")
        return options

    if cookies_from_browser:
        options["cookiesfrombrowser"] = parse_cookies_from_browser(cookies_from_browser)
        logger.info("yt-dlp browser cookie authentication is enabled")

    return options
