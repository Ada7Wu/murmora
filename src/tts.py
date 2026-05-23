"""降落语音（D）：用本机 macOS `say` 合成舒缓引导语（免 key、离线）。

跟 B 的免 key 思路一致：不调云 TTS、不耗 token。非 macOS / 无 `say` 时 available()=False，
降落屏自动退回纯文字 + 呼吸圈。合成结果按内容缓存，重复进降落屏不重复合成。
"""
import hashlib
import os
import shutil
import subprocess
import tempfile

_CACHE = {}
_VOICE = "__unset__"


def available():
    return shutil.which("say") is not None


def _voice():
    """优先中文女声（Tingting/Meijia/Sinji），找不到就用系统默认。"""
    global _VOICE
    if _VOICE != "__unset__":
        return _VOICE
    _VOICE = None
    try:
        out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, timeout=10).stdout
        for v in ("Tingting", "Meijia", "Sinji"):
            if v.lower() in out.lower():
                _VOICE = v
                break
    except Exception:
        pass
    return _VOICE


def synth(text, rate=145):
    """把引导语合成为 WAV bytes（缓存）。不可用/失败返回 None。
    rate 越小越慢越舒缓；text 里可用 `[[slnc 毫秒]]` 插入停顿。"""
    if not available():
        return None
    key = hashlib.md5(f"{rate}|{text}".encode()).hexdigest()
    if key in _CACHE:
        return _CACHE[key]
    out = os.path.join(tempfile.gettempdir(), f"murmora_tts_{key}.wav")
    cmd = ["say"]
    v = _voice()
    if v:
        cmd += ["-v", v]
    cmd += ["-r", str(rate), "-o", out, "--data-format=LEI16@22050", text]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        with open(out, "rb") as f:
            data = f.read()
        _CACHE[key] = data
        return data
    except Exception:
        return None
    finally:
        try:
            os.remove(out)
        except OSError:
            pass
