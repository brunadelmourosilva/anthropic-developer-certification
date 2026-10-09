# Anthropic SDK for Python: https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL_LEAD = "claude-sonnet-5-5"
MODEL_WORKER = "claude-haiku-5-5"
MODEL_JUDGE = "claude-sonnet-5-5"

def make_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(max_retries=3, timeout=60.0)