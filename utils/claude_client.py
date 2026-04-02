"""
utils/claude_client.py  —  thin wrapper around Anthropic API
All Claude calls live here so you only change one place if the API evolves.
"""
import anthropic
from config import CLAUDE_API_KEY, CLAUDE_MODEL

_client = None

def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    return _client


def ask(system: str, user: str, max_tokens: int = 1500) -> str:
    """Simple single-turn call. Returns the text response."""
    resp = get_client().messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}]
    )
    return resp.content[0].text


def chat(system: str, history: list, max_tokens: int = 2000) -> str:
    """
    Multi-turn call.
    history = [{"role": "user"|"assistant", "content": "..."}]
    Returns assistant text.
    """
    resp = get_client().messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=history
    )
    return resp.content[0].text
