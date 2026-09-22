from google import genai
from google.genai import types
import os


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def create_embedding(text: str) -> list[float]:

    if not text or not text.strip():
        raise ValueError(
            "Cannot embed empty text"
        )

    response = client.models.embed_content(
        model="text-embedding-004",
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=768,
            task_type="SEMANTIC_SIMILARITY",
        ),
    )

    return response.embeddings[0].values


def create_embeddings(
    texts: list[str],
) -> list[list[float]]:

    clean_texts = [
        text.strip()
        for text in texts
        if text and text.strip()
    ]

    if not clean_texts:
        return []

    response = client.models.embed_content(
        model="text-embedding-004",
        contents=clean_texts,
        config=types.EmbedContentConfig(
            output_dimensionality=768,
            task_type="SEMANTIC_SIMILARITY",
        ),
    )

    return [
        embedding.values
        for embedding in response.embeddings
    ]