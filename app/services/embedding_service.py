import asyncio

from google import genai
from google.genai import types

from app.core.config import settings


class EmbeddingService:
    def __init__(self):
        self.ai_client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    async def get_embedding(
        self,
        text: str
    ):
        try:
            if not text or not text.strip():
                return None

            loop = asyncio.get_running_loop()

            result = await loop.run_in_executor(
                None,
                lambda: self.ai_client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=text,
                    config=types.EmbedContentConfig(
                        output_dimensionality=1536
                    ),
                ),
            )

            if not result or not result.embeddings:
                print("Embedding generation returned no vector.")
                return None

            embedding = result.embeddings[0]

            if not embedding or not embedding.values:
                print("Embedding vector is empty.")
                return None

            vector = list(embedding.values)

            if len(vector) != 1536:
                raise ValueError(
                    f"Expected 1536 dimensions, got {len(vector)}"
                )

            return vector

        except Exception as e:
            print(f"Embedding generation error: {e}")
            return None


embedding_service = EmbeddingService()

