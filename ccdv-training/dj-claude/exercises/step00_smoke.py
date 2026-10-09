import os
import anthropic
from djclaude.config import MODEL_WORKER

# Disregard this after paying my own API key
# auth_token = os.getenv('ANTHROPIC_AUTH_TOKEN')
# base_url = os.getenv('ANTHROPIC_BASE_URL')

client = anthropic.Anthropic()

r = client.messages.create(
    model=MODEL_WORKER,
    max_tokens=50,
    messages=[{"role": "user", "content": "Diga 'ok' em português."}]
)

print(r.content[0].text, r.usage)
