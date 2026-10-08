#!/usr/bin/env python3
"""Inventory local media without moving, editing or judging its creative quality."""
import argparse
import hashlib
import json
import shutil
import subprocess
import unicodedata
from pathlib import Path

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
EXTENSIONS = IMAGE_EXT | VIDEO_EXT | AUDIO_EXT

def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()

def ratio(value):
    try:
        if isinstance(value, str) and "/" in value:
            a, b = value.split("/", 1)
            return float(a) / float(b)
        return float(value) if value is not None else None
    except (ValueError, TypeError, ZeroDivisionError):
        return None

def probe_media(path, executable):
    if executable:
        proc = subprocess.run(
            [executable, "-v", "error", "-show_format", "-show_streams",
             "-of", "json", str(path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60
        )
        if proc.returncode:
            raise RuntimeError(proc.stderr.strip()[-400:] or "ffprobe failed")
        data = json.loads(proc.stdout)
        streams = data.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), {})
        audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
        return {
            "method": "ffprobe",
            "duration": ratio(data.get("format", {}).get("duration")),
            "width": video.get("width"), "height": video.get("height"),
            "fps": ratio(video.get("avg_frame_rate")),
            "frame_count_reported": ratio(video.get("nb_frames")),
            "video_codec": video.get("codec_name"), "audio_codec": audio.get("codec_name"),
            "sample_rate": ratio(audio.get("sample_rate")), "channels": audio.get("channels"),
            "stream_types": [s.get("codec_type") for s in streams]
        }
    try:
        import av
    except ImportError:
        raise RuntimeError("Neither ffprobe nor PyAV is available; media metadata not inspected")
    with av.open(str(path)) as container:
        videos = list(container.streams.video)
        audios = list(container.streams.audio)
        video = videos[0] if videos else None
        audio = audios[0] if audios else None
        duration = container.duration / 1e6 if container.duration is not None else None
        if duration is None:
            lengths = [float(s.duration * s.time_base) for s in container.streams
                       if s.duration is not None and s.time_base is not None]
            duration = max(lengths) if lengths else None
        return {
            "method": "PyAV", "duration": duration,
            "width": video.width if video else None, "height": video.height if video else None,
            "fps": ratio(video.average_rate) if video else None,
            "frame_count_reported": video.frames or None if video else None,
            "video_codec": video.codec_context.name if video else None,
            "audio_codec": audio.codec_context.name if audio else None,
            "sample_rate": audio.codec_context.sample_rate if audio else None,
            "channels": audio.codec_context.channels if audio else None,
            "stream_types": [s.type for s in container.streams]
        }

def inventory(roots, ffprobe=None):
    paths = {}
    for root in roots:
        root = Path(root).expanduser().resolve()
        if not root.exists():
            raise ValueError("Source does not exist: " + str(root))
        candidates = [root] if root.is_file() else root.rglob("*")
        for path in candidates:
            if path.is_file() and path.suffix.lower() in EXTENSIONS:
                paths[str(path.resolve())] = path.resolve()
    items, hashes = [], {}
    for path in sorted(paths.values(), key=lambda p: unicodedata.normalize("NFC", str(p))):
        kind = "image" if path.suffix.lower() in IMAGE_EXT else "video" if path.suffix.lower() in VIDEO_EXT else "audio"
        item = {"path": str(path), "display_name": unicodedata.normalize("NFC", path.name),
                "kind": kind, "bytes": path.stat().st_size, "visual_review": "not_performed",
                "metadata_inspected": False}
        try:
            item["sha256"] = digest(path)
            hashes.setdefault(item["sha256"], []).append(str(path))
            if kind == "image":
                from PIL import Image
                with Image.open(path) as image:
                    item["metadata"] = {"method": "Pillow", "width": image.width,
                                        "height": image.height, "mode": image.mode,
                                        "format": image.format}
            else:
                item["metadata"] = probe_media(path, ffprobe)
            item["metadata_inspected"] = True
        except Exception as exc:
            item["inspection_error"] = str(exc)
        items.append(item)
    return {"status": "inventory_only", "roots": [str(Path(r).expanduser().resolve()) for r in roots],
            "items": items, "count": len(items),
            "duplicate_groups": [v for v in hashes.values() if len(v) > 1],
            "inspection_error_count": sum("inspection_error" in x for x in items),
            "full_decode_performed": False, "canon_review_performed": False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+")
    parser.add_argument("--out", required=True)
    parser.add_argument("--ffprobe", help="Explicit ffprobe executable; otherwise use PATH or PyAV")
    args = parser.parse_args()
    output = Path(args.out).expanduser().resolve()
    if output.exists():
        parser.error("Output already exists; use a new inventory filename")
    try:
        result = inventory(args.roots, args.ffprobe or shutil.which("ffprobe"))
    except ValueError as exc:
        parser.error(str(exc))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"output": str(output), "files": result["count"],
                      "duplicate_groups": len(result["duplicate_groups"]),
                      "inspection_errors": result["inspection_error_count"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
