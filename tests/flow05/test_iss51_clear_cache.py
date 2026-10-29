"""ISS-51: clearing the cache deletes only resume_extract:*, jd_cache:* and emb:* keys."""
import fakeredis

from app.utils.cache_maintenance import clear_app_cache


def test_deletes_cache_keys_only_in_batches():
    r = fakeredis.FakeRedis(decode_responses=True)
    for i in range(1200):
        r.set(f"emb:{i}", "v")
    r.set("resume_extract:x", "v")
    r.set("jd_cache:y", "v")
    r.set("celery-task-meta-1", "v")
    r.set("emb_not_cache", "v")
    r.rpush("celery", "task")

    assert clear_app_cache(r) == 1202
    assert sorted(r.keys("*")) == ["celery", "celery-task-meta-1", "emb_not_cache"]


def test_empty_redis_deletes_nothing():
    assert clear_app_cache(fakeredis.FakeRedis()) == 0
