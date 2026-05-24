"""降落屏的 ADHD 舒缓音（D′，取代 v2.2 的 say 朗读）。

PRD §模块7：降落屏播放低刺激音效（loop），帮注意力从认知转移到身体锚点。
策略：assets/ 放 CC0 音频 → 优先用它；没放则用 numpy 合成**很安静的颂钵 + 稀疏水滴**兜底——
间隔很久才轻轻一声颂钵（长长的共鸣尾音，带微微的「嗡—」beating），其间偶尔一两滴水珠，
大段近乎静默。整体音量压得很低。跨平台、无依赖、路演不失声。
（历史：双耳节拍 binaural、稳定水流 shower 都反馈太吵；改成更安静、更稀疏的颂钵+水滴。）
"""
import glob
import io
import os
import wave

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
# 找文件的优先「名字前缀」（landing 最先）与可接受的音频扩展名（浏览器/st.audio 都支持）
FILE_STEMS = ("landing", "bowl", "drip", "water", "rain", "forest", "stream")
AUDIO_EXTS = (".ogg", ".mp3", ".m4a", ".wav", ".opus", ".flac")


def find_file():
    for stem in FILE_STEMS:
        for p in sorted(glob.glob(os.path.join(ASSETS, stem + ".*"))):
            if p.lower().endswith(AUDIO_EXTS):
                return p
    return None


def _bowl_strike(np, sr, f0, dur):
    """一声颂钵：几个非谐波分音各自指数衰减（低分音尾音最长），每个分音轻微失谐 → 缓慢的「嗡—」shimmer。"""
    n = int(dur * sr)
    t = np.arange(n) / sr
    # (频率比, 相对幅度, 衰减系数·秒, 失谐 beat Hz)；比例取自真实颂钵的非谐波分音
    parts = [(1.00, 1.00, dur * 0.95, 0.6),
             (2.00, 0.55, dur * 0.70, 1.0),
             (2.69, 0.34, dur * 0.50, 1.3),
             (3.43, 0.20, dur * 0.36, 1.7),
             (4.18, 0.11, dur * 0.26, 2.1)]
    sig = np.zeros(n)
    for ratio, amp, dec, beat in parts:
        f = f0 * ratio
        env = np.exp(-t / (dec * 0.5))
        s = 0.5 * (np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * (f + beat) * t))
        sig += amp * env * s
    atk = int(0.004 * sr)                                   # 4ms 软起音，去敲击咔哒
    sig[:atk] *= np.linspace(0, 1, atk)
    return sig


def _one_drop(np, sr, f0, decay):
    """一颗水珠：音高随时间微微上扬的阻尼正弦（水腔共鸣的「叮—」）+ 一点二次谐波。"""
    n = int(decay * 4 * sr)
    t = np.arange(n) / sr
    freq = f0 * (1.0 + 0.18 * (1.0 - np.exp(-t / (decay * 0.5))))
    phase = 2 * np.pi * np.cumsum(freq) / sr
    env = np.exp(-t / decay)
    return (np.sin(phase) + 0.25 * np.sin(2 * phase)) * env


def synth_singingbowl_wav(duration_sec=90, sample_rate=22050, peak=0.18, seed=21):
    """合成「很安静的颂钵 + 稀疏水滴」WAV（单声道）兜底，返回 bytes。

    颂钵每 ~16-24s 一声（长共鸣尾音，音高略随机），其间偶尔很轻的一滴水珠（~10-18s），
    大段近乎静默 + 极faint 的气息垫底。整体压到很低（peak≈0.18）；头尾淡入淡出 → loop 无缝。
    """
    import numpy as np

    n = int(duration_sec * sample_rate)
    out = np.zeros(n)
    rng = np.random.default_rng(seed)

    # 颂钵：稀疏、长尾
    pos = rng.uniform(0.5, 2.5)
    while pos < duration_sec - 1.5:
        bowl = _bowl_strike(np, sample_rate, f0=rng.uniform(285, 360),
                            dur=rng.uniform(9.0, 12.0)) * rng.uniform(0.8, 1.0)
        i = int(pos * sample_rate)
        end = min(i + len(bowl), n)
        out[i:end] += bowl[:end - i]
        pos += rng.uniform(16.0, 24.0)

    # 水滴：更稀疏、更轻（颂钵之间的小点缀）
    pos = rng.uniform(4.0, 9.0)
    while pos < duration_sec - 1.0:
        drop = _one_drop(np, sample_rate, f0=rng.uniform(620, 1000),
                         decay=rng.uniform(0.12, 0.2)) * rng.uniform(0.18, 0.34)
        i = int(pos * sample_rate)
        end = min(i + len(drop), n)
        out[i:end] += drop[:end - i]
        pos += rng.uniform(10.0, 18.0)

    # 极轻气息垫底，避免数字死寂
    amb = rng.standard_normal(n)
    amb = np.convolve(amb, np.ones(64) / 64, mode="same")
    amb /= (np.max(np.abs(amb)) or 1.0)
    out = out + amb * 0.012

    out = out / (np.max(np.abs(out)) or 1.0) * peak        # 整体压低 → 很安静
    fade = int(1.0 * sample_rate)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    pcm = (out * 32767).astype("int16")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


# 扩展名 → 浏览器/st.audio 用的标准 MIME（mp3 必须是 audio/mpeg 才稳）
_MIME = {"mp3": "audio/mpeg", "m4a": "audio/mp4", "opus": "audio/ogg",
         "ogg": "audio/ogg", "wav": "audio/wav", "flac": "audio/flac"}


def get():
    """返回 (data_or_path, mime, source)。source ∈ {'file', 'synth'}。"""
    p = find_file()
    if p:
        ext = os.path.splitext(p)[1].lstrip(".").lower()
        return p, _MIME.get(ext, "audio/mpeg"), "file"
    return synth_singingbowl_wav(), "audio/wav", "synth"
