"""降落屏的 ADHD 舒缓音（D′，取代 v2.2 的 say 朗读）。

PRD §模块7：降落屏播放低刺激音效（loop），帮注意力从认知转移到身体锚点。
策略：assets/ 放 CC0 音频 → 优先用它；没放则用 numpy 合成**很安静的水滴声**兜底——
稀疏的水珠滴落（音高微微上扬的「叮」）落在近乎静默之上，几乎听不见的水面气息垫底。
跨平台、无依赖 macOS `say` / Win `System.Speech`，路演不失声。
（历史：曾用过双耳节拍 binaural，反馈太吵，改回更安静的水滴。）
"""
import io
import os
import wave

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
# 优先找文件；水滴主题放最前
FILE_CANDIDATES = ("landing.mp3", "drip.mp3", "water.mp3", "rain.mp3", "forest.mp3", "stream.mp3")


def find_file():
    for name in FILE_CANDIDATES:
        p = os.path.join(ASSETS, name)
        if os.path.exists(p):
            return p
    return None


def _one_drop(np, sample_rate, f0, decay):
    """一颗水珠：音高随时间微微上扬的阻尼正弦（水腔共鸣的「叮—」），加一丝二次谐波。"""
    n = int(decay * 4 * sample_rate)
    t = np.arange(n) / sample_rate
    freq = f0 * (1.0 + 0.18 * (1.0 - np.exp(-t / (decay * 0.5))))   # 收尾微微抬高音
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    env = np.exp(-t / decay)
    body = np.sin(phase) + 0.25 * np.sin(2 * phase)                 # 一点二次谐波更「水」
    return body * env


def synth_waterdrops_wav(duration_sec=60, sample_rate=22050, peak=0.24, seed=11):
    """合成「很安静的水滴」WAV（单声道）兜底，返回 bytes。

    稀疏水珠（每 ~2-4.5s 一颗，音高/衰减略随机）落在近乎静默之上，
    叠一层极轻的水面气息（重度低通的柔噪，~0.03）避免死寂。整体音量压得很低（peak≈0.24）。
    头尾淡入淡出 + 滴落不跨越循环边界 → loop 无缝、无咔哒。
    """
    import numpy as np

    n = int(duration_sec * sample_rate)
    out = np.zeros(n)
    rng = np.random.default_rng(seed)
    pos = 1.0
    while pos < duration_sec - 0.8:                                 # 留尾，不跨 loop 边界
        drop = _one_drop(np, sample_rate, f0=rng.uniform(620, 1020),
                         decay=rng.uniform(0.12, 0.22)) * rng.uniform(0.55, 1.0)
        i = int(pos * sample_rate)
        end = min(i + len(drop), n)
        out[i:end] += drop[:end - i]
        pos += rng.uniform(2.0, 4.5)                                # 稀疏间隔，安静
    # 极轻的水面气息（重度低通柔噪），避免完全死寂
    amb = rng.standard_normal(n)
    amb = np.convolve(amb, np.ones(48) / 48, mode="same")
    amb /= (np.max(np.abs(amb)) or 1.0)
    out = out + amb * 0.03
    m = np.max(np.abs(out)) or 1.0
    out = out / m * peak                                            # 整体压低 → 很安静
    fade = int(0.5 * sample_rate)
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


def get():
    """返回 (data_or_path, mime, source)。source ∈ {'file', 'synth'}。"""
    p = find_file()
    if p:
        ext = os.path.splitext(p)[1].lstrip(".").lower() or "mp3"
        return p, f"audio/{ext}", "file"
    return synth_waterdrops_wav(), "audio/wav", "synth"
