import unittest
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch

from app.api.v1.ai.ai_chat_router import ai_chat
from app.api.v1.model import model_router
from app.schemas.chat_schema import ChatRequest
from app.services.llm_service import LLMProviderError, LLMService, llm_service


class ProviderSelectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_gemini_uses_configured_default_model_when_model_is_omitted(self):
        service = LLMService()
        generate = AsyncMock(return_value="answer")
        with (
            patch.object(service, "_generate_gemini", generate),
            patch.object(
                model_router.settings,
                "DEFAULT_MODEL_PROVIDER",
                "gemini",
            ),
            patch.object(
                model_router.settings,
                "DEFAULT_MODEL",
                "gemini-3.5-flash-lite",
            ),
        ):
            await service.generate_rag_answer(
                question="hello",
                provider="gemini",
            )

        self.assertEqual(
            generate.await_args.kwargs["model"],
            "gemini-3.5-flash-lite",
        )

    async def test_chat_passes_selected_provider_and_model(self):
        generate = AsyncMock(return_value="answer")
        with patch.object(llm_service, "generate_rag_answer", generate):
            response = await ai_chat(
                ChatRequest(
                    question="hello",
                    provider="openrouter",
                    model="openrouter/free",
                ),
                db=None,
                current_user=1,
            )

        self.assertEqual(response.answer, "answer")
        generate.assert_awaited_once_with(
            question="hello",
            contexts=[],
            provider="openrouter",
            model="openrouter/free",
        )

    async def test_removed_provider_is_rejected(self):
        with self.assertRaises(LLMProviderError) as error:
            await LLMService().generate_rag_answer(
                question="hello",
                provider="groq",
                model="model-id",
            )

        self.assertEqual(error.exception.status_code, 422)

    async def test_chat_surfaces_provider_limit_to_user(self):
        raise_limit = AsyncMock(
            side_effect=LLMProviderError(
                "OpenRouter usage limit reached. Try again in 30 seconds.",
                429,
                retry_after_seconds=30,
            )
        )
        with patch.object(llm_service, "generate_rag_answer", raise_limit):
            with self.assertRaises(HTTPException) as error:
                await ai_chat(
                    ChatRequest(
                        question="hello",
                        provider="openrouter",
                        model="model-id",
                    ),
                    db=None,
                    current_user=1,
                )

        self.assertEqual(error.exception.status_code, 429)
        self.assertIn("30 seconds", error.exception.detail)
        self.assertEqual(error.exception.headers["Retry-After"], "30")

    async def test_model_catalog_includes_supported_providers(self):
        async def fake_catalog(status_info, provider):
            status_info.update(
                configured=True,
                available=True,
                message="loaded",
            )
            return [
                {
                    "provider": provider,
                    "model": "model-id",
                    "name": "Model",
                    "free": True,
                    "available": True,
                    "description": "Test model",
                }
            ]

        def catalog_for(provider):
            async def fetch(status_info):
                return await fake_catalog(status_info, provider)

            return fetch

        with (
            patch.object(
                model_router,
                "_ollama_models",
                new=catalog_for("ollama"),
            ),
            patch.object(
                model_router,
                "_gemini_models",
                new=catalog_for("gemini"),
            ),
            patch.object(
                model_router,
                "_openrouter_models",
                new=catalog_for("openrouter"),
            ),
        ):
            response = await model_router.get_available_models()

        self.assertEqual(
            {item["provider"] for item in response["models"]},
            {"ollama", "gemini", "openrouter"},
        )
        self.assertGreaterEqual(response["count"], 3)

    async def test_openrouter_catalog_keeps_only_zero_price_models(self):
        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "data": [
                        {
                            "id": "openrouter/free",
                            "name": "Free router",
                            "pricing": {"prompt": "0", "completion": "0"},
                        },
                        {
                            "id": "free-model",
                            "name": "Free model",
                            "pricing": {"prompt": "0", "completion": "0"},
                        },
                        {
                            "id": "paid-model",
                            "pricing": {"prompt": "0.1", "completion": "0"},
                        },
                    ]
                }

        class FakeClient:
            def __init__(self, **kwargs):
                self.timeout = kwargs.get("timeout")

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                _ = args
                return None

            async def get(self, *args, **kwargs):
                _ = args, kwargs
                return FakeResponse()

        status_info = {}
        with (
            patch.object(
                model_router.settings,
                "OPENROUTER_API_KEY",
                "test-key",
            ),
            patch.object(model_router.httpx, "AsyncClient", FakeClient),
        ):
            models = await model_router._openrouter_models(status_info)

        self.assertEqual(
            {item["model"] for item in models},
            {"openrouter/free", "free-model"},
        )
        self.assertTrue(all(item["free"] is True for item in models))
        self.assertTrue(status_info["available"])

    async def test_gemini_catalog_keeps_only_configured_free_models(self):
        class FakeModel:
            def __init__(self, name):
                self.name = name
                self.display_name = name
                self.supported_actions = ["generateContent"]

        class FakeModels:
            def list(self, **kwargs):
                _ = kwargs
                return [
                    FakeModel("models/free-model"),
                    FakeModel("models/paid-model"),
                ]

        class FakeGeminiClient:
            models = FakeModels()

        status_info = {}
        with (
            patch.object(model_router.settings, "GEMINI_API_KEY", "test-key"),
            patch.object(model_router.settings, "GEMINI_FREE_MODELS", "free-model"),
            patch.object(model_router.llm_service, "gemini_client", FakeGeminiClient()),
        ):
            models = await model_router._gemini_models(status_info)

        self.assertEqual(
            {item["model"] for item in models},
            {"free-model"},
        )
        self.assertTrue(all(item["free"] is True for item in models))
        self.assertTrue(status_info["available"])

    def test_backend_configured_models_are_always_in_catalog(self):
        models = [
            model_router._model(
                "ollama",
                "qwen3:4b",
                "qwen3:4b",
                "Already listed by Ollama.",
                available=False,
            )
        ]
        with (
            patch.object(model_router.settings, "DEFAULT_MODEL_PROVIDER", "openrouter"),
            patch.object(model_router.settings, "DEFAULT_MODEL", "openrouter/free"),
            patch.object(model_router.settings, "LLM_PROVIDER", "ollama"),
            patch.object(model_router.settings, "OLLAMA_MODEL", "qwen3:4b"),
        ):
            model_router._include_backend_defaults(models)

        configured = [
            item for item in models if item["configured_default"]
        ]
        self.assertEqual(
            {(item["provider"], item["model"]) for item in configured},
            {("openrouter", "openrouter/free"), ("ollama", "qwen3:4b")},
        )
        self.assertTrue(next(
            item
            for item in configured
            if item["provider"] == "ollama"
        )["available"] is False)

    def test_gemini_default_is_catalogued_when_another_provider_is_configured(self):
        models = []
        with (
            patch.object(
                model_router.settings,
                "DEFAULT_MODEL_PROVIDER",
                "gemini",
            ),
            patch.object(
                model_router.settings,
                "DEFAULT_MODEL",
                "gemini-3.5-flash-lite",
            ),
            patch.object(model_router.settings, "LLM_PROVIDER", "ollama"),
            patch.object(model_router.settings, "OLLAMA_MODEL", "qwen3:4b"),
        ):
            model_router._include_backend_defaults(models)

        self.assertTrue(
            any(
                model["provider"] == "gemini"
                and model["model"] == "gemini-3.5-flash-lite"
                and model["configured_default"]
                for model in models
            )
        )
        default_model = next(
            model
            for model in models
            if model["provider"] == "gemini"
            and model["model"] == "gemini-3.5-flash-lite"
        )
        self.assertIsNone(default_model["free"])
        self.assertTrue(default_model["configured_default"])


class ProviderErrorTests(unittest.TestCase):
    def test_generated_answer_removes_internal_safety_label(self):
        answer = LLMService._clean_generated_answer(
            "User Safety: safe\n\nI'm doing well, thanks!"
        )

        self.assertEqual(answer, "I'm doing well, thanks!")

    def test_generated_answer_preserves_normal_content(self):
        answer = LLMService._clean_generated_answer(
            "I'm doing well, thank you!"
        )

        self.assertEqual(answer, "I'm doing well, thank you!")

    def test_generated_answer_removes_model_control_markers(self):
        answer = LLMService._clean_generated_answer(
            "[[A0]]\n[:] Hello, there!\n[[B1]]\n[:] How can I help?"
        )

        self.assertEqual(answer, "Hello, there!\nHow can I help?")

    def test_prompt_requests_plain_conversational_answers_for_all_modes(self):
        service = LLMService()

        general_prompt = service._build_prompt("hello")
        document_prompt = service._build_prompt("hello", ["Example context"])

        for prompt in (general_prompt, document_prompt):
            self.assertIn("natural conversational", prompt)
            self.assertIn("Do not turn the answer into a song, poem, verse", prompt)

    def test_default_provider_uses_configured_default_model_provider(self):
        service = LLMService()
        self.assertEqual(
            service.default_provider,
            model_router.settings.DEFAULT_MODEL_PROVIDER.lower(),
        )

    def test_http_rate_limit_message_includes_provider_reset_time(self):
        with self.assertRaises(LLMProviderError) as error:
            LLMService._raise_http_error(
                "OpenRouter",
                429,
                "30 seconds",
            )

        self.assertEqual(error.exception.status_code, 429)
        self.assertIn("Try again in 30 seconds", error.exception.message)
        self.assertEqual(error.exception.retry_after_seconds, 30)

    def test_retry_after_parser_supports_provider_duration_headers(self):
        self.assertEqual(LLMService._retry_after_seconds("2m30.5s"), 150.5)
        self.assertEqual(LLMService._retry_after_seconds("4.5"), 4.5)
        self.assertIsNone(LLMService._retry_after_seconds("unknown"))
