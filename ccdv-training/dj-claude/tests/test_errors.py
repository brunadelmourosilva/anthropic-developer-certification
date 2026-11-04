# arquivo: tests/test_errors.py
import anthropic
import httpx
from djclaude.errors import classify


def _status_error(cls, code):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return cls("boom", response=httpx.Response(code, request=request), body=None)


def test_rate_limit_is_retriable():
    assert classify(_status_error(anthropic.RateLimitError, 429)) == "retriable"


def test_auth_error_is_terminal():
    assert classify(_status_error(anthropic.AuthenticationError, 401)) == "terminal"


def test_not_found_is_terminal():
    assert classify(_status_error(anthropic.NotFoundError, 404)) == "terminal"
