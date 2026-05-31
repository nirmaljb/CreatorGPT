from backend.app.ingest.chunker import format_timestamp


def metadata_source_tag(video_id: str) -> str:
    return f"[Video {video_id} metadata]"


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
        followers = item["creator_followers"] if item["creator_followers"] else "unavailable"
        lines.append(
            "\n".join(
                [
                    f"{metadata_source_tag(item['video_id'])}",
                    f"platform: {item['platform']}",
                    f"creator: {item['creator']}",
                    f"creator_followers: {followers}",
                    f"views: {item['views']}",
                    f"likes: {item['likes']}",
                    f"comments: {item['comments']}",
                    f"engagement_rate_percent: {item['engagement_rate']}",
                    f"duration_seconds: {item['duration_seconds']}",
                    f"upload_date: {item['upload_date'] or 'unknown'}",
                    f"hashtags: {', '.join(item['hashtags']) if item['hashtags'] else 'none'}",
                ]
            )
        )
    return "\n\n".join(lines) if lines else "No metadata available."


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


def build_chat_messages(
    query: str,
    metadata: list[dict],
    chunks: list[dict],
    history: list[dict],
) -> list[dict]:
    system = (
        "You are a creator analytics assistant comparing Video A and Video B. "
        "Use only the provided metadata, transcript chunks, and chat history. "
        "Cite every factual claim with the provided source tags. "
        "Never invent numbers. If a value is unknown or unavailable, say so directly. "
        "Keep answers concise and useful for a social media creator."
    )
    user = "\n\n".join(
        [
            "[METADATA]",
            _metadata_block(metadata),
            "[TRANSCRIPT CHUNKS]",
            _chunks_block(chunks),
            "[QUESTION]",
            query,
        ]
    )
    return [{"role": "system", "content": system}, *_history_messages(history), {"role": "user", "content": user}]
