REQUIRED_GOOGLE_OAUTH_SCOPES: tuple[str, ...] = (
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
)


FORBIDDEN_GOOGLE_OAUTH_SCOPE_FRAGMENTS: tuple[str, ...] = (
    "yt-analytics-monetary",
    "youtube.force-ssl",
    "youtube.upload",
    "youtubepartner",
)


def normalize_scope_string(value: str | None) -> list[str]:
    if not value:
        return []
    return sorted({scope.strip() for scope in value.replace(",", " ").split() if scope.strip()})


def missing_required_scopes(granted_scopes: list[str]) -> list[str]:
    granted = set(granted_scopes)
    return [scope for scope in REQUIRED_GOOGLE_OAUTH_SCOPES if scope not in granted]
