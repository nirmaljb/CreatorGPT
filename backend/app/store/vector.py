import uuid

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from backend.app.core.config import get_settings

_client: QdrantClient | None = None
_embedder: TextEmbedding | None = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.qdrant_url:
            raise RuntimeError("QDRANT_URL is not configured")
        _client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
    return _client


def get_embedder() -> TextEmbedding:
    global _embedder
    if _embedder is None:
        settings = get_settings()
        _embedder = TextEmbedding(model_name=settings.embedding_model)
    return _embedder


def ensure_collection() -> None:
    settings = get_settings()
    client = get_qdrant_client()
    exists = client.collection_exists(settings.qdrant_collection)
    if exists:
        return
    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=qm.VectorParams(size=settings.embedding_dimensions, distance=qm.Distance.COSINE),
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return [vector.tolist() for vector in get_embedder().embed(texts)]


def _point_id(chunk: dict) -> str:
    raw = f"{chunk['session_id']}:{chunk['video_id']}:{chunk['chunk_index']}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


def upsert_chunks(chunks: list[dict]) -> int:
    if not chunks:
        return 0
    settings = get_settings()
    ensure_collection()
    vectors = embed_texts([chunk["text"] for chunk in chunks])
    points = [
        qm.PointStruct(id=_point_id(chunk), vector=vector, payload=chunk)
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]
    get_qdrant_client().upsert(collection_name=settings.qdrant_collection, points=points)
    return len(points)


def retrieve(
    query: str,
    session_id: str,
    video_id: str | None = None,
    hook_only: bool = False,
    top_k: int = 6,
) -> list[dict]:
    settings = get_settings()
    ensure_collection()
    must = [qm.FieldCondition(key="session_id", match=qm.MatchValue(value=session_id))]
    if video_id:
        must.append(qm.FieldCondition(key="video_id", match=qm.MatchValue(value=video_id)))
    if hook_only:
        must.append(qm.FieldCondition(key="is_hook", match=qm.MatchValue(value=True)))

    query_filter = qm.Filter(must=must)
    vector = embed_texts([query])[0]
    client = get_qdrant_client()

    try:
        hits = client.search(
            collection_name=settings.qdrant_collection,
            query_vector=vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )
    except AttributeError:
        result = client.query_points(
            collection_name=settings.qdrant_collection,
            query=vector,
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )
        hits = result.points

    output = []
    for hit in hits:
        payload = hit.payload or {}
        payload["score"] = getattr(hit, "score", None)
        output.append(payload)
    return output


def health_check() -> bool:
    get_qdrant_client().get_collections()
    return True
