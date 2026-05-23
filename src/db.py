"""最简单的本地存储：SQLite，一个文件。黑客松不要起数据库服务。"""
import os
import sqlite3
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 项目根目录
DB_PATH = os.path.join(ROOT, "data", "mistery.db")


def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS dumps(
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                raw_text   TEXT,
                mood       TEXT,
                winddown   TEXT,
                audio      TEXT
            );
            CREATE TABLE IF NOT EXISTS cards(
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                dump_id  INTEGER,
                type     TEXT,            -- todo / worry / idea
                content  TEXT,
                reframe  TEXT,            -- 仅 worry 有：安抚文案
                resolved INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS feedback(
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                dump_id    INTEGER,
                slept_ok   INTEGER,
                note       TEXT,
                created_at TEXT
            );
            """
        )


def save(raw_text, result):
    """把一次倒念 + AI 结果落库，返回 dump_id。"""
    p = result["parsed"]
    reframe_map = {r.get("worry"): r.get("reframe") for r in result.get("reframes", [])}
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO dumps(created_at,raw_text,mood,winddown,audio) VALUES(?,?,?,?,?)",
            (
                datetime.now().isoformat(timespec="minutes"),
                raw_text,
                p.get("mood", ""),
                result.get("winddown", ""),
                result.get("audio", "none"),
            ),
        )
        dump_id = cur.lastrowid
        rows = []
        for t in p.get("todos", []):
            rows.append((dump_id, "todo", t, None))
        for w in p.get("worries", []):
            rows.append((dump_id, "worry", w, reframe_map.get(w)))
        for i in p.get("ideas", []):
            rows.append((dump_id, "idea", i, None))
        c.executemany(
            "INSERT INTO cards(dump_id,type,content,reframe) VALUES(?,?,?,?)", rows
        )
        return dump_id


def past_worries(limit=20):
    """给「安抚者」用：唤起以往的担心，做个性化引用。"""
    with _conn() as c:
        rows = c.execute(
            "SELECT content FROM cards WHERE type='worry' ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [r["content"] for r in rows]


def last_night_count():
    """首页那句「昨晚你放下了 N 件事」。"""
    with _conn() as c:
        row = c.execute(
            "SELECT COUNT(*) AS n FROM cards WHERE dump_id=(SELECT MAX(id) FROM dumps)"
        ).fetchone()
        return row["n"] if row else 0
