"""Murmora 真实管线（B）：一次结构化 Claude 调用，把睡前倾倒拆解归类 + 重述。

设计原则（省 token / 少往返）：
- 只用 **一次** messages.create —— 用 output_config.format 强约束 JSON，把"理解 + 六类归类 +
  第一人称重述 + 那句看见 + 明日第一步"一次拿全。
- 降落语音三段、呼吸节律、转场文案这些**固定脚本**不走 LLM（在 app.py 里硬编码）。
- system 提示词是稳定前缀 → 开 prompt caching（现长度未到阈值不会真命中，但不报错，不影响）。
没有 ANTHROPIC_API_KEY 时自动走 demo（池中之石示例），方便先看 UI。
"""
import json
import os
import shutil
import subprocess
import tempfile

MODEL = "claude-opus-4-7"
CATEGORIES = ["任务", "情绪", "灵感", "担忧", "回忆", "小电影"]

_client = None


def has_api_key():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _client_():
    global _client
    if _client is None:
        import anthropic  # 延迟导入：demo 模式无需安装

        _client = anthropic.Anthropic()
    return _client


def _system():
    path = os.path.join(os.path.dirname(__file__), "prompts", "murmora.txt")
    with open(path, encoding="utf-8") as f:
        return f.read()


# 结构化输出 schema（output_config.format 强约束；注意 additionalProperties 必须 False）
SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "threads": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": CATEGORIES},
                    "label": {"type": "string"},
                    "detail": {"type": "string"},
                },
                "required": ["category", "label", "detail"],
                "additionalProperties": False,
            },
        },
        "journal": {"type": "string"},
        "insight": {"type": "string"},
        "tomorrow_first_step": {"type": "string"},
    },
    "required": ["title", "threads", "journal", "insight", "tomorrow_first_step"],
    "additionalProperties": False,
}


def run(raw_text):
    """真实管线：一次结构化调用。返回 dict（结构见 SCHEMA）。"""
    resp = _client_().messages.create(
        model=MODEL,
        max_tokens=1500,
        system=[{"type": "text", "text": _system(), "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": raw_text}],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
    )
    text = next(b.text for b in resp.content if b.type == "text")
    return json.loads(text)


def cli_available():
    """本机是否装了 Claude Code CLI（用它复用订阅 OAuth，免 API key）。"""
    return shutil.which("claude") is not None


def run_cli(raw_text):
    """复用本机 Claude Code 的登录（订阅 OAuth，无需 API key）：调 `claude -p` 一次性出结构化结果。

    关键点（否则会跑偏成"编码 agent"）：
    - `--system-prompt` 完全**替换** Claude Code 默认人格为 Murmora（不能用 --append-system-prompt）。
    - `--tools ""` 禁用所有工具 → 不会去读写文件，单轮直接生成，更快。
    - **不要用 --bare**：它会禁用 OAuth/keychain、强制用 API key，正好与"复用订阅登录"相反。
    - 在临时空目录里跑，避免本仓库的 CLAUDE.md 被自动加载进上下文。
    仅适用于本机装了并登录了 Claude Code 的场景（部署到 Streamlit Cloud 不可用）。
    """
    cmd = [
        "claude", "-p",
        "--output-format", "json",
        "--model", "opus",
        "--system-prompt", _system(),
        "--tools", "",
        "--json-schema", json.dumps(SCHEMA, ensure_ascii=False),
        raw_text,
    ]
    with tempfile.TemporaryDirectory() as cwd:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=180)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip()[:300] or "claude CLI 调用失败")
    env = json.loads(proc.stdout)
    out = env.get("structured_output")
    if not out and env.get("result"):       # 兜底：偶尔结构化结果落在 result 文本里
        out = json.loads(env["result"])
    if not out:
        raise RuntimeError("claude CLI 未返回 structured_output")
    return out


def run_demo(raw_text=None):
    """无 key 时的「池中之石」示例，让八屏直接可演。"""
    return {
        "title": "池中之石",
        "threads": [
            {"category": "任务", "label": "汇报 · PPT", "detail": "明天有汇报，PPT 还没写完"},
            {"category": "情绪", "label": "愧疚 · 妈妈", "detail": "和妈妈视频，她又说我太瘦"},
            {"category": "灵感", "label": "播客选题", "detail": "突然想到一个播客选题"},
            {"category": "担忧", "label": "经期前夕", "detail": "经期快到了，怕状态更差"},
            {"category": "小电影", "label": "飞行幻想", "detail": "脑子里又开始放飞行的画面"},
        ],
        "journal": (
            "今晚水面起了好几道波纹——疲惫、牵挂、还有一点微亮。你说起了明天的汇报，"
            "也说起了和妈妈那通总让你心里发紧的电话，还有一个突然冒出来的、关于播客的灵感。"
            "听起来，今晚真正落不下去的，不是 PPT，是妈妈那通电话。"
        ),
        "insight": "今晚真正落不下去的，不是 PPT，是妈妈那通电话。",
        "tomorrow_first_step": "明早醒来，先只打开那份 PPT，写一行字就好。",
    }


def _demo_with_error(raw_text, err):
    fallback = run_demo(raw_text)
    fallback["_error"] = str(err)
    return fallback


def backend():
    """当前会用哪条后端：api（有 key）/ cli（复用 Claude Code 登录）/ demo（都没有）。"""
    if has_api_key():
        return "api"
    if cli_available():
        return "cli"
    return "demo"


def generate(raw_text):
    """app 调用入口。优先级：① 有 ANTHROPIC_API_KEY → 直连 API（最快、可部署）；
    ② 否则本机有 Claude Code → 复用其订阅 OAuth（`claude -p`，免 key，仅本地）；③ 都没有 → demo。
    任一后端出错都回落 demo，绝不让演示崩。"""
    b = backend()
    if b == "api":
        try:
            return run(raw_text)
        except Exception as e:
            return _demo_with_error(raw_text, e)
    if b == "cli":
        try:
            return run_cli(raw_text)
        except Exception as e:
            return _demo_with_error(raw_text, e)
    return run_demo(raw_text)
