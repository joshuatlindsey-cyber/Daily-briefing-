"""Orchestrator CLI: edit a video, then publish it to all four platforms.

Examples
--------
# Full pipeline: Descript edit + render, then fan out to all platforms.
python -m src.pipeline \
    --video-url https://example.com/raw.mp4 \
    --caption "My take on content leverage" \
    --edit

# Skip editing — you already have a public video URL, just publish it.
python -m src.pipeline \
    --video-url https://share.descript.com/view/abc123 \
    --caption "My take on content leverage"

# See exactly what would be posted without sending anything.
python -m src.pipeline --video-url https://x/v.mp4 --caption "hi" --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys

from . import descript
from .captions import build_captions
from .config import load_config, require_env
from .publisher import publish_video


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI edit + multi-platform video publisher")
    parser.add_argument("--video-url", required=True, help="Public URL to the source video")
    parser.add_argument("--caption", required=True, help="Base caption; reshaped per platform")
    parser.add_argument("--edit", action="store_true", help="Run the Descript edit/render step first")
    parser.add_argument("--project-name", default="Pipeline Edit", help="Descript project name (with --edit)")
    parser.add_argument("--resolution", default="1080p", help="Render resolution (with --edit)")
    parser.add_argument("--schedule-at", help="ISO-8601 UTC, e.g. 2026-06-16T09:00:00Z (default: post now)")
    parser.add_argument("--platforms", help="Comma list overriding config (e.g. linkedin,youtube)")
    parser.add_argument("--config", help="Path to config.json")
    parser.add_argument("--dry-run", action="store_true", help="Build requests but don't post")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    platforms = (
        [p.strip() for p in args.platforms.split(",")] if args.platforms else cfg["platforms"]
    )

    video_url = args.video_url
    if args.edit:
        print("→ Editing + rendering in Descript…")
        token = require_env("DESCRIPT_API_TOKEN")
        video_url = descript.edit_and_render(
            token, video_url, args.project_name, resolution=args.resolution
        )
        print(f"  rendered: {video_url}")

    print(f"→ Building captions for: {', '.join(platforms)}")
    captions = build_captions(args.caption, platforms, cfg.get("captions", {}))

    print("→ Publishing…")
    api_key = "DRY-RUN" if args.dry_run else require_env("AYRSHARE_API_KEY")
    results = publish_video(
        api_key=api_key,
        video_url=video_url,
        captions=captions,
        platforms=platforms,
        platform_options=cfg.get("platform_options", {}),
        schedule_at=args.schedule_at,
        dry_run=args.dry_run,
    )

    print("\nResult:")
    print(json.dumps(results, indent=2))
    return 1 if results.get("errors") and not results.get("posts") else 0


if __name__ == "__main__":
    sys.exit(main())
