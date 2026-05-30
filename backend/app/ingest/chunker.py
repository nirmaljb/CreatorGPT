def format_timestamp(seconds: float) -> str:
    seconds = max(0, int(seconds))
    minutes, secs = divmod(seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def source_tag(chunk: dict) -> str:
    return (
        f"[Video {chunk['video_id']}, chunk {chunk['chunk_index']}, "
        f"{format_timestamp(chunk['start_time'])}-{format_timestamp(chunk['end_time'])}]"
    )


def chunk_transcript(
    words: list[dict],
    metadata: dict,
    window_size: int = 60,
    overlap: int = 12,
) -> list[dict]:
    if not words:
        return []
    if overlap >= window_size:
        raise ValueError("overlap must be smaller than window_size")

    chunks: list[dict] = []
    step = window_size - overlap
    index = 0
    for start in range(0, len(words), step):
        window = words[start : start + window_size]
        if not window:
            continue
        text = " ".join(word["text"] for word in window)
        start_time = float(window[0]["start"])
        end_time = float(window[-1]["end"])
        chunk = {
            "session_id": metadata["session_id"],
            "video_id": metadata["video_id"],
            "chunk_index": index,
            "text": text,
            "start_time": start_time,
            "end_time": end_time,
            "is_hook": start_time < 5.0,
            "engagement_rate": metadata["engagement_rate"],
            "creator": metadata["creator"],
            "url": metadata["url"],
        }
        chunk["source_tag"] = source_tag(chunk)
        chunks.append(chunk)
        index += 1
    return chunks
