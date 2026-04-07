"""
Anthropic API wrapper - single shared LLM client for the entire project.
All agents use this; never instantiate anthropic.Anthropic directly elsewhere.
"""

import json
import anthropic


class LLMClient:
    """Thin wrapper around the Anthropic Messages API."""

    def __init__(self, settings):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.settings = settings

    # ──────────────────────────────────────────────────────
    # Core call methods
    # ──────────────────────────────────────────────────────

    def call(
        self,
        system_prompt: str,
        user_message: str,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
    ) -> str:
        """
        Single-turn LLM call.
        Returns the text content of the first content block.
        """
        model = model or self.settings.LLM_MODEL_FAST
        temperature = (
            temperature if temperature is not None
            else self.settings.LLM_TEMPERATURE_DETERMINISTIC
        )
        max_tokens = max_tokens or self.settings.LLM_MAX_TOKENS

        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    def call_with_history(
        self,
        system_prompt: str,
        messages: list[dict],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
    ) -> str:
        """
        Multi-turn LLM call with full conversation history.
        `messages` should be in Anthropic format: [{role, content}, ...]
        """
        model = model or self.settings.LLM_MODEL_FAST
        temperature = (
            temperature if temperature is not None
            else self.settings.LLM_TEMPERATURE_DETERMINISTIC
        )
        max_tokens = max_tokens or self.settings.LLM_MAX_TOKENS

        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text

    def call_json(
        self,
        system_prompt: str,
        user_message: str,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        default: dict = None,
    ) -> dict:
        """
        LLM call that expects JSON back.
        Automatically strips markdown fences if the model wraps in ```json.
        Returns `default` dict on parse failure.
        """
        raw = self.call(
            system_prompt=system_prompt,
            user_message=user_message,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Strip possible markdown fences
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last fence line
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract a JSON object from the text
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            return default or {}
