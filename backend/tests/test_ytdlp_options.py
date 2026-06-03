import pytest

from backend.app.core.config import Settings
from backend.app.ingest.yt_dlp_options import parse_cookies_from_browser, yt_dlp_options


def test_yt_dlp_options_adds_cookie_file() -> None:
    settings = Settings(YTDLP_COOKIES_PATH="/private/tmp/youtube-cookies.txt", YTDLP_COOKIES_FROM_BROWSER="")

    options = yt_dlp_options({"quiet": True}, settings)

    assert options["quiet"] is True
    assert options["cookiefile"] == "/private/tmp/youtube-cookies.txt"
    assert "cookiesfrombrowser" not in options


def test_yt_dlp_options_prefers_cookie_file_over_browser_source() -> None:
    settings = Settings(YTDLP_COOKIES_PATH="/private/tmp/youtube-cookies.txt", YTDLP_COOKIES_FROM_BROWSER="chrome")

    options = yt_dlp_options({}, settings)

    assert options == {"cookiefile": "/private/tmp/youtube-cookies.txt"}


def test_yt_dlp_options_adds_browser_cookie_source() -> None:
    settings = Settings(YTDLP_COOKIES_PATH="", YTDLP_COOKIES_FROM_BROWSER="chrome:Profile 1")

    options = yt_dlp_options({}, settings)

    assert options["cookiesfrombrowser"] == ("chrome", "Profile 1", None, None)


def test_parse_cookies_from_browser_supports_keyring_profile_and_container() -> None:
    assert parse_cookies_from_browser("firefox+kwallet:default::Work") == ("firefox", "default", "KWALLET", "Work")


def test_parse_cookies_from_browser_rejects_invalid_spec() -> None:
    with pytest.raises(ValueError, match="Unsupported YTDLP_COOKIES_FROM_BROWSER browser"):
        parse_cookies_from_browser("notabrowser")
