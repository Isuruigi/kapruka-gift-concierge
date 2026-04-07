"""
Tier 1: Short-Term Memory - Session Conversation Buffer
=======================================================
Maintains the current conversation as a rolling window of messages.
Automatically trims to max_messages.
"""

from datetime import datetime


class ConversationMemory:
    """Rolling message buffer for a single chat session."""

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self._messages: list[dict] = []  # [{role, content, timestamp}]

    # ── Write ──────────────────────────────────────────────

    def add_message(self, role: str, content: str):
        """Append a message. Role must be 'user' or 'assistant'."""
        self._messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
        )
        # Trim if over the window
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages :]

    # ── Read ───────────────────────────────────────────────

    def get_messages(self) -> list[dict]:
        """Return messages in Anthropic API format (role + content only)."""
        return [{"role": m["role"], "content": m["content"]} for m in self._messages]

    def get_context_summary(self, n: int = 6) -> str:
        """Return a brief text summary of the last N exchanges for injecting into prompts."""
        if not self._messages:
            return "No previous conversation."
        recent = self._messages[-n:]
        return "\n".join(
            f"{m['role'].upper()}: {m['content'][:120]}" for m in recent
        )

    def get_last_n(self, n: int = 5) -> list[dict]:
        """Return last N messages in Anthropic API format."""
        return [
            {"role": m["role"], "content": m["content"]}
            for m in self._messages[-n:]
        ]

    def get_last_user_message(self) -> str | None:
        """Return the most recent user message text, or None."""
        for m in reversed(self._messages):
            if m["role"] == "user":
                return m["content"]
        return None

    # ── Management ─────────────────────────────────────────

    def clear(self):
        """Reset the buffer (start a new session)."""
        self._messages = []

    def __len__(self) -> int:
        return len(self._messages)

    def __repr__(self) -> str:
        return f"ConversationMemory(messages={len(self._messages)}, max={self.max_messages})"
