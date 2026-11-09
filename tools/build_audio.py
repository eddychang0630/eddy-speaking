"""產生口說 App 的 Kokoro 自然語音 MP3。

讀 lessons/ 裡所有課程，把 App 會唸的每一句（chunk、例句、問答、對話、跟讀、聽力題）
用 Kokoro 產生成 audio/<hash>.mp3，並寫出 audio/manifest.js 給 App 查表。
已經存在的音檔會跳過，所以新增一課只會產生新的句子。

用法（Windows PowerShell，在 eddy-speaking 資料夾裡）：
    & "$env:USERPROFILE\\Desktop\\English class 整理重點\\.models\\kokoro\\venv\\Scripts\\python.exe" tools\\build_audio.py
    加上 --push 會在產生完後自動 git add / commit / pull --rebase / push。

需要：Kokoro（和單字 App 共用的那一份）、ffmpeg。
"""

import argparse
import ctypes
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
LESSON_DIR = APP_DIR / "lessons"
AUDIO_DIR = APP_DIR / "audio"
VOICE_A = "am_puck"   # 主要聲音（和單字、句子 App 相同）
VOICE_B = "af_heart"  # 對話裡 B 角色的聲音
TEST_SENTENCE = "Do you wanna grab coffee later?"  # 設定裡「試聽」用
DEFAULT_KOKORO = Path.home() / "Desktop/English class 整理重點/.models/kokoro"


# ── 文字規則：必須和 index.html 的 normText() / core() 完全一致 ──
def norm_text(text):
    return re.sub(r"\s*/\s*", ", ", str(text)).strip()


def core(s):
    s = re.sub(r"\(.*?\)", "", str(s or ""))
    s = re.sub(r"\+\s*\[.*?\]", "", s)
    s = s.replace("...", "").replace("…", "")
    s = re.sub(r"[?.!]", "", s)
    return s.strip()


def clip_hash(voice, text):
    return hashlib.sha256(f"{voice}\0{text}".encode("utf-8")).hexdigest()[:20]


# ── 讀課程檔：registerLesson(<JSON>); ──
def load_lessons():
    files = re.findall(r"['\"]([^'\"]+\.js)['\"]", (LESSON_DIR / "index.js").read_text(encoding="utf-8"))
    lessons = []
    for name in files:
        src = (LESSON_DIR / name).read_text(encoding="utf-8")
        start = src.index("registerLesson(") + len("registerLesson(")
        end = src.rindex(")")
        try:
            lessons.append(json.loads(src[start:end]))
        except json.JSONDecodeError as e:
            raise SystemExit(f"{name} 不是標準 JSON（registerLesson 裡要用雙引號、不能有註解或結尾逗號）：{e}")
    return lessons


def collect_texts(lessons):
    a, b = {TEST_SENTENCE}, set()
    for L in lessons:
        video = L.get("type") == "video"
        for c in L.get("cards", []):
            if video:
                written = c.get("written", "")
                a.add(core(written) + ("?" if "?" in written else "."))
                a.update(e["en"] for e in c.get("examples", []))
            else:
                a.add(c["question"])
                a.update(x["en"] for x in c.get("answers", []))
        dialogue = L.get("dialogue")
        if dialogue:
            for line in dialogue.get("lines", []):
                (b if line.get("speaker") == "B" else a).add(line["en"])
        elif not video:  # App 自動產生的問答對練：A 問、B 用第一個回答
            for c in L.get("cards", []):
                a.add(c["question"])
                if c.get("answers"):
                    b.add(c["answers"][0]["en"])
        for s in (L.get("shadow") or {}).get("sentences", []):
            a.add(s["en"])
        for q in L.get("challenges", []) or []:
            a.add(q["sentence"])
    clean = lambda xs: sorted({norm_text(x) for x in xs if str(x).strip()})
    return {VOICE_A: clean(a), VOICE_B: clean(b)}


# ── Kokoro 渲染（和 eddy-flashcards/audio_assets.py 同一套設定） ──
def _short_path(path):
    path = str(Path(path).resolve())
    if os.name != "nt":
        return path
    buffer = ctypes.create_unicode_buffer(32768)
    length = ctypes.windll.kernel32.GetShortPathNameW(path, buffer, len(buffer))
    if not length or length >= len(buffer):
        raise RuntimeError(f"Windows short path unavailable for eSpeak data: {path}")
    return buffer.value.replace("\\", "/")


def make_renderer(kokoro_home):
    if kokoro_home is None:
        # GitHub Actions / 一般 pip 安裝：用 pip 裝好的 kokoro，模型從 Hugging Face 下載
        pass
    else:
        kokoro_home = Path(kokoro_home)
        data_path = kokoro_home / "venv/Lib/site-packages/espeakng_loader/espeak-ng-data"
        if not data_path.is_dir():
            raise FileNotFoundError(f"找不到 eSpeak 資料：{data_path}（用 --kokoro-home 指定 Kokoro 資料夾）")
        os.environ["HF_HOME"] = str(kokoro_home / "hf-cache")
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["ESPEAK_DATA_PATH"] = _short_path(data_path)

    import torch
    from kokoro import KPipeline

    if kokoro_home is not None:
        import misaki.espeak  # noqa: F401
        from phonemizer.backend.espeak.wrapper import EspeakWrapper
        EspeakWrapper.set_data_path(None)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading Kokoro on {device}", flush=True)
    pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M", device=device)

    def render_one(text, voice, target):
        target = Path(target)
        temporary = target.with_suffix(".tmp.mp3")
        try:
            chunks = [r.audio for r in pipeline(text, voice=voice)]
            if not chunks:
                raise RuntimeError(f"Kokoro 沒有產生聲音：{text}")
            samples = torch.cat(chunks).detach().cpu().numpy().astype("float32")
            subprocess.run(
                [os.environ.get("FFMPEG_BIN", "ffmpeg"), "-hide_banner", "-loglevel", "error", "-y",
                 "-f", "f32le", "-ar", "24000", "-ac", "1", "-i", "pipe:0",
                 "-codec:a", "libmp3lame", "-q:a", "4", "-f", "mp3", str(temporary)],
                input=samples.tobytes(), check=True,
            )
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)

    return render_one


def write_manifest(texts):
    clips = {voice: {t: clip_hash(voice, t) for t in items} for voice, items in texts.items()}
    body = json.dumps(clips, ensure_ascii=False, indent=1, sort_keys=True)
    (AUDIO_DIR / "manifest.js").write_text(
        "/* 由 tools/build_audio.py 產生，請勿手動修改 */\nwindow.AUDIO_CLIPS = " + body + ";\n", encoding="utf-8")
    return clips


def git_push(count):
    run = lambda *a: subprocess.run(["git", *a], cwd=APP_DIR, check=True)
    run("add", "--", "audio")
    if subprocess.run(["git", "diff", "--cached", "--quiet", "--", "audio"], cwd=APP_DIR).returncode == 0:
        print("音檔沒有變更，不需要 push")
        return
    run("commit", "-m", f"Update Kokoro audio ({count} new clips)", "--", "audio")
    run("pull", "--rebase", "--autostash")
    run("push")
    print("已推送到 GitHub，Pages 部署完成後按 App 的 ↻ 就會用新音檔")


def main(argv=None):
    p = argparse.ArgumentParser(description="產生口說 App 的 Kokoro MP3")
    p.add_argument("--kokoro-home", default=os.environ.get("KOKORO_HOME", str(DEFAULT_KOKORO)),
                   help="本機 Kokoro 資料夾；GitHub Actions 用 none（直接用 pip 安裝的 kokoro）")
    p.add_argument("--push", action="store_true", help="產生完後 git commit + push")
    p.add_argument("--keep-orphans", action="store_true", help="保留已經沒有用到的舊音檔")
    args = p.parse_args(argv)

    AUDIO_DIR.mkdir(exist_ok=True)
    texts = collect_texts(load_lessons())
    clips = write_manifest(texts)
    pending = [(v, t, h) for v, m in clips.items() for t, h in m.items()
               if not (AUDIO_DIR / f"{h}.mp3").is_file() or (AUDIO_DIR / f"{h}.mp3").stat().st_size == 0]
    total = sum(len(m) for m in clips.values())
    print(f"需要 {total} 段音檔，其中 {len(pending)} 段要產生", flush=True)

    if pending:
        render = make_renderer(None if str(args.kokoro_home).lower() == "none" else Path(args.kokoro_home))
        for i, (voice, text, h) in enumerate(pending, 1):
            render(text, voice, AUDIO_DIR / f"{h}.mp3")
            if i % 20 == 0 or i == len(pending):
                print(f"  已產生 {i}/{len(pending)}", flush=True)

    used = {f"{h}.mp3" for m in clips.values() for h in m.values()}
    if not args.keep_orphans:
        for f in AUDIO_DIR.glob("*.mp3"):
            if f.name not in used:
                f.unlink()
    missing = [n for n in used if not (AUDIO_DIR / n).is_file() or (AUDIO_DIR / n).stat().st_size == 0]
    if missing:
        raise SystemExit(f"有 {len(missing)} 段音檔沒有產生成功，例如 {missing[0]}")
    print("全部音檔檢查完成 ✅")
    if args.push:
        git_push(len(pending))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
