#!/usr/bin/env python3
"""Build an offline shot gallery with copied images, videos and Korean prompts."""
import argparse
import html
import json
import re
import shutil
import unicodedata
from pathlib import Path
from urllib.parse import quote, urlparse

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}
STATUSES = {"planned", "generated", "approved", "partial", "rejected"}
LABELS = {"planned": "계획", "generated": "생성·검수 전", "approved": "검수됨",
          "partial": "일부 구간만 사용", "rejected": "사용 불가"}

def esc(value):
    return html.escape(str(value), quote=True)

def safe_stem(name):
    value = re.sub(r"[^A-Za-z0-9가-힣_-]+", "_", unicodedata.normalize("NFC", name))
    return value[:50] or "asset"

def copy_asset(value, role, index, scene_id, base, output, missing):
    if not value:
        return None
    source = Path(value).expanduser()
    source = source if source.is_absolute() else base / source
    source = source.resolve()
    valid = VIDEO_EXT if role == "video" else IMAGE_EXT
    if not source.is_file() or source.suffix.lower() not in valid:
        missing.append({"role": role, "source": str(source), "reason": "missing_file_or_unsupported_type"})
        return None
    folder = "videos" if role == "video" else "images"
    name = scene_id + "_" + role + str(index).zfill(2) + "_" + safe_stem(source.stem) + source.suffix.lower()
    target = output / folder / name
    shutil.copy2(source, target)
    return target.relative_to(output).as_posix()

def thumbnail(path, label):
    if not path:
        return '<div class="empty">' + esc(label) + ' 없음</div>'
    href = quote(path, safe="/")
    return '<a href="' + href + '" target="_blank"><img loading="lazy" src="' + href + '" alt="' + esc(label) + '"></a>'

def prompt_box(scene_id, field, label, text):
    target = scene_id + "_" + field
    return '<div class="prompt"><div class="label">' + esc(label) + '<button data-copy="' + esc(target) + '">복사</button></div><textarea readonly id="' + esc(target) + '">' + esc(text) + '</textarea></div>'

def render(manifest):
    cards = []
    for scene in manifest["scenes"]:
        scene_id = scene["id"]
        refs = "".join(thumbnail(p, "참고 이미지") for p in scene["references"])
        video = ""
        if scene["video"]:
            video = '<video controls preload="metadata" src="' + quote(scene["video"], safe="/") + '"></video>'
        links = []
        for url in scene.get("source_urls", []):
            if urlparse(url).scheme in {"http", "https"}:
                links.append('<a target="_blank" rel="noreferrer" href="' + esc(url) + '">원작 근거</a>')
        missing = scene.get("missing_assets", [])
        warning = '<p class="warning">누락 파일: ' + esc(len(missing)) + '개</p>' if missing else ""
        searchable = " ".join(str(scene.get(k, "")) for k in ["id", "title", "note", "image_prompt", "motion_prompt"])
        cards.append('<article class="card" data-search="' + esc(searchable.lower()) + '"><h2>' +
                     esc(scene_id + " · " + scene.get("title", "")) + '</h2><span class="status">' +
                     esc(LABELS[scene["status"]]) + '</span>' + warning +
                     '<div class="media">' + thumbnail(scene["image"], "생성 시작 이미지") + video + '</div>' +
                     '<details><summary>참고 이미지 (' + str(len(scene["references"])) + ')</summary><div class="refs">' + refs + '</div></details>' +
                     prompt_box(scene_id, "image", "이미지 프롬프트", scene.get("image_prompt", "")) +
                     prompt_box(scene_id, "motion", "모션 프롬프트", scene.get("motion_prompt", "")) +
                     '<p>' + esc(scene.get("note", "")) + '</p><div class="links">' + " · ".join(links) + '</div></article>')
    title = manifest.get("project", "팬툰오프닝")
    header = '<header><h1>' + esc(title) + '</h1><p>' + esc(manifest.get("aspect_ratio", "16:9")) + ' · ' + esc(manifest.get("output_resolution", "1280x720")) + ' · ' + str(len(manifest["scenes"])) + '컷</p><input id="search" type="search" placeholder="컷·인물·프롬프트 검색"><p id="notice" aria-live="polite"></p><a href="manifest.json">자료 목록</a> · <a href="images/">전체 이미지 폴더</a></header>'
    css = """
body{margin:0;background:#101217;color:#eef0f4;font:15px/1.6 system-ui,sans-serif}
header{max-width:1160px;margin:auto;padding:28px 20px}h1{margin:0;font-size:28px}
#search{box-sizing:border-box;width:100%;padding:12px;margin:14px 0;background:#20252d;color:#fff;border:1px solid #687384;border-radius:8px}
main{max-width:1160px;margin:auto;padding:0 20px 30px;display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:18px}
.card{background:#1c2028;border:1px solid #343c49;border-radius:12px;padding:18px}h2{font-size:18px;margin:0 0 8px}
.status{color:#a7d1fe}.warning{color:#ffc273}.media img,.media video{width:100%;max-height:320px;object-fit:contain;background:#090a0d}
.media{margin:12px 0}.empty{border:1px dashed #647083;padding:36px;text-align:center;color:#aeb7c6}
.refs{display:flex;gap:8px;overflow:auto}.refs img{height:110px;max-width:210px;object-fit:contain}
summary{cursor:pointer;margin:10px 0}textarea{box-sizing:border-box;width:100%;height:150px;resize:vertical;background:#101217;color:#e4e7ee;border:1px solid #485468;border-radius:7px;padding:10px;font:inherit}
.label{display:flex;justify-content:space-between;align-items:center;margin:12px 0 5px}
button{border:0;border-radius:6px;padding:7px 12px;background:#b8d8fc;color:#142338;cursor:pointer}
a{color:#a7d1fe}#notice{min-height:24px}.card[hidden]{display:none}
"""
    js = """
const notice=document.getElementById('notice');
document.getElementById('search').addEventListener('input',function(e){
 const query=e.target.value.toLowerCase();
 document.querySelectorAll('.card').forEach(function(card){card.hidden=!card.dataset.search.includes(query);});
});
document.querySelectorAll('[data-copy]').forEach(function(button){
 button.addEventListener('click',async function(){
  const area=document.getElementById(button.dataset.copy);
  try{
   if(navigator.clipboard && window.isSecureContext){await navigator.clipboard.writeText(area.value);}
   else{area.focus();area.select();if(!document.execCommand('copy')){throw new Error('copy unavailable');}}
   notice.textContent='프롬프트를 복사했습니다.';
  }catch(e){area.focus();area.select();notice.textContent='복사할 내용을 선택했습니다. 직접 복사해 주세요.';}
 });
});
"""
    return '<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + esc(title) + '</title><style>' + css + '</style></head><body>' + header + '<main>' + "".join(cards) + '</main><script>' + js + '</script></body></html>'

def build(source_manifest, output):
    source_manifest = Path(source_manifest).expanduser().resolve()
    output = Path(output).expanduser().resolve()
    if output.exists():
        raise ValueError("Output directory already exists; use a new handoff folder")
    data = json.loads(source_manifest.read_text(encoding="utf-8"))
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("scenes must be a nonempty list")
    ids = set()
    for scene in scenes:
        scene_id = scene.get("id", "")
        if not isinstance(scene_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,47}", scene_id):
            raise ValueError("Invalid scene id: " + str(scene_id))
        if scene_id.casefold() in ids:
            raise ValueError("Duplicate scene id: " + scene_id)
        ids.add(scene_id.casefold())
        if scene.get("status", "planned") not in STATUSES:
            raise ValueError("Unknown scene status: " + str(scene.get("status")))
        if not isinstance(scene.get("references", []), list) or not all(isinstance(x, str) for x in scene.get("references", [])):
            raise ValueError("references must be a list of paths")
        for key in ["image", "video"]:
            if scene.get(key) is not None and not isinstance(scene[key], str):
                raise ValueError(key + " must be a path or null")
        if not isinstance(scene.get("source_urls", []), list) or not all(isinstance(x, str) for x in scene.get("source_urls", [])):
            raise ValueError("source_urls must be a list of strings")
        for key in ["title", "image_prompt", "motion_prompt", "note"]:
            if key in scene and not isinstance(scene[key], str):
                raise ValueError(key + " must be a string")
    for folder in ["images", "videos", "cuts"]:
        (output / folder).mkdir(parents=True, exist_ok=False)
    base = source_manifest.parent
    copied = []
    for original in scenes:
        scene = dict(original)
        scene_id = scene["id"]
        scene["status"] = scene.get("status", "planned")
        missing = []
        scene["references"] = [p for i, value in enumerate(original.get("references", []), 1)
                               for p in [copy_asset(value, "ref", i, scene_id, base, output, missing)] if p]
        scene["image"] = copy_asset(original.get("image"), "start", 1, scene_id, base, output, missing)
        scene["video"] = copy_asset(original.get("video"), "video", 1, scene_id, base, output, missing)
        scene["missing_assets"] = missing
        scene["original_asset_paths"] = {"references": original.get("references", []),
                                         "image": original.get("image"), "video": original.get("video")}
        cut = output / "cuts" / scene_id
        cut.mkdir()
        (cut / "image_prompt_ko.txt").write_text(str(scene.get("image_prompt", "")), encoding="utf-8")
        (cut / "motion_prompt_ko.txt").write_text(str(scene.get("motion_prompt", "")), encoding="utf-8")
        (cut / "scene.json").write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")
        copied.append(scene)
    data["scenes"] = copied
    data["package_type"] = "local_handoff"
    data["generated_by_this_script"] = False
    (output / "manifest.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "index.html").write_text(render(data), encoding="utf-8")
    return {"output": str(output), "index": str(output / "index.html"), "scenes": len(copied),
            "copied_images": len(list((output / "images").iterdir())),
            "copied_videos": len(list((output / "videos").iterdir())),
            "missing_assets": sum(len(s["missing_assets"]) for s in copied)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        result = build(args.manifest, args.out)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
