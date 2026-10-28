"""FLOW-01/FLOW-02 shared step — local FastEmbed embeddings with Redis cache."""
import hashlib

from app.embedding import embedding_service as es


def test_model_and_dims():
    assert (es.MODEL_NAME, es.EMBED_DIM) == ("BAAI/bge-small-en-v1.5", 384)


def test_cache_key():
    h = hashlib.sha256(b"BAAI/bge-small-en-v1.5:hello").hexdigest()
    assert es._cache_key("hello") == f"emb:{h}"


def test_blank_texts_become_single_space_and_order_is_kept(monkeypatch, fake_redis):
    monkeypatch.setattr(es, "_redis", fake_redis)
    seen = []
    monkeypatch.setattr(es, "_embed_batch", lambda texts: seen.extend(texts) or [[float(len(t))] for t in texts])

    out = es.create_embeddings(["abc", "", None, "  "])

    assert seen == ["abc", " ", " ", " "]  # duplicates within one batch are each embedded
    assert out == [[3.0], [1.0], [1.0], [1.0]]


def test_cached_texts_are_not_re_embedded(monkeypatch, fake_redis):
    monkeypatch.setattr(es, "_redis", fake_redis)
    monkeypatch.setattr(es, "_embed_batch", lambda texts: [[1.0] for _ in texts])
    es.create_embeddings(["a"])
    monkeypatch.setattr(es, "_embed_batch", lambda texts: (_ for _ in ()).throw(AssertionError))
    assert es.create_embeddings(["a"]) == [[1.0]]


def test_empty_list_returns_empty():
    assert es.create_embeddings([]) == []
