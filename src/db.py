"""最简单的本地存储：SQLite，一个文件。黑客松不要起数据库服务。

v2/V3.0 schema（对应现 pipeline 输出）：
- entries：每一夜的倾倒 + 整理结果（title/journal/insight/soothe/明日第一步/睡前落点…）
- threads：那一夜的六类线程（任务/情绪/灵感/担忧/回忆/小电影），供「似曾相识」召回（G3）
- ratings：⑥评分屏的反馈训练（E）——贴近度 / 哪部分最贴近 / 自由文本

注：v1 旧表 dumps/cards/feedback 已废弃（schema 不兼容），保留在旧 db 文件里不动；
本模块只用 entries/threads/ratings（新名字，避免与旧 feedback 表撞名）。
"""
import json
import os
import re
import sqlite3
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 项目根目录
# 默认本地 data/mistery.db；可用 MURMORA_DB 覆盖（部署/测试隔离用）
DB_PATH = os.environ.get("MURMORA_DB") or os.path.join(ROOT, "data", "mistery.db")

# 贴近度 → 分数（反馈训练用，便于后续按相关度学习）
CLOSENESS_SCORE = {"不像": 1, "一点": 2, "还行": 3, "挺像": 4, "完全是": 5}
# 召回时优先的线程类别（睡前真正放不下的多是这几类）
_RECALL_PRIORITY = {"担忧": 0, "情绪": 1, "回忆": 2}


def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS entries(
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at          TEXT,
                channel             TEXT,     -- sensory / rational
                raw_text            TEXT,
                title               TEXT,
                journal             TEXT,     -- ① 你说了什么
                insight             TEXT,     -- 那句「看见」
                soothe              TEXT,     -- ② 抚慰疗愈
                tomorrow_first_step TEXT,     -- ④ 明天只做一步
                closing             TEXT,     -- ⑤ 睡前落点
                closing_source      TEXT
            );
            CREATE TABLE IF NOT EXISTS threads(
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id  INTEGER,
                category  TEXT,               -- 任务/情绪/灵感/担忧/回忆/小电影
                label     TEXT,
                detail    TEXT
            );
            CREATE TABLE IF NOT EXISTS ratings(
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id    INTEGER,
                closeness   TEXT,             -- 不像/一点/还行/挺像/完全是
                score       INTEGER,          -- 1-5
                parts       TEXT,             -- JSON 数组：哪部分最贴近
                note        TEXT,             -- 自由文本
                created_at  TEXT
            );
            """
        )


def save_entry(raw_text, channel, result):
    """把一夜的倾倒 + 整理结果落库，返回 entry_id。线程同时写入 threads（供召回）。"""
    r = result or {}
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO entries(created_at,channel,raw_text,title,journal,insight,"
            "soothe,tomorrow_first_step,closing,closing_source) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                datetime.now().isoformat(timespec="minutes"),
                channel,
                raw_text,
                r.get("title", ""),
                r.get("journal", ""),
                r.get("insight", ""),
                r.get("soothe", ""),
                r.get("tomorrow_first_step", ""),
                r.get("closing", ""),
                r.get("closing_source", ""),
            ),
        )
        entry_id = cur.lastrowid
        rows = [
            (entry_id, t.get("category", ""), t.get("label", ""), t.get("detail", ""))
            for t in r.get("threads", [])
        ]
        if rows:
            c.executemany(
                "INSERT INTO threads(entry_id,category,label,detail) VALUES(?,?,?,?)", rows
            )
        return entry_id


def save_rating(entry_id, closeness, parts, note):
    """⑥评分屏「沉入池底」：贴近度 / 哪部分最贴近(列表) / 自由文本 → ratings。"""
    with _conn() as c:
        c.execute(
            "INSERT INTO ratings(entry_id,closeness,score,parts,note,created_at) "
            "VALUES(?,?,?,?,?,?)",
            (
                entry_id,
                closeness,
                CLOSENESS_SCORE.get(closeness),
                json.dumps(parts or [], ensure_ascii=False),
                note or "",
                datetime.now().isoformat(timespec="minutes"),
            ),
        )


def _tokens(label):
    """把线程标签拆成可匹配的关键词（如「汇报·妈妈」→ ['汇报','妈妈']），过滤过短词。
    无分隔符的长标签再补一个头两字（「播客选题」→ 也含「播客」），头词常是核心，误命中风险低。"""
    toks = set()
    for w in re.split(r"[·,，、/\\\s]+", label or ""):
        w = w.strip()
        if len(w) >= 2:
            toks.add(w)
            if len(w) >= 4:
                toks.add(w[:2])
    if toks:
        return list(toks)
    lab = (label or "").strip()
    return [lab] if len(lab) >= 2 else []


def recall_similar(raw_text, limit=3):
    """G3「似曾相识」：在今晚的倾倒里命中**过往线程**的关键词，召回最相关的几条做类比。

    简单可靠、零额外依赖：用过往线程的短标签（妈妈/汇报/播客…）在今晚原文里做子串匹配，
    优先担忧/情绪/回忆类，去重、按最近优先，返回带 days_ago 的 dict 列表。
    （embedding 召回是以后的事；黑客松先用关键词把「记得你」做出来。）
    """
    raw = raw_text or ""
    if not raw.strip():
        return []
    try:
        with _conn() as c:
            rows = c.execute(
                "SELECT t.category, t.label, t.detail, e.created_at "
                "FROM threads t JOIN entries e ON e.id = t.entry_id "
                "ORDER BY e.id DESC LIMIT 300"
            ).fetchall()
    except sqlite3.OperationalError:
        return []  # 表还没建好

    today = date.today()
    seen, cands = set(), []
    for r in rows:
        hit = next((w for w in _tokens(r["label"]) if w in raw), None)
        if not hit:
            continue
        key = (r["category"], r["label"])
        if key in seen:
            continue
        seen.add(key)
        try:
            days = (today - datetime.fromisoformat(r["created_at"]).date()).days
        except (ValueError, TypeError):
            days = None
        cands.append(
            {
                "category": r["category"],
                "label": r["label"],
                "detail": r["detail"],
                "created_at": r["created_at"],
                "days_ago": days,
                "hit": hit,
                "_prio": _RECALL_PRIORITY.get(r["category"], 9),
            }
        )
    cands.sort(key=lambda x: x["_prio"])
    return cands[:limit]


def last_night_count():
    """晨间层（F）以后用：昨夜放下了几件事。"""
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT COUNT(*) AS n FROM threads "
                "WHERE entry_id=(SELECT MAX(id) FROM entries)"
            ).fetchone()
            return row["n"] if row else 0
    except sqlite3.OperationalError:
        return 0
