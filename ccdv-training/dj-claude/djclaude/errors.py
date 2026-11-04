# arquivo: djclaude/errors.py
import anthropic


class RefusalError(Exception):
    """O modelo recusou (stop_reason == 'refusal'). Não é transitório: não faça retry."""


class LLMUnavailableError(Exception):
    """Erro transitório que persistiu depois dos retries do SDK."""


class LLMRequestError(Exception):
    """Erro terminal: a mesma requisição nunca vai funcionar (400/401/403/404...)."""


def classify(exc: Exception) -> str:
    """Esperar e repetir a MESMA requisição poderia funcionar? Sim -> retriable."""
    if isinstance(exc, (anthropic.RateLimitError, anthropic.InternalServerError,
                        anthropic.APIConnectionError, anthropic.APITimeoutError)):
        return "retriable"
    if isinstance(exc, anthropic.APIStatusError) and exc.status_code in (429, 500, 502, 503, 504, 529):
        return "retriable"
    return "terminal"


async def call_llm(client, **params):
    try:
        # O SDK (max_retries=3 em config.py) já fez backoff e respeitou retry-after.
        response = await client.messages.create(**params)
    except anthropic.APIError as exc:
        if classify(exc) == "retriable":
            raise LLMUnavailableError("API temporarily unavailable; try again shortly.") from exc
        raise LLMRequestError(f"Request rejected: {exc}") from exc
    if response.stop_reason == "refusal":      # HTTP 200! um classificador por status code não pega
        raise RefusalError("The model declined to answer this request.")
    return response
