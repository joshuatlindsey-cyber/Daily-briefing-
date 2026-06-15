"""Multi-platform publisher built on the Ayrshare API.

One call to Ayrshare's /post endpoint fans a single video out to LinkedIn,
YouTube, TikTok and Instagram. Ayrshare has already done the per-platform
OAuth + app-review work, so we don't have to integrate each network natively.

Docs: https://www.ayrshare.com/docs/apis/post/post
Each social account is linked once in the Ayrshare dashboard; this module just
hands Ayrshare a public video URL plus per-platform captions and options.
"""
from __future__ import annotations

from typing import Any

import requests

AYRSHARE_POST_URL = "https://api.ayrshare.com/api/post"

# Map our platform names -> Ayrshare's per-platform options key.
_OPTIONS_KEY = {
    "youtube": "youTubeOptions",
    "instagram": "instagramOptions",
    "tiktok": "tikTokOptions",
    "linkedin": "linkedInOptions",
}


class PublishError(RuntimeError):
    pass


def publish_video(
    api_key: str,
    video_url: str,
    captions: dict[str, str],
    platforms: list[str],
    platform_options: dict[str, dict[str, Any]] | None = None,
    schedule_at: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Post one video to many platforms.

    Args:
        api_key: Ayrshare API key.
        video_url: PUBLIC URL to the rendered video (e.g. a Descript share/download URL).
        captions: {platform: caption_text}.
        platforms: subset of linkedin/youtube/tiktok/instagram.
        platform_options: {platform: {...}} merged into the platform's options object.
        schedule_at: ISO-8601 UTC (e.g. "2026-06-16T09:00:00Z"); None posts now.
        dry_run: build and print the request body without sending.

    Returns the Ayrshare response (or the would-be payload when dry_run).
    """
    platform_options = platform_options or {}

    # Ayrshare takes a single `post` text field. Since each platform may want
    # different copy, we post per platform so every network gets its own caption
    # and options, then aggregate the results.
    results: dict[str, Any] = {"posts": [], "errors": []}

    for platform in platforms:
        payload: dict[str, Any] = {
            "post": captions.get(platform, ""),
            "platforms": [platform],
            "mediaUrls": [video_url],
            "isVideo": True,
        }

        opts = dict(platform_options.get(platform, {}))
        # YouTube requires a title; fall back to the caption's first line.
        if platform == "youtube" and "title" not in opts:
            opts["title"] = (captions.get(platform, "Video").splitlines() or ["Video"])[0][:100]
        if opts:
            payload[_OPTIONS_KEY[platform]] = opts

        if schedule_at:
            payload["scheduleDate"] = schedule_at

        if dry_run:
            print(f"  [dry-run] {platform}: {payload}")
            results["posts"].append({"platform": platform, "dryRun": True, "payload": payload})
            continue

        resp = requests.post(
            AYRSHARE_POST_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=120,
        )
        body = _safe_json(resp)

        if resp.status_code >= 400 or body.get("status") == "error":
            results["errors"].append({"platform": platform, "status": resp.status_code, "response": body})
            print(f"  ✗ {platform}: {body.get('message') or resp.status_code}")
        else:
            post_url = _extract_post_url(body)
            results["posts"].append({"platform": platform, "postUrl": post_url, "response": body})
            print(f"  ✓ {platform}: {post_url or 'posted'}")

    if results["errors"] and not results["posts"]:
        raise PublishError(f"All platforms failed: {results['errors']}")
    return results


def _safe_json(resp: requests.Response) -> dict[str, Any]:
    try:
        return resp.json()
    except ValueError:
        return {"status": "error", "message": resp.text[:500]}


def _extract_post_url(body: dict[str, Any]) -> str | None:
    for entry in body.get("postIds", []) or []:
        if entry.get("postUrl"):
            return entry["postUrl"]
    return body.get("postUrl")
