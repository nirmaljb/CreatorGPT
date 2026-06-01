from backend.app.ingest.chunker import format_timestamp


def _format_value(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(_format_value(item) for item in value) if value else "none"
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            if key == "source_tag":
                parts.append(_format_value(item))
            else:
                parts.append(f"{key}: {_format_value(item)}")
        return "; ".join(parts)
    return str(value)


def metadata_source_tag(video_id: str) -> str:
    return f"[Video {video_id} metadata]"


def _available_value(item: dict, value_key: str, available_key: str) -> object:
    if item.get(available_key, True):
        return item[value_key]
    return "unavailable"


def build_sources(metadata: list[dict], chunks: list[dict]) -> list[dict]:
    sources: list[dict] = []
    for item in metadata:
        sources.append(
            {
                "type": "metadata",
                "video_id": item["video_id"],
                "source_tag": metadata_source_tag(item["video_id"]),
            }
        )
    for chunk in chunks:
        sources.append(
            {
                "type": "chunk",
                "video_id": chunk["video_id"],
                "chunk_index": chunk["chunk_index"],
                "start_time": chunk["start_time"],
                "end_time": chunk["end_time"],
                "source_tag": chunk["source_tag"],
            }
        )
    return sources


def _metadata_block(metadata: list[dict]) -> str:
    lines = []
    for item in metadata:
        followers = _available_value(item, "creator_followers", "creator_followers_available")
        views = _available_value(item, "views", "views_available")
        likes = _available_value(item, "likes", "likes_available")
        comments = _available_value(item, "comments", "comments_available")
        engagement_rate = _available_value(item, "engagement_rate", "engagement_rate_available")
        lines.append(
            "\n".join(
                [
                    f"{metadata_source_tag(item['video_id'])}",
                    f"platform: {item['platform']}",
                    f"creator: {item['creator']}",
                    f"creator_followers: {followers}",
                    f"views: {views}",
                    f"likes: {likes}",
                    f"comments: {comments}",
                    f"engagement_rate_percent: {engagement_rate}",
                    f"duration_seconds: {item['duration_seconds']}",
                    f"upload_date: {item['upload_date'] or 'unknown'}",
                    f"hashtags: {', '.join(item['hashtags']) if item['hashtags'] else 'none'}",
                ]
            )
        )
    return "\n\n".join(lines) if lines else "No metadata available."


def _metadata_tools_block(metadata_tool_results: list[dict]) -> str:
    if not metadata_tool_results:
        return "No metadata tool results available."
    lines = []
    for item in metadata_tool_results:
        lines.append(f"tool: {item['tool']}\nresult: {_format_value(item['result'])}")
    return "\n\n".join(lines)


def _chunks_block(chunks: list[dict]) -> str:
    if not chunks:
        return "No transcript chunks were retrieved."
    lines = []
    for chunk in chunks:
        timestamp = f"{format_timestamp(chunk['start_time'])}-{format_timestamp(chunk['end_time'])}"
        lines.append(
            "\n".join(
                [
                    f"{chunk['source_tag']}",
                    f"video_id: {chunk['video_id']}",
                    f"timestamp: {timestamp}",
                    f"is_hook: {chunk['is_hook']}",
                    f"transcript_source: {chunk.get('transcript_source', 'unknown')}",
                    f"text: {chunk['text']}",
                ]
            )
        )
    return "\n\n".join(lines)


def _history_messages(history: list[dict]) -> list[dict]:
    messages = []
    for item in history[-10:]:
        if item["role"] not in {"user", "assistant"}:
            continue
        messages.append({"role": item["role"], "content": item["content"]})
    return messages


def _answer_requirements(route: str, chunks: list[dict]) -> str:
    if route == "metadata":
        return (
            "This is a metadata route. Do not use transcript chunks. "
            "Cite numeric and creator facts with metadata source tags."
        )
    if route == "mixed" and chunks:
        return (
            "This is a mixed route. Use metadata for metrics and transcript chunks for content reasons. "
            "Cite at least one returned transcript chunk source tag in the answer. "
            "When comparing Video A and Video B, cite transcript chunks from both videos if available. "
            "If a metric is unavailable, say unavailable instead of treating 0 as a real value."
        )
    if chunks:
        return "Use transcript chunks for content claims and cite returned transcript chunk source tags."
    return "No transcript chunks were retrieved. State that transcript evidence is unavailable if needed."


def build_chat_messages(
    query: str,
    metadata: list[dict],
    metadata_tool_results: list[dict],
    chunks: list[dict],
    history: list[dict],
    route: str = "semantic",
) -> list[dict]:
    system = (
        "You are a creator analytics assistant comparing Video A and Video B. "
        "Use only the provided Postgres metadata tool results, metadata, transcript chunks, and chat history. "
        "For numeric or creator metadata questions, answer from Postgres metadata tool results and metadata only. "
        "For mixed comparison questions, combine metric evidence with transcript evidence "
        "and cite both when available. "
        "Cite every factual claim with the provided source tags. "
        "Copy source tags exactly, such as [Video A metadata]. "
        "Do not wrap source tags as [source_tag: ...], [citation: ...], or [POSTGRES METADATA TOOL RESULTS]. "
        "Never invent numbers. If a value is unknown or unavailable, say so directly. "
        "If the question assumes a comparison that the metadata does not support, correct that premise. "
        "Keep answers concise and useful for a social media creator."
    )
    user = "\n\n".join(
        [
            "[ROUTE]",
            route,
            "[POSTGRES METADATA TOOL RESULTS]",
            _metadata_tools_block(metadata_tool_results),
            "[METADATA]",
            _metadata_block(metadata),
            "[TRANSCRIPT CHUNKS]",
            _chunks_block(chunks),
            "[ANSWER REQUIREMENTS]",
            _answer_requirements(route, chunks),
            "[QUESTION]",
            query,
        ]
    )
    return [{"role": "system", "content": system}, *_history_messages(history), {"role": "user", "content": user}]
