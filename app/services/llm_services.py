import httpx
from typing import List

import google.generativeai as genai

from app.core.config import settings


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()

        self.ollama_url = f"{settings.OLLAMA_BASE_URL}/api/generate"

        self.ollama_model = settings.OLLAMA_MODEL


        if self.provider == "gemini":
            genai.configure(api_key=settings.GEMINI_API_KEY)

    async def generate_rag_answer(self, question: str, contexts: List[str]) :

        merged_context = "\n---\n".join(contexts)

        prompt = f"""
You are DevDocs AI, an expert software developer assistant. 
Answer the user's question accurately using ONLY the provided documentation context below. 
If the answer cannot be found in the context, reply with "I'm sorry, but I couldn't find the answer in the uploaded documentation." Do not make up facts.

[Documentation Context]
{merged_context}

[User Question]
{question}

[Expert Answer]
"""


        if self.provider == "ollama":
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False
            }
            try:
                async with httpx.AsyncClient(timeout=90.0) as client:
                    response = await client.post(self.ollama_url, json=payload)
                    if response.status_code == 200:
                        return response.json().get("response", "No response from AI.")
                    return f"Ollama Error: Status code {response.status_code}"
            except Exception as e:
                return f"Failed to connect to local Ollama: {str(e)}"


        elif self.provider == "gemini":
            try:

                model = genai.GenerativeModel("gemini-1.5-flash")

                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text
                return "No response text received from Gemini API."
            except Exception as e:
                return f"Gemini API Error: {str(e)}"

        return "Unknown LLM Provider configured."


# global object create
document_service = LLMService()
