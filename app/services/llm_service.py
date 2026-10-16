import asyncio
from typing import List

import httpx
from google import genai

from app.core.config import settings


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()

        self.ollama_url = (
            f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        )
        self.ollama_model = settings.OLLAMA_MODEL

        self.ai_client = None

        if self.provider == "gemini":
            self.ai_client = genai.Client(
                api_key=settings.GEMINI_API_KEY
            )

    async def generate_rag_answer(
        self,
        question: str,
        contexts: List[str],
    ) -> str:
        if not question or not question.strip():
            return "Please provide a question."

        valid_contexts = [
            context.strip()
            for context in contexts
            if context and context.strip()
        ]

        if not valid_contexts:
            return (
                "I'm sorry, but I couldn't find the answer "
                "in the uploaded documentation."
            )

        merged_context = "\n\n---\n\n".join(valid_contexts)

        prompt = f"""
You are DevDocs AI, an expert software developer assistant.

Answer the user's question using ONLY the documentation context
provided below.

Rules:
1. Do not invent facts that are not present in the context.
2. If the context does not contain the answer, say:
   "I'm sorry, but I couldn't find the answer in the uploaded documentation."
3. Explain technical concepts clearly.
4. Use examples only when supported by the documentation.
5. Keep the answer relevant to the user's question.

[Documentation Context]
{merged_context}

[User Question]
{question}

[Answer]
"""

        # Ollama provider
        if self.provider == "ollama":
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
            }

            try:
                async with httpx.AsyncClient(
                    timeout=90.0
                ) as client:
                    response = await client.post(
                        self.ollama_url,
                        json=payload,
                    )

                    response.raise_for_status()

                    answer = response.json().get("response")

                    if answer:
                        return answer

                    return "No response received from Ollama."

            except httpx.HTTPStatusError as e:
                print(f"Ollama HTTP error: {e}")

                return (
                    f"Ollama API Error: "
                    f"HTTP {e.response.status_code}"
                )

            except httpx.RequestError as e:
                print(f"Ollama connection error: {e}")

                return (
                    "Failed to connect to local Ollama. "
                    "Check whether Ollama is running."
                )

            except Exception as e:
                print(f"Ollama generation error: {e}")
                return "An error occurred while generating the answer."

        # Gemini provider
        elif self.provider == "gemini":
            try:
                loop = asyncio.get_running_loop()

                response = await loop.run_in_executor(
                    None,
                    lambda: self.ai_client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=prompt,
                    ),
                )

                if response and response.text:
                    return response.text.strip()

                return "No response text received from Gemini API."

            except Exception as e:
                print(f"Gemini API Error: {e}")

                return (
                    "An error occurred while generating the "
                    "answer with Gemini."
                )

        return "Unknown LLM provider configured."


# Global service instance
llm_service = LLMService()

