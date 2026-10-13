import google.generativeai as genai
from app.core.config import settings

class EmbeddingService:
    def __init__(self):

        genai.configure(api_key=settings.GEMINI_API_KEY)

    async def get_embedding(self, text: str) -> list[float]:

        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            print(f"Embedding Query generation error: {str(e)}")
            return None

embedding_service = EmbeddingService()
