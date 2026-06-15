"""Descript editing step: import a raw video, let Descript's AI edit it, render.

Status note — read this:
  Descript's REST API is in beta. The two paths to drive an edit are:

  1. THE MCP (verified, recommended): the Descript MCP server exposes
     `prompt_project_agent` (natural-language editing) and `publish_project`
     (render to a shareable/downloadable URL). When this pipeline is run by an
     agent that has the Descript MCP connected, prefer driving those tools — they
     are the same ones used and tested interactively.

  2. THIS MODULE (beta REST): a thin client over the documented beta endpoints
     for headless/cron use without an MCP host. Base URL and the import path are
     documented; the publish job path may shift while the API is in beta, so it's
     overridable via `publish_path`. Auth is a Bearer personal token scoped to a
     Drive (Settings -> API Tokens in Descript).

  Docs: https://help.descript.com/hc/en-us/articles/43370311322509-Descript-API
"""
from __future__ import annotations

import time
from typing import Any

import requests

BASE_URL = "https://api.descript.com/v1"


class DescriptError(RuntimeError):
    pass


class DescriptClient:
    def __init__(self, token: str, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    # --- low-level helpers ---------------------------------------------------
    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        resp = self.session.post(f"{self.base_url}{path}", json=payload, timeout=120)
        if resp.status_code >= 400:
            raise DescriptError(f"POST {path} -> {resp.status_code}: {resp.text[:500]}")
        return resp.json()

    def _wait_for_job(self, job_id: str, poll_every: float = 5.0, timeout: float = 1800) -> dict[str, Any]:
        """Poll a job until it completes. Returns the job's result payload."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = self.session.get(f"{self.base_url}/jobs/{job_id}", timeout=60)
            if resp.status_code >= 400:
                raise DescriptError(f"GET /jobs/{job_id} -> {resp.status_code}: {resp.text[:300]}")
            job = resp.json()
            status = (job.get("status") or job.get("state") or "").lower()
            if status in {"complete", "completed", "succeeded", "success", "done"}:
                return job
            if status in {"failed", "error", "cancelled", "canceled"}:
                raise DescriptError(f"Job {job_id} ended as {status}: {job}")
            time.sleep(poll_every)
        raise DescriptError(f"Job {job_id} timed out after {timeout}s")

    # --- pipeline steps ------------------------------------------------------
    def import_from_url(self, video_url: str, project_name: str) -> str:
        """Import a video by URL into a new project. Returns project_id."""
        job = self._post(
            "/jobs/import/project_media",
            {"url": video_url, "name": project_name, "add_to_composition": True},
        )
        result = self._wait_for_job(job["id"])
        project_id = result.get("project_id") or result.get("result", {}).get("project_id")
        if not project_id:
            raise DescriptError(f"Import finished but no project_id in result: {result}")
        return project_id

    def publish(
        self,
        project_id: str,
        resolution: str = "1080p",
        access_level: str = "unlisted",
        publish_path: str = "/jobs/publish",
    ) -> dict[str, str]:
        """Render + publish a project. Returns {'share_url', 'download_url'}.

        `publish_path` is overridable because the publish job route is the part
        of the beta API most likely to change.
        """
        job = self._post(
            publish_path,
            {
                "project_id": project_id,
                "media_type": "Video",
                "resolution": resolution,
                "access_level": access_level,
            },
        )
        result = self._wait_for_job(job["id"])
        payload = result.get("result", result)
        share_url = payload.get("share_url")
        download_url = payload.get("download_url")
        if not (share_url or download_url):
            raise DescriptError(f"Publish finished but no URLs in result: {result}")
        return {"share_url": share_url or "", "download_url": download_url or ""}


def edit_and_render(
    token: str,
    video_url: str,
    project_name: str,
    resolution: str = "1080p",
) -> str:
    """Import -> publish, returning a public URL to the rendered video.

    NOTE: the natural-language EDIT step (remove filler words, add captions,
    tighten intro) is performed by Descript's AI agent. Via REST that requires
    the agent endpoint, which is only partially documented in beta — drive it
    through the Descript MCP's `prompt_project_agent` for now. This helper covers
    the reliable import + render bookends; wire the agent call in between once
    your account's agent endpoint is confirmed.
    """
    client = DescriptClient(token)
    project_id = client.import_from_url(video_url, project_name)
    urls = client.publish(project_id, resolution=resolution)
    # Prefer the time-limited download URL (direct MP4) so the publisher can
    # hand a real media file to each platform; fall back to the share URL.
    return urls["download_url"] or urls["share_url"]
