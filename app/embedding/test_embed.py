
# from app.embedding.embedding_service import create_embedding, create_embeddings

# # 1. Single
# v = create_embedding("Python developer")
# print("single:", len(v))                            # 1024

# # 2. Small batch
# vs = create_embeddings(["Python", "SQL", "Excel"])
# print("small batch:", len(vs), "x", len(vs[0]))     # 3 x 1024

# # 3. Big batch
# big = [f"skill_{i}" for i in range(250)]
# vs = create_embeddings(big)
# print("big batch:", len(vs))                        # 250

# # 4. DB round-trip — proves 1024 fits the column
# from sqlalchemy import text
# from app.database.db import engine

# with engine.begin() as conn:
#     conn.execute(text("""
#         INSERT INTO cand_skill (cand_id, skill, skill_embedding)
#         VALUES (999999, 'test-skill', CAST(:v AS vector))
#     """), {"v": str(v)})

#     row = conn.execute(text("""
#         SELECT skill, vector_dims(skill_embedding)
#         FROM cand_skill WHERE cand_id = 999999
#     """)).first()
#     print("db round-trip:", row[0], row[1])         # test-skill 1024

#     conn.execute(text("DELETE FROM cand_skill WHERE cand_id = 999999"))

# print("ALL OK")
from fastembed import TextEmbedding

# Point FastEmbed exactly to the cache folder you found
model = TextEmbedding(
    model_name="BAAI/bge-small-en-v1.5",
    cache_dir="/tmp/fastembed_cache"
)

# Test a quick embedding
vec = list(model.embed(["Testing the local cache"]))
print(f"Success! Generated a vector with {len(vec[0])} dimensions.")