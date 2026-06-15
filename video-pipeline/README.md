# Video Pipeline — AI edit + one-shot publish to 4 platforms

Edit a video with AI, then publish it to **LinkedIn, YouTube, TikTok and
Instagram** in a single command. No more uploading to four places by hand.

```
raw video ──▶ Descript AI edit + render ──▶ per-platform captions ──▶ Ayrshare ──▶ 4 platforms
              (optional, --edit)                                       (one call, fans out)
```

## Why this shape

- **Publishing** uses [Ayrshare](https://www.ayrshare.com/), a multi-platform
  API that has already done the per-network OAuth and app-review work. One API
  key + one linked account per network, and a single request reaches all four.
  Building those four integrations natively means a separate OAuth flow and a
  platform approval process each (TikTok and Instagram especially gatekeep
  video-publish access) — weeks of setup we skip entirely.
- **Editing** uses Descript's AI ("remove filler words, add captions, tighten
  the intro"). Descript's REST API is in **beta**; the most reliable way to drive
  the AI edit today is the Descript MCP (`prompt_project_agent` + `publish_project`).
  `src/descript.py` covers the headless import + render bookends — see the note at
  the top of that file. If you already have a rendered, public video URL, skip
  editing and just publish.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env            # add AYRSHARE_API_KEY (and DESCRIPT_API_TOKEN if editing)
cp config.example.json config.json
```

1. **Ayrshare**: create an account, grab your API key, and link your LinkedIn,
   YouTube, TikTok and Instagram accounts in the Ayrshare dashboard (one-time).
2. **Descript** (only for `--edit`): Settings → API Tokens → create a token.
3. Edit `config.json` to set platforms, caption templates and per-platform
   options (YouTube title/visibility, IG reels, TikTok privacy, …).

## Usage

```bash
# Already have a public video URL — just publish it everywhere:
python -m src.pipeline --video-url https://share.descript.com/view/abc --caption "My take on content leverage"

# Full pipeline: AI edit + render in Descript, then publish:
python -m src.pipeline --video-url https://example.com/raw.mp4 --caption "My take" --edit

# Schedule instead of posting now:
python -m src.pipeline --video-url https://x/v.mp4 --caption "My take" --schedule-at 2026-06-16T09:00:00Z

# Preview the exact requests without sending anything (no API key needed):
python -m src.pipeline --video-url https://x/v.mp4 --caption "My take" --dry-run
```

## Captions

One base caption is reshaped per platform via `config.json` templates
(`{base}` is substituted, hashtags appended, length clamped). Set
`CAPTIONS_USE_AI=1` (and `ANTHROPIC_API_KEY`) to have Claude rewrite the base in
each platform's native voice before templating. AI caption failures fall back to
the base text — captions never break a publish.

## Layout

| File | Role |
|------|------|
| `src/pipeline.py` | CLI orchestrator (edit → captions → publish) |
| `src/publisher.py` | Ayrshare multi-platform publisher (the core) |
| `src/descript.py` | Descript import + render (beta REST; MCP recommended for the AI edit) |
| `src/captions.py` | Per-platform caption building (template + optional AI) |
| `src/config.py` | Loads secrets from `.env`, behaviour from `config.json` |

## Status

- ✅ **Publisher** — production-ready against Ayrshare's stable `/post` API.
- 🧪 **Descript edit** — import/render against the beta API; the AI-agent edit
  step is best driven via the Descript MCP until the agent REST route is GA.
- Verified locally: `--dry-run` builds correct per-platform payloads with no
  network calls or keys.
