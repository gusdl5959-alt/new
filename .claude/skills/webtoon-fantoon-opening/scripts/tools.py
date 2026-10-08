"""Shared helpers: locate ffmpeg/ffprobe and probe media files."""
import glob, json, os, re, shutil, subprocess


def _candidates(name):
    c = [shutil.which(name), f"/opt/homebrew/bin/{name}", f"/usr/local/bin/{name}"]
    c += glob.glob(os.path.expanduser(f"~/Documents/**/bin/{name}"), recursive=True)[:5]
    return [p for p in c if p and os.path.exists(p)]


def ffmpeg():
    env = os.environ.get("OPKIT_FFMPEG")
    if env and os.path.exists(env):
        return env
    c = _candidates("ffmpeg")
    if c:
        return c[0]
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        raise SystemExit("ffmpeg not found. Install it (brew install ffmpeg) or set OPKIT_FFMPEG=/path/to/ffmpeg")


def ffprobe():
    env = os.environ.get("OPKIT_FFPROBE")
    if env and os.path.exists(env):
        return env
    c = _candidates("ffprobe")
    return c[0] if c else None


def probe(path):
    """returns dict(dur, w, h, fps) — works with ffprobe or ffmpeg alone"""
    fp = ffprobe()
    if fp:
        out = subprocess.run([fp, "-v", "error", "-select_streams", "v:0", "-show_entries",
                              "stream=width,height,r_frame_rate:format=duration", "-of", "json", path],
                             capture_output=True, text=True).stdout
        j = json.loads(out or "{}")
        d = float(j.get("format", {}).get("duration", 0) or 0)
        st = (j.get("streams") or [{}])[0]
        num, _, den = (st.get("r_frame_rate") or "0/1").partition("/")
        fps = float(num) / float(den or 1) if float(den or 1) else 0.0
        return dict(dur=d, w=st.get("width", 0), h=st.get("height", 0), fps=fps)
    err = subprocess.run([ffmpeg(), "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    d = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0
    v = re.search(r"Video:.*?(\d{2,5})x(\d{2,5}).*?([\d.]+) fps", err)
    return dict(dur=d, w=int(v.group(1)) if v else 0, h=int(v.group(2)) if v else 0, fps=float(v.group(3)) if v else 0.0)
