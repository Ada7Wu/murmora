"""语音转写（C）：st.audio_input 录音 → faster-whisper 本地转写。

选型理由：零额外 key、离线、不耗 Claude token、隐私最好（睡前私密音频不出本机）。
代价：需 `pip install faster-whisper`，首次会下模型（中文用 small）。没装也不报错——
available() 返回 False，倾倒屏自动降级为只打字。
"""
import os
import tempfile

_model = None


def available():
    """faster-whisper 是否可用（没装就让 UI 优雅降级到打字）。"""
    try:
        import faster_whisper  # noqa: F401

        return True
    except Exception:
        return False


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        # medium：中文普通话准度明显好于 small（代价：~1.5GB、CPU 上慢 2-3 倍）。
        # 可用 WHISPER_MODEL 覆盖：small(更快更弱) / large-v3(最准最慢)。CPU + int8 省内存。
        size = os.environ.get("WHISPER_MODEL", "medium")
        _model = WhisperModel(size, device="cpu", compute_type="int8")
    return _model


def transcribe(audio_bytes):
    """audio_bytes：st.audio_input 返回对象的 .getvalue()（WAV）。返回转写文本（失败返回 ""）。"""
    path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            path = f.name
        # initial_prompt：把输出往「简体普通话」上拽，治 Whisper 中文爱出繁体/串味的老毛病
        segments, _info = _get_model().transcribe(
            path,
            language="zh",
            task="transcribe",              # 明确是转写，不是翻译成英文
            initial_prompt="以下是普通话的句子。",
            vad_filter=True,
        )
        return "".join(s.text for s in segments).strip()
    except Exception:
        return ""
    finally:
        if path:
            try:
                os.remove(path)
            except OSError:
                pass
