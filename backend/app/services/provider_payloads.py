from typing import Any


def _is_probable_video_url(url: str) -> bool:
    lowered = url.lower()
    return (
        lowered.startswith("http://")
        or lowered.startswith("https://")
        or lowered.startswith("asset://")
    ) and any(token in lowered for token in (".mp4", ".mov", ".m3u8", "video"))


def _is_probable_image_url(url: str) -> bool:
    lowered = url.lower()
    return (
        lowered.startswith("http://")
        or lowered.startswith("https://")
        or lowered.startswith("asset://")
    ) and any(token in lowered for token in (".png", ".jpg", ".jpeg", ".webp", "frame"))


def _deep_collect_strings(node: Any, out: list[str]) -> None:
    if isinstance(node, str):
        out.append(node)
        return
    if isinstance(node, dict):
        for value in node.values():
            _deep_collect_strings(value, out)
        return
    if isinstance(node, list):
        for item in node:
            _deep_collect_strings(item, out)


def extract_provider_artifacts(payload: dict[str, Any]) -> tuple[str | None, str | None, dict[str, Any], str | None]:
    video_url: str | None = None
    last_frame_url: str | None = None
    error_message: str | None = None

    prioritized_video_keys = ("video_url", "videoUrl", "result_url", "resultUrl", "output_url", "url")
    prioritized_frame_keys = ("last_frame_url", "lastFrameUrl", "frame_url", "frameUrl")
    error_keys = ("error", "error_message", "message", "msg", "reason")

    def scan_dict(d: dict[str, Any]) -> None:
        nonlocal video_url, last_frame_url, error_message
        for key, value in d.items():
            if isinstance(value, str):
                if not video_url and key in prioritized_video_keys and _is_probable_video_url(value):
                    video_url = value
                if not last_frame_url and key in prioritized_frame_keys and _is_probable_image_url(value):
                    last_frame_url = value
                if not error_message and key in error_keys and value and any(
                    t in key.lower() for t in ("error", "message", "reason", "msg")
                ):
                    error_message = value
            elif isinstance(value, dict):
                scan_dict(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        scan_dict(item)

    scan_dict(payload)

    # Fallback URL discovery across all string values.
    all_strings: list[str] = []
    _deep_collect_strings(payload, all_strings)
    if not video_url:
        for s in all_strings:
            if _is_probable_video_url(s):
                video_url = s
                break
    if not last_frame_url:
        for s in all_strings:
            if _is_probable_image_url(s):
                last_frame_url = s
                break

    metadata: dict[str, Any] = {}
    if isinstance(payload.get("data"), dict):
        metadata["data"] = payload["data"]
    if isinstance(payload.get("code"), int):
        metadata["code"] = payload["code"]
    if isinstance(payload.get("status"), str):
        metadata["status"] = payload["status"]

    return video_url, last_frame_url, metadata, error_message

