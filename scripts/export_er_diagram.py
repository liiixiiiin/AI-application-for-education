"""Export an ER diagram from `backend/app/db.py`.

Reads the `CREATE TABLE` statements in `init_db()` and generates:
  - `data/er-diagram/schema.sql`  : the raw extracted SQL (for inspection)
  - `data/er-diagram/schema.dbml` : dbdiagram.io 兼容的 DBML
  - `data/er-diagram/schema.mmd`  : Mermaid erDiagram (markdown 可直接预览)
  - `data/er-diagram/schema.dot`  : Graphviz DOT
  - `data/er-diagram/er.png`      : 渲染好的 PNG (优先 kroki.io，
                                     回退到本地 `dot`，再回退到 `mmdc`)
  - `data/er-diagram/er.svg`      : SVG 版（同上策略）

Usage::

    python scripts/export_er_diagram.py
"""

from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import zlib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PY = ROOT / "backend" / "app" / "db.py"
OUT_DIR = ROOT / "data" / "er-diagram"

# =====================================================================
# 1. Parse `db.py` to extract CREATE TABLE statements
# =====================================================================


@dataclass
class Column:
    name: str
    type: str
    pk: bool = False
    not_null: bool = False
    unique: bool = False
    default: str | None = None
    note: str | None = None


@dataclass
class ForeignKey:
    column: str
    ref_table: str
    ref_column: str


@dataclass
class Table:
    name: str
    columns: list[Column] = field(default_factory=list)
    foreign_keys: list[ForeignKey] = field(default_factory=list)
    unique_groups: list[list[str]] = field(default_factory=list)


# Friendly Chinese descriptions for the 8 known tables in this project.
TABLE_NOTES = {
    "users": "用户账号 / 三角色（teacher / student / admin）",
    "sessions": "登录会话 / token 管理",
    "courses": "课程信息 / 基本元数据",
    "knowledge_points": "课程知识点（自动 + 手动）",
    "conversations": "RAG 多轮对话会话",
    "messages": "对话消息（含引用 JSON）",
    "knowledge_mastery": "EMA 知识掌握度（知识追踪 ⭐）",
    "exercise_attempts": "学生作答记录（数据闭环 ⭐）",
}


def parse_db_py(path: Path) -> list[Table]:
    """Pull every `CREATE TABLE ... ( ... )` block out of db.py."""
    src = path.read_text(encoding="utf-8")

    # Each CREATE TABLE statement lives inside a Python triple-quoted string.
    pattern = re.compile(
        r"CREATE TABLE IF NOT EXISTS\s+(\w+)\s*\((.*?)\)\s*\"\"\"",
        re.DOTALL,
    )

    tables: list[Table] = []
    for m in pattern.finditer(src):
        name = m.group(1)
        body = m.group(2)
        tables.append(_parse_table_body(name, body))
    return tables


def _split_top_level(body: str) -> list[str]:
    """Split a CREATE TABLE body on top-level commas (ignores commas inside `()`)."""
    parts: list[str] = []
    depth = 0
    buf: list[str] = []
    for ch in body:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth -= 1
            buf.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return [p for p in parts if p]


def _parse_table_body(name: str, body: str) -> Table:
    table = Table(name=name)

    for piece in _split_top_level(body):
        upper = piece.upper().strip()

        # FOREIGN KEY (col) REFERENCES other (col)
        m_fk = re.match(
            r"FOREIGN KEY\s*\(\s*(\w+)\s*\)\s*REFERENCES\s+(\w+)\s*\(\s*(\w+)\s*\)",
            piece,
            re.IGNORECASE,
        )
        if m_fk:
            table.foreign_keys.append(
                ForeignKey(m_fk.group(1), m_fk.group(2), m_fk.group(3))
            )
            continue

        # UNIQUE (col1, col2, ...)
        m_uniq = re.match(r"UNIQUE\s*\(([^)]+)\)", piece, re.IGNORECASE)
        if m_uniq and not upper.startswith(("PRIMARY", "FOREIGN")):
            cols = [c.strip() for c in m_uniq.group(1).split(",")]
            table.unique_groups.append(cols)
            continue

        # PRIMARY KEY (col, col)  — used by composite keys (we don't have any)
        if upper.startswith("PRIMARY KEY"):
            continue

        # Otherwise: this is a column definition.
        col = _parse_column(piece)
        if col is not None:
            table.columns.append(col)

    return table


def _parse_column(piece: str) -> Column | None:
    tokens = piece.split()
    if len(tokens) < 2:
        return None

    name = tokens[0]
    # Type may be one or two tokens (e.g. `INTEGER`, `TEXT`, `REAL`)
    col_type = tokens[1]
    rest = " ".join(tokens[2:]).upper()

    col = Column(name=name, type=col_type)
    if "PRIMARY KEY" in rest:
        col.pk = True
        col.not_null = True
    if "NOT NULL" in rest:
        col.not_null = True
    if re.search(r"\bUNIQUE\b", rest):
        col.unique = True
    m_def = re.search(r"DEFAULT\s+(\S+(?:\s+\S+)?)", rest)
    if m_def:
        col.default = m_def.group(1).strip()
    return col


# =====================================================================
# 2. Emit raw SQL
# =====================================================================


def emit_sql(tables: list[Table]) -> str:
    """Reconstruct readable SQL from the parsed tables."""
    out: list[str] = []
    out.append("-- Auto-generated from backend/app/db.py")
    out.append("-- DO NOT EDIT BY HAND")
    out.append("")
    for t in tables:
        out.append(f"-- {t.name}: {TABLE_NOTES.get(t.name, '')}")
        out.append(f"CREATE TABLE {t.name} (")
        col_lines = []
        for c in t.columns:
            parts = [f"  {c.name}", c.type]
            if c.pk:
                parts.append("PRIMARY KEY")
            if c.not_null and not c.pk:
                parts.append("NOT NULL")
            if c.unique:
                parts.append("UNIQUE")
            if c.default is not None:
                parts.append(f"DEFAULT {c.default}")
            col_lines.append(" ".join(parts))
        for fk in t.foreign_keys:
            col_lines.append(
                f"  FOREIGN KEY ({fk.column}) REFERENCES {fk.ref_table} ({fk.ref_column})"
            )
        for ug in t.unique_groups:
            col_lines.append(f"  UNIQUE ({', '.join(ug)})")
        out.append(",\n".join(col_lines))
        out.append(");")
        out.append("")
    return "\n".join(out)


# =====================================================================
# 3. Emit DBML (https://dbml.dbdiagram.io)
# =====================================================================


def emit_dbml(tables: list[Table]) -> str:
    out: list[str] = []
    out.append(
        "// Auto-generated from backend/app/db.py — paste into https://dbdiagram.io"
    )
    out.append("Project teaching_assistant {")
    out.append('  database_type: "SQLite"')
    out.append(
        '  Note: \'\'\''
        "AI 教学实训智能辅助系统 — 8 张核心业务表（数据闭环：作答 → EMA → 推荐）'''"
    )
    out.append("}")
    out.append("")

    table_groups = {
        "users": "基础数据",
        "sessions": "基础数据",
        "courses": "基础数据",
        "knowledge_points": "基础数据",
        "conversations": "对话",
        "messages": "对话",
        "knowledge_mastery": "知识追踪",
        "exercise_attempts": "知识追踪",
    }

    for t in tables:
        note = TABLE_NOTES.get(t.name, "")
        header_settings = f" [headercolor: {_dbml_color(table_groups.get(t.name))}]"
        out.append(f"Table {t.name}{header_settings} {{")
        for c in t.columns:
            settings = []
            if c.pk:
                settings.append("pk")
            if c.unique and not c.pk:
                settings.append("unique")
            if c.not_null and not c.pk:
                settings.append("not null")
            if c.default is not None:
                settings.append(f"default: {c.default}")
            settings_str = " [" + ", ".join(settings) + "]" if settings else ""
            out.append(f"  {c.name} {c.type.lower()}{settings_str}")
        if note:
            out.append(f"  Note: '{note}'")
        out.append("}")
        out.append("")

    # References
    out.append("// =========================== Refs (foreign keys) ===========================")
    for t in tables:
        for fk in t.foreign_keys:
            out.append(
                f"Ref: {t.name}.{fk.column} > {fk.ref_table}.{fk.ref_column}"
            )
    out.append("")
    return "\n".join(out)


def _dbml_color(group: str | None) -> str:
    return {
        "基础数据": "#4A90E2",
        "对话": "#2E9C6E",
        "知识追踪": "#D9822E",
    }.get(group or "", "#8888AA")


# =====================================================================
# 4. Emit Mermaid erDiagram
# =====================================================================


def emit_mermaid(tables: list[Table]) -> str:
    out: list[str] = []
    out.append("%% Auto-generated from backend/app/db.py")
    out.append("%% Render: https://mermaid.live  or VSCode mermaid preview")
    out.append("erDiagram")
    for t in tables:
        out.append(f"    {t.name} {{")
        for c in t.columns:
            ctype = c.type.lower()
            constraints = []
            if c.pk:
                constraints.append("PK")
            if c.unique and not c.pk:
                constraints.append("UK")
            cons_str = (" " + ",".join(constraints)) if constraints else ""
            out.append(f"        {ctype} {c.name}{cons_str}")
        out.append("    }")
    # Relationships
    for t in tables:
        for fk in t.foreign_keys:
            label = f"{fk.column}→{fk.ref_column}"
            # parent ||--o{ child (a parent has many children)
            out.append(
                f"    {fk.ref_table} ||--o{{ {t.name} : \"{label}\""
            )
    return "\n".join(out)


# =====================================================================
# 5. Emit Graphviz DOT
# =====================================================================


def emit_dot(tables: list[Table]) -> str:
    GROUP_COLORS = {
        "users": "#E3F2FD",
        "sessions": "#E3F2FD",
        "courses": "#E3F2FD",
        "knowledge_points": "#E3F2FD",
        "conversations": "#E8F5E9",
        "messages": "#E8F5E9",
        "knowledge_mastery": "#FFF3E0",
        "exercise_attempts": "#FFF3E0",
    }
    HEADER_COLORS = {
        "users": "#4A90E2",
        "sessions": "#4A90E2",
        "courses": "#4A90E2",
        "knowledge_points": "#4A90E2",
        "conversations": "#2E9C6E",
        "messages": "#2E9C6E",
        "knowledge_mastery": "#D9822E",
        "exercise_attempts": "#D9822E",
    }

    out: list[str] = []
    out.append("// Auto-generated from backend/app/db.py")
    out.append('digraph ER {')
    # rankdir=LR with tighter vertical spacing and wider horizontal spacing
    # produces a more landscape-shaped diagram that fits PPT slides better.
    out.append('  graph [rankdir="LR", splines="spline", fontname="Helvetica", '
               'pad="0.3", nodesep="0.20", ranksep="1.6", bgcolor="white", '
               'newrank=true, concentrate=false];')
    out.append('  node  [shape=plain, fontname="Helvetica"];')
    out.append('  edge  [fontname="Helvetica", fontsize=10, color="#555555"];')
    out.append("")

    for t in tables:
        bg = GROUP_COLORS.get(t.name, "#F5F5F5")
        head = HEADER_COLORS.get(t.name, "#666666")
        rows = [
            f'    <TR><TD BGCOLOR="{head}" COLSPAN="2"><FONT COLOR="white"><B>{t.name}</B></FONT></TD></TR>'
        ]
        if t.name in TABLE_NOTES:
            rows.append(
                f'    <TR><TD BGCOLOR="{head}" COLSPAN="2">'
                f'<FONT COLOR="white" POINT-SIZE="9">{TABLE_NOTES[t.name]}</FONT></TD></TR>'
            )
        # FK columns set for star marker
        fk_cols = {fk.column for fk in t.foreign_keys}
        for c in t.columns:
            badges: list[str] = []
            if c.pk:
                badges.append('<FONT COLOR="#C62828"><B>PK</B></FONT>')
            if c.name in fk_cols:
                badges.append('<FONT COLOR="#1565C0"><B>FK</B></FONT>')
            if c.unique and not c.pk:
                badges.append('<FONT COLOR="#6A1B9A"><B>U</B></FONT>')
            badge_str = " ".join(badges) if badges else " "
            rows.append(
                f'    <TR><TD ALIGN="LEFT" PORT="{c.name}">'
                f"<B>{c.name}</B>  <FONT POINT-SIZE=\"9\" COLOR=\"#666666\">{c.type.lower()}</FONT>"
                f'</TD><TD ALIGN="RIGHT">{badge_str}</TD></TR>'
            )
        # Composite uniques
        for ug in t.unique_groups:
            rows.append(
                f'    <TR><TD ALIGN="LEFT" COLSPAN="2"><FONT POINT-SIZE="9" COLOR="#6A1B9A">'
                f"UNIQUE ({', '.join(ug)})</FONT></TD></TR>"
            )

        label = (
            f'<\n  <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" '
            f'CELLPADDING="6" BGCOLOR="{bg}">\n'
            + "\n".join(rows)
            + "\n  </TABLE>\n>"
        )
        out.append(f'  {t.name} [label={label}];')
        out.append("")

    out.append("  // Relationships (FK -> referenced table)")
    for t in tables:
        for fk in t.foreign_keys:
            out.append(
                f'  {t.name}:{fk.column} -> {fk.ref_table}:{fk.ref_column} '
                f'[arrowhead=crow, arrowtail=none, dir=both, '
                f'taillabel="N", headlabel="1", labeldistance=2.0];'
            )
    out.append("}")
    return "\n".join(out)


# =====================================================================
# 6. Render to PNG/SVG (kroki -> dot -> mmdc fallback chain)
# =====================================================================


_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def _kroki_encode(source: str) -> str:
    """Kroki GET-URL encoding: zlib(level 9) → base64 url-safe (no padding)."""
    compressed = zlib.compress(source.encode("utf-8"), level=9)
    return base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")


def render_with_kroki(source: str, kind: str, fmt: str, out_path: Path) -> bool:
    """Render via kroki.io. Tries GET (zlib+base64) first, then POST."""
    headers = {
        "User-Agent": _USER_AGENT,
        "Accept": "image/png, image/svg+xml, */*",
    }

    # 1) GET with encoded source — bypasses any POST-size or proxy issues
    encoded = _kroki_encode(source)
    get_url = f"https://kroki.io/{kind}/{fmt}/{encoded}"
    try:
        req = urllib.request.Request(get_url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        if data:
            out_path.write_bytes(data)
            return True
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="ignore")[:200]
        except Exception:
            err_body = ""
        print(f"  [kroki GET] {kind}/{fmt} → HTTP {e.code} {err_body}")
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  [kroki GET] {kind}/{fmt} → {e}")

    # 2) POST as fallback
    post_url = f"https://kroki.io/{kind}/{fmt}"
    post_headers = dict(headers)
    post_headers["Content-Type"] = "text/plain"
    try:
        req = urllib.request.Request(
            post_url,
            data=source.encode("utf-8"),
            headers=post_headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        if data:
            out_path.write_bytes(data)
            return True
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="ignore")[:200]
        except Exception:
            err_body = ""
        print(f"  [kroki POST] {kind}/{fmt} → HTTP {e.code} {err_body}")
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  [kroki POST] {kind}/{fmt} → {e}")
    except Exception as e:  # noqa: BLE001
        print(f"  [kroki POST] {kind}/{fmt} unexpected: {e}")
    return False


def render_with_dot(dot_src: Path, fmt: str, out_path: Path) -> bool:
    if not shutil.which("dot"):
        return False
    try:
        subprocess.run(
            ["dot", f"-T{fmt}", str(dot_src), "-o", str(out_path)],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [dot] failed: {e.stderr.decode(errors='ignore')[:200]}")
        return False


def render_with_mmdc(mmd_src: Path, fmt: str, out_path: Path) -> bool:
    mmdc = shutil.which("mmdc")
    if not mmdc:
        return False
    try:
        subprocess.run(
            [mmdc, "-i", str(mmd_src), "-o", str(out_path), "-b", "white"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [mmdc] failed: {e.stderr.decode(errors='ignore')[:200]}")
        return False


# =====================================================================
# Main
# =====================================================================


def main() -> int:
    if not DB_PY.exists():
        print(f"[ERR] cannot find {DB_PY}")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Parsing {DB_PY.relative_to(ROOT)} ...")
    tables = parse_db_py(DB_PY)
    print(f"  → {len(tables)} tables: {', '.join(t.name for t in tables)}")

    summary = {
        "tables": [
            {
                "name": t.name,
                "columns": [c.name for c in t.columns],
                "foreign_keys": [
                    {"col": fk.column, "ref": f"{fk.ref_table}.{fk.ref_column}"}
                    for fk in t.foreign_keys
                ],
                "uniques": t.unique_groups,
            }
            for t in tables
        ]
    }

    files: dict[str, Path] = {
        "sql": OUT_DIR / "schema.sql",
        "dbml": OUT_DIR / "schema.dbml",
        "mmd": OUT_DIR / "schema.mmd",
        "dot": OUT_DIR / "schema.dot",
        "json": OUT_DIR / "schema.json",
    }
    files["sql"].write_text(emit_sql(tables), encoding="utf-8")
    files["dbml"].write_text(emit_dbml(tables), encoding="utf-8")
    files["mmd"].write_text(emit_mermaid(tables), encoding="utf-8")
    files["dot"].write_text(emit_dot(tables), encoding="utf-8")
    files["json"].write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print()
    print("Wrote text artifacts:")
    for name, p in files.items():
        size = p.stat().st_size
        print(f"  {name:<5}  {p.relative_to(ROOT)}  ({size:,} bytes)")

    print()
    print("Rendering images ...")
    targets = [
        ("er.png", "png"),
        ("er.svg", "svg"),
    ]
    for filename, fmt in targets:
        out_path = OUT_DIR / filename
        ok = False
        # 1) Try kroki with graphviz (richest output)
        print(f"  → {filename}: trying kroki/graphviz ...")
        ok = render_with_kroki(files["dot"].read_text(encoding="utf-8"),
                               "graphviz", fmt, out_path)
        # 2) Fallback: kroki + mermaid (simpler but works)
        if not ok:
            print(f"  → {filename}: trying kroki/mermaid ...")
            ok = render_with_kroki(files["mmd"].read_text(encoding="utf-8"),
                                   "mermaid", fmt, out_path)
        # 3) Local dot
        if not ok:
            print(f"  → {filename}: trying local `dot` ...")
            ok = render_with_dot(files["dot"], fmt, out_path)
        # 4) Local mmdc
        if not ok and fmt in ("png", "svg"):
            print(f"  → {filename}: trying local `mmdc` ...")
            ok = render_with_mmdc(files["mmd"], fmt, out_path)
        if ok:
            print(f"  ✓ {filename}: {out_path.relative_to(ROOT)} "
                  f"({out_path.stat().st_size:,} bytes)")
        else:
            print(f"  ✗ {filename}: all renderers failed; "
                  "use the .dot or .mmd file in dbdiagram.io / mermaid.live")

    print()
    print("Done. ER diagram artifacts in:", OUT_DIR.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
