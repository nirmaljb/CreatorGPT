import logging
import threading
import uuid

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http import models as qm

from backend.app.core.config import get_settings

_client: QdrantClient | None = None
_embedder: TextEmbedding | None = None
_client_lock = threading.Lock()
_embedder_lock = threading.Lock()
logger = logging.getLogger(__name__)


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                settings = get_settings()
                if not settings.qdrant_url:
                    raise RuntimeError("QDRANT_URL is not configured")
                logger.info("Creating Qdrant client url=%s collection=%s", settings.qdrant_url, settings.qdrant_collection)
                _client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
    return _client


def get_embedder() -> TextEmbedding:
    global _embedder
    if _embedder is None:
        with _embedder_lock:
            if _embedder is None:
                settings = get_settings()
                logger.info("Loading embedding model=%s", settings.embedding_model)
                _embedder = TextEmbedding(model_name=settings.embedding_model)
    return _embedder


def ensure_collection() -> None:
    settings = get_settings()
    client = get_qdrant_client()
    exists = client.collection_exists(settings.qdrant_collection)
    if exists:
        info = client.get_collection(settings.qdrant_collection)
        vectors = info.config.params.vectors
        actual_size = getattr(vectors, "size", None)
        if isinstance(vectors, dict):
            actual_size = next((getattr(vector, "size", None) for vector in vectors.values()), None)
        logger.info(
            "Qdrant collection already exists name=%s dimensions=%s expected_dimensions=%s",
            settings.qdrant_collection,
            actual_size or "unknown",
            settings.embedding_dimensions,
        )
        if actual_size and actual_size != settings.embedding_dimensions:
            raise RuntimeError(
                f"Qdrant collection {settings.qdrant_collection} has dimension {actual_size}; "
                f"expected {settings.embedding_dimensions}. Create a new collection or update EMBEDDING_DIMENSIONS."
            )
        ensure_payload_indexes()
        return
    logger.info(
        "Creating Qdrant collection name=%s dimensions=%s distance=cosine",
        settings.qdrant_collection,
        settings.embedding_dimensions,
    )
    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=qm.VectorParams(size=settings.embedding_dimensions, distance=qm.Distance.COSINE),
    )
    ensure_payload_indexes()


def ensure_payload_indexes() -> None:
    settings = get_settings()
    client = get_qdrant_client()
    collection_info = client.get_collection(settings.qdrant_collection)
    existing_schema = getattr(collection_info, "payload_schema", {}) or {}
    indexes = {
        "session_id": qm.PayloadSchemaType.KEYWORD,
        "video_id": qm.PayloadSchemaType.KEYWORD,
        "is_hook": qm.PayloadSchemaType.BOOL,
    }

    for field_name, field_type in indexes.items():
        if field_name in existing_schema:
            logger.info(
                "Qdrant payload index already exists collection=%s field=%s",
                settings.qdrant_collection,
                field_name,
            )
            continue
        try:
            client.create_payload_index(
                collection_name=settings.qdrant_collection,
                field_name=field_name,
                field_schema=field_type,
                wait=True,
            )
            logger.info(
                "Ensured Qdrant payload index collection=%s field=%s type=%s",
                settings.qdrant_collection,
                field_name,
                field_type,
            )
        except UnexpectedResponse as exc:
            message = str(exc).lower()
            if "already exists" in message or "same name" in message:
                logger.info(
                    "Qdrant payload index already exists collection=%s field=%s",
                    settings.qdrant_collection,
                    field_name,
                )
                continue
            raise


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return [vector.tolist() for vector in get_embedder().embed(texts)]


def _point_id(chunk: dict) -> str:
    raw = f"{chunk['session_id']}:{chunk['video_id']}:{chunk['chunk_index']}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


def upsert_chunks(chunks: list[dict]) -> int:
    if not chunks:
        logger.info("No chunks to upsert")
        return 0
    settings = get_settings()
    ensure_collection()
    vectors = embed_texts([chunk["text"] for chunk in chunks])
    points = [
        qm.PointStruct(id=_point_id(chunk), vector=vector, payload=chunk)
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]
    get_qdrant_client().upsert(collection_name=settings.qdrant_collection, points=points)
    logger.info(
        "Upserted chunks to Qdrant collection=%s session_id=%s video_id=%s count=%s",
        settings.qdrant_collection,
        chunks[0]["session_id"],
        chunks[0]["video_id"],
        len(points),
    )
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
    logger.info(
        "Retrieving chunks session_id=%s video_id=%s hook_only=%s top_k=%s query=%s",
        session_id,
        video_id or "any",
        hook_only,
        top_k,
        query,
    )

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
    logger.info("Retrieved %s chunks session_id=%s", len(output), session_id)
    return output


def health_check() -> bool:
    get_qdrant_client().get_collections()
    return True
