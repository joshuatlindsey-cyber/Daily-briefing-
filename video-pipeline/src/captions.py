"""Per-platform caption building.

Each platform wants a different shape: LinkedIn likes a hook + a question,
YouTube needs a real title, TikTok/Instagram lean on hashtags. We start from
one "base" caption and reshape it per platform using the templates in
config.json. Optionally, an LLM can rewrite the base per platform first.
"""
from __future__ import annotations

import os
from typing import Any


def _apply_template(base: str, spec: dict[str, Any]) -> str:
    template = spec.get("template", "{base}")
    text = template.replace("{base}", base).strip()

    hashtags = spec.get("hashtags") or []
    if hashtags:
        text = f"{text}\n\n{' '.join(hashtags)}".strip()

    max_chars = spec.get("max_chars")
    if max_chars and len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
    return text


def _ai_rewrite(base: str, platform: str) -> str:
    """Rewrite the base caption for a platform's voice using Claude.

    Only called when CAPTIONS_USE_AI=1 and anthropic is installed. Falls back
    to the base text on any failure so the pipeline never breaks on captions.
    """
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        prompt = (
            f"Rewrite this caption for {platform}. Match the platform's native "
            f"tone and length norms. Return only the caption text, no preamble.\n\n"
            f"{base}"
        )
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception as exc:  # noqa: BLE001 - captions must never be fatal
        print(f"  [captions] AI rewrite for {platform} failed ({exc}); using base text")
        return base


def build_captions(base: str, platforms: list[str], caption_cfg: dict[str, Any]) -> dict[str, str]:
    """Return {platform: caption} for every requested platform."""
    use_ai = os.environ.get("CAPTIONS_USE_AI", "0") == "1"
    result: dict[str, str] = {}
    for platform in platforms:
        source = _ai_rewrite(base, platform) if use_ai else base
        result[platform] = _apply_template(source, caption_cfg.get(platform, {}))
    return result
