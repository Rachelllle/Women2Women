from flask import Blueprint, request, session, redirect, url_for, Response
from functools import wraps
import csv, io
from database.db import db_query as query, get_db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ADMIN_PASSWORD = "admin123"
PER_PAGE = 25

def get_tables():
    rows = query(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    result = []
    for r in rows:
        name = r["name"]
        cnt  = query(f'SELECT COUNT(*) as c FROM `{name}`', one=True)["c"]
        result.append((name, cnt))
    return result

def get_columns(table):
    # Map SQLite's PRAGMA table_info to the phpMyAdmin-style shape the rest of
    # this module expects (Field / Type / Null / Key / Default / Extra).
    rows = query(f'PRAGMA table_info(`{table}`)')
    cols = []
    for r in rows:
        is_pk = bool(r["pk"])
        cols.append({
            "Field":   r["name"],
            "Type":    r["type"] or "",
            "Null":    "NO" if r["notnull"] else "YES",
            "Key":     "PRI" if is_pk else "",
            "Default": r["dflt_value"],
            "Extra":   "auto_increment" if is_pk and "INT" in (r["type"] or "").upper() else "",
        })
    return cols

def valid_table(table):
    names = [t for t, _ in get_tables()]
    return table in names

def get_pk(table):
    cols = get_columns(table)
    pk = next((c["Field"] for c in cols if c["Key"] == "PRI"), None)
    return pk or cols[0]["Field"]

def auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin_ok"):
            return redirect(url_for("admin.login_page"))
        return fn(*args, **kwargs)
    return wrapper


CSS = """
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,sans-serif;font-size:13px;background:#f5f5f5;color:#333}
a{color:#007bff;text-decoration:none}a:hover{text-decoration:underline}
#topmenu{background:#3a3f51;padding:0 12px;display:flex;align-items:center;height:36px}
#topmenu a{color:#ccc;padding:0 12px;line-height:36px;font-size:12px}
#topmenu a:hover{background:#4a5068;color:#fff;text-decoration:none}
#topmenu .brand{color:#ff9800;font-weight:700;font-size:14px;padding-right:20px;border-right:1px solid #555;margin-right:8px}
#wrap{display:flex;min-height:calc(100vh - 36px)}
#sidebar{width:200px;background:#fff;border-right:1px solid #ddd;flex-shrink:0;overflow-y:auto}
#main{flex:1;overflow:auto}
.sb-db{background:#eef2f7;padding:8px 10px;font-weight:700;font-size:12px;color:#555;border-bottom:1px solid #ddd}
.sb-table{display:flex;justify-content:space-between;align-items:center;padding:5px 10px 5px 18px;border-bottom:1px solid #f0f0f0;color:#333;font-size:12px}
.sb-table:hover{background:#eef2f7}.sb-table.on{background:#d6e4ff;font-weight:700}
.sb-table .cnt{color:#999;font-size:11px}
.breadcrumb{background:#fff;border-bottom:1px solid #ddd;padding:8px 16px;font-size:12px;color:#666}
.tabs{background:#dee2e6;border-bottom:2px solid #007bff;display:flex;padding:0 12px;padding-top:6px}
.tabs a{display:inline-block;padding:6px 14px;font-size:12px;color:#555;border:1px solid transparent;border-bottom:none;border-radius:3px 3px 0 0;margin-right:2px;background:#dee2e6}
.tabs a:hover{background:#eef2f7;text-decoration:none}
.tabs a.on{background:#fff;color:#333;border-color:#ddd;border-bottom-color:#fff;font-weight:700}
.content{padding:16px}
.pma-table{width:100%;border-collapse:collapse;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.1)}
.pma-table th{background:#3a3f51;color:#fff;padding:6px 10px;text-align:left;font-size:12px;font-weight:normal;white-space:nowrap}
.pma-table th a{color:#ffd;font-size:11px;margin-left:4px;text-decoration:none}
.pma-table td{padding:5px 10px;border-bottom:1px solid #e8e8e8;vertical-align:top;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pma-table tr:nth-child(even) td{background:#f9f9f9}
.pma-table tr:hover td{background:#fffde7}
.pma-table td.actions{white-space:nowrap;width:1px}
.btn{display:inline-block;padding:3px 10px;border:1px solid #ccc;border-radius:3px;background:#f8f8f8;color:#333;font-size:12px;cursor:pointer;line-height:1.6}
.btn:hover{background:#e8e8e8;text-decoration:none}
.btn-edit{background:#fff3cd;border-color:#ffc107;color:#856404}.btn-edit:hover{background:#ffe69c}
.btn-del{background:#f8d7da;border-color:#dc3545;color:#721c24}.btn-del:hover{background:#f1aeb5}
.btn-primary{background:#007bff;border-color:#0056b3;color:#fff}.btn-primary:hover{background:#0056b3}
.btn-success{background:#28a745;border-color:#1e7e34;color:#fff}.btn-success:hover{background:#1e7e34}
.btn-sm{padding:2px 7px;font-size:11px}
.form-table{border-collapse:collapse;width:100%;max-width:700px}
.form-table td{padding:6px 10px;vertical-align:middle}
.form-table td:first-child{font-weight:700;width:180px;color:#555;font-size:12px}
.form-input{width:100%;padding:5px 8px;border:1px solid #ccc;border-radius:3px;font-size:13px}
.sql-box{font-family:monospace;font-size:13px;width:100%;padding:8px;border:1px solid #ccc;border-radius:3px;min-height:120px;resize:vertical;background:#fafafa}
.msg-ok{background:#d4edda;border:1px solid #c3e6cb;color:#155724;padding:8px 12px;border-radius:3px;margin-bottom:12px;font-size:12px}
.msg-err{background:#f8d7da;border:1px solid #f5c6cb;color:#721c24;padding:8px 12px;border-radius:3px;margin-bottom:12px;font-size:12px}
.pager{margin-top:10px;font-size:12px;display:flex;align-items:center;gap:6px}
.pager a{padding:3px 8px;border:1px solid #ddd;border-radius:3px;background:#fff}
.pager a:hover{background:#eef2f7;text-decoration:none}
.pager span.cur{padding:3px 8px;border:1px solid #007bff;border-radius:3px;background:#007bff;color:#fff}
.struct-table{border-collapse:collapse;width:100%;background:#fff}
.struct-table th{background:#6c757d;color:#fff;padding:5px 10px;font-size:12px;font-weight:normal;text-align:left}
.struct-table td{padding:5px 10px;border-bottom:1px solid #e8e8e8;font-size:12px}
.struct-table tr:nth-child(even) td{background:#f9f9f9}
.key-pk{color:#dc3545;font-weight:700}.null-yes{color:#28a745}.null-no{color:#dc3545}
.login-wrap{display:flex;align-items:center;justify-content:center;height:100vh;background:#3a3f51}
.login-box{background:#fff;padding:30px;border-radius:4px;box-shadow:0 4px 20px rgba(0,0,0,.3);min-width:300px}
.login-box h2{margin-bottom:16px;color:#3a3f51;font-size:18px}
</style>
"""

def shell(content, table="", tab="browse", flash="", flash_type="ok"):
    tables = get_tables()
    total  = sum(c for _, c in tables)
    sb_items = "".join(
        f'<a class="sb-table {"on" if t==table else ""}" href="/admin/table/{t}">'
        f'{t}<span class="cnt">{c}</span></a>'
        for t, c in tables
    )
    flash_html = f'<div class="msg-{flash_type}">{flash}</div>' if flash else ""
    bc = (f'<span>women2women</span> &rsaquo; <b>{table}</b>' if table
          else '<b>women2women</b> (SQLite)')
    tabs_html = ""
    if table:
        def tl(label, t_tab):
            on = "on" if tab == t_tab else ""
            return f'<a class="{on}" href="/admin/table/{table}?tab={t_tab}">{label}</a>'
        tabs_html = f"""<div class="tabs">
          {tl("&#9776; Browse","browse")}{tl("&#9776; Structure","structure")}
          {tl("&#43; Insert","insert")}{tl("&#128190; Export","export")}
        </div>"""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
    <title>phpMyAdmin — women2women</title>{CSS}</head><body>
    <div id="topmenu">
      <span class="brand">phpMyAdmin</span>
      <a href="/admin">&#127968; Database</a>
      <a href="/admin/sql">&#9654; SQL</a>
      <a href="/admin/logout" style="margin-left:auto;color:#f88">&#128274; Sign out</a>
    </div>
    <div id="wrap">
      <div id="sidebar">
        <div class="sb-db">&#128196; women2women <span style="float:right;color:#999;font-size:10px">{total}r</span></div>
        {sb_items}
      </div>
      <div id="main">
        <div class="breadcrumb">{bc}</div>
        {tabs_html}
        <div class="content">{flash_html}{content}</div>
      </div>
    </div></body></html>"""


@admin_bp.get("/login")
def login_page():
    err = '<div class="msg-err">Wrong password.</div>' if request.args.get("err") else ""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Admin Login</title>{CSS}</head><body>
    <div class="login-wrap"><div class="login-box">
    <h2>&#128274; phpMyAdmin</h2>
    <p style="font-size:12px;color:#666;margin-bottom:14px">women2women · SQLite</p>{err}
    <form method="post" action="/admin/login">
    <div style="margin-bottom:10px"><label style="font-size:12px;color:#555">Password</label><br>
    <input class="form-input" name="pwd" type="password" autofocus style="margin-top:4px"></div>
    <button class="btn btn-primary" type="submit" style="width:100%;padding:7px">Sign in</button>
    </form></div></div></body></html>"""

@admin_bp.post("/login")
def login_post():
    if request.form.get("pwd") == ADMIN_PASSWORD:
        session["admin_ok"] = True
        return redirect(url_for("admin.overview"))
    return redirect(url_for("admin.login_page") + "?err=1")

@admin_bp.get("/logout")
def logout():
    session.pop("admin_ok", None)
    return redirect(url_for("admin.login_page"))


@admin_bp.get("")
@admin_bp.get("/")
@auth
def overview():
    tables = get_tables()
    rows_html = ""
    for i, (t, c) in enumerate(tables):
        ncols = len(get_columns(t))
        rows_html += f"""<tr>
          <td>{i+1}</td>
          <td><a href="/admin/table/{t}">{t}</a></td>
          <td>{ncols}</td>
          <td style="text-align:right">{c}</td>
          <td>
            <a class="btn btn-sm" href="/admin/table/{t}">Browse</a>
            <a class="btn btn-sm" href="/admin/table/{t}?tab=structure">Structure</a>
            <a class="btn btn-sm" href="/admin/table/{t}?tab=insert">Insert</a>
            <a class="btn btn-sm btn-del" href="/admin/table/{t}/empty"
               onclick="return confirm('Empty table {t}?')">Empty</a>
          </td></tr>"""
    content = f"""<h3 style="margin-bottom:12px;font-size:14px">Tables in <b>women2women</b></h3>
    <table class="pma-table"><thead><tr>
      <th>#</th><th>Table</th><th>Columns</th><th>Rows</th><th>Actions</th>
    </tr></thead><tbody>{rows_html}</tbody></table>"""
    return shell(content)


@admin_bp.get("/table/<table>")
@auth
def table_view(table):
    if not valid_table(table):
        return "Table not found", 404
    tab = request.args.get("tab", "browse")
    if tab == "structure": return _structure(table)
    if tab == "insert":    return _insert_form(table)
    if tab == "export":    return _export(table)
    return _browse(table)

def _browse(table):
    page   = max(1, int(request.args.get("page", 1)))
    sort   = request.args.get("sort", "")
    order  = request.args.get("order", "ASC")
    search = request.args.get("q", "")
    offset = (page - 1) * PER_PAGE
    cols   = [c["Field"] for c in get_columns(table)]
    pk     = get_pk(table)
    order  = "ASC" if order not in ("ASC", "DESC") else order
    sort_col = sort if sort in cols else cols[0]

    where, params = "", []
    if search:
        clauses = [f"CAST(`{c}` AS TEXT) LIKE %s" for c in cols]
        where   = "WHERE " + " OR ".join(clauses)
        params  = [f"%{search}%"] * len(cols)

    total_rows = query(f"SELECT COUNT(*) as c FROM `{table}` {where}", params, one=True)["c"]
    rows = query(
        f"SELECT * FROM `{table}` {where} ORDER BY `{sort_col}` {order} LIMIT %s OFFSET %s",
        params + [PER_PAGE, offset]
    )

    def th(col):
        new_order = "DESC" if (sort == col and order == "ASC") else "ASC"
        arrow = (" &#9650;" if order == "ASC" else " &#9660;") if sort == col else ""
        return (f'<th><a href="/admin/table/{table}?sort={col}&order={new_order}&q={search}" '
                f'style="color:#ffd">{col}{arrow}</a></th>')

    thead = "<th>Actions</th>" + "".join(th(c) for c in cols)
    tbody = ""
    for row in rows:
        pk_val = row[pk]
        cells  = "".join(f"<td title='{row[c]}'>{row[c]}</td>" for c in cols)
        tbody += (f"<tr><td class='actions'>"
                  f"<a class='btn btn-edit btn-sm' href='/admin/table/{table}/edit/{pk_val}'>Edit</a> "
                  f"<a class='btn btn-del btn-sm' href='/admin/table/{table}/delete/{pk_val}' "
                  f"onclick=\"return confirm('Delete row {pk_val}?')\">Delete</a>"
                  f"</td>{cells}</tr>")

    total_pages = max(1, (total_rows + PER_PAGE - 1) // PER_PAGE)
    pager = f'<div class="pager">Rows {offset+1}–{min(offset+PER_PAGE,total_rows)} of {total_rows}&nbsp;'
    if page > 1:
        pager += f'<a href="/admin/table/{table}?page={page-1}&sort={sort}&order={order}&q={search}">&#8592; Prev</a>'
    for p in range(max(1, page-2), min(total_pages+1, page+3)):
        tag = f'<span class="cur">{p}</span>' if p == page else f'<a href="/admin/table/{table}?page={p}&sort={sort}&order={order}&q={search}">{p}</a>'
        pager += tag
    if page < total_pages:
        pager += f'<a href="/admin/table/{table}?page={page+1}&sort={sort}&order={order}&q={search}">Next &#8594;</a>'
    pager += "</div>"

    search_bar = f"""<form method="get" style="margin-bottom:10px;display:flex;gap:6px">
      <input name="q" value="{search}" placeholder="Search all columns…" class="form-input" style="max-width:260px">
      <input type="hidden" name="sort" value="{sort}"><input type="hidden" name="order" value="{order}">
      <button class="btn btn-primary" type="submit">Search</button>
      {"<a class='btn' href='/admin/table/"+table+"'>Clear</a>" if search else ""}
    </form>"""

    content = (search_bar +
               f'<table class="pma-table"><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>' +
               pager)
    return shell(content, table=table, tab="browse")


def _structure(table):
    cols = get_columns(table)
    rows = ""
    for i, c in enumerate(cols):
        pk   = '<span class="key-pk">PRI</span>' if c["Key"] == "PRI" else c["Key"] or ""
        null = '<span class="null-yes">YES</span>' if c["Null"] == "YES" else '<span class="null-no">NO</span>'
        dflt = c["Default"] if c["Default"] is not None else "<em style='color:#999'>NULL</em>"
        rows += f"<tr><td>{i+1}</td><td><b>{c['Field']}</b></td><td>{c['Type']}</td><td>{null}</td><td>{dflt}</td><td>{pk}</td><td>{c['Extra']}</td></tr>"
    cnt = query(f"SELECT COUNT(*) as c FROM `{table}`", one=True)["c"]
    content = f"""<p style="margin-bottom:10px;font-size:12px;color:#555">{cnt} rows in table</p>
    <table class="struct-table"><thead><tr>
      <th>#</th><th>Field</th><th>Type</th><th>Null</th><th>Default</th><th>Key</th><th>Extra</th>
    </tr></thead><tbody>{rows}</tbody></table>"""
    return shell(content, table=table, tab="structure")


def _insert_form(table, prefill=None, flash="", flash_type="ok"):
    cols = get_columns(table)
    fields = ""
    for c in cols:
        is_auto = "auto_increment" in (c["Extra"] or "")
        if is_auto:
            fields += f'<tr><td>{c["Field"]}<br><small style="color:#999">{c["Type"]}</small></td><td><input class="form-input" disabled placeholder="auto_increment" style="background:#f0f0f0;color:#999"></td></tr>'
        else:
            val = (prefill or {}).get(c["Field"], "")
            fields += f'<tr><td>{c["Field"]}<br><small style="color:#999">{c["Type"]}</small></td><td><input class="form-input" name="{c["Field"]}" value="{val}"></td></tr>'
    content = f"""<form method="post" action="/admin/table/{table}/insert">
    <table class="form-table">{fields}</table>
    <div style="margin-top:14px">
      <button class="btn btn-success" type="submit">&#10003; Insert</button>
      <a class="btn" href="/admin/table/{table}?tab=insert">Reset</a>
    </div></form>"""
    return shell(content, table=table, tab="insert", flash=flash, flash_type=flash_type)


def _export(table):
    content = f"""<h3 style="margin-bottom:12px;font-size:13px">Export <b>{table}</b></h3>
    <p style="margin-bottom:12px;font-size:12px;color:#555">Download as CSV.</p>
    <a class="btn btn-success" href="/admin/table/{table}/export.csv">&#128190; Download CSV</a>"""
    return shell(content, table=table, tab="export")


@admin_bp.post("/table/<table>/insert")
@auth
def insert_row(table):
    if not valid_table(table): return "Not found", 404
    cols = [c["Field"] for c in get_columns(table) if "auto_increment" not in (c["Extra"] or "")]
    vals = [request.form.get(c, "") for c in cols]
    try:
        col_names    = ", ".join(f"`{c}`" for c in cols)
        placeholders = ", ".join(["%s"] * len(cols))
        query(f"INSERT INTO `{table}` ({col_names}) VALUES ({placeholders})", vals, write=True)
        return redirect(f"/admin/table/{table}?tab=insert&flash=Row+inserted&ft=ok")
    except Exception as e:
        return _insert_form(table, prefill=request.form, flash=str(e), flash_type="err")

@admin_bp.get("/table/<table>/delete/<pk_val>")
@auth
def delete_row(table, pk_val):
    if not valid_table(table): return "Not found", 404
    pk = get_pk(table)
    query(f"DELETE FROM `{table}` WHERE `{pk}` = %s", (pk_val,), write=True)
    return redirect(f"/admin/table/{table}")

@admin_bp.get("/table/<table>/edit/<pk_val>")
@auth
def edit_form(table, pk_val):
    if not valid_table(table): return "Not found", 404
    pk  = get_pk(table)
    row = query(f"SELECT * FROM `{table}` WHERE `{pk}` = %s", (pk_val,), one=True)
    if not row: return "Row not found", 404
    cols = get_columns(table)
    fields = ""
    for c in cols:
        val      = row.get(c["Field"], "")
        disabled = 'disabled style="background:#f0f0f0;color:#999"' if c["Key"] == "PRI" else ""
        fields  += (f'<tr><td>{c["Field"]}<br><small style="color:#999">{c["Type"]}</small></td>'
                    f'<td><input class="form-input" name="{c["Field"]}" value="{val if val is not None else ""}" {disabled}></td></tr>')
    content = f"""<h3 style="margin-bottom:12px;font-size:13px">Edit row — {pk} = {pk_val}</h3>
    <form method="post" action="/admin/table/{table}/edit/{pk_val}">
    <table class="form-table">{fields}</table>
    <div style="margin-top:14px">
      <button class="btn btn-success" type="submit">&#10003; Save</button>
      <a class="btn" href="/admin/table/{table}">Cancel</a>
    </div></form>"""
    return shell(content, table=table, tab="browse")

@admin_bp.post("/table/<table>/edit/<pk_val>")
@auth
def edit_save(table, pk_val):
    if not valid_table(table): return "Not found", 404
    pk       = get_pk(table)
    editable = [c["Field"] for c in get_columns(table) if c["Key"] != "PRI"]
    sets     = ", ".join(f"`{c}` = %s" for c in editable)
    vals     = [request.form.get(c, "") for c in editable] + [pk_val]
    query(f"UPDATE `{table}` SET {sets} WHERE `{pk}` = %s", vals, write=True)
    return redirect(f"/admin/table/{table}")

@admin_bp.get("/table/<table>/empty")
@auth
def empty_table(table):
    if not valid_table(table): return "Not found", 404
    query(f"DELETE FROM `{table}`", write=True)
    return redirect(url_for("admin.overview"))

@admin_bp.get("/table/<table>/export.csv")
@auth
def export_csv(table):
    if not valid_table(table): return "Not found", 404
    rows = query(f"SELECT * FROM `{table}`")
    cols = list(rows[0].keys()) if rows else []
    buf  = io.StringIO()
    w    = csv.writer(buf)
    w.writerow(cols)
    for row in rows:
        w.writerow([row[c] for c in cols])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment;filename={table}.csv"})


@admin_bp.get("/sql")
@auth
def sql_get():
    return _sql_page()

@admin_bp.post("/sql")
@auth
def sql_post():
    q = request.form.get("q", "").strip()
    result, flash, ft = "", "", "ok"
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(q)
        rows = cur.fetchall()
        conn.commit(); conn.close()
        if rows:
            cols   = list(rows[0].keys())
            thead  = "".join(f"<th>{c}</th>" for c in cols)
            tbody  = "".join("<tr>" + "".join(f"<td>{row[c]}</td>" for c in cols) + "</tr>" for row in rows)
            result = f'<table class="pma-table" style="margin-top:16px"><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>'
            flash  = f"{len(rows)} rows returned"
        else:
            flash = f"Query OK"
    except Exception as e:
        flash, ft = str(e), "err"
    return _sql_page(q, result, flash, ft)

def _sql_page(q="", result="", flash="", ft="ok"):
    content = f"""<h3 style="margin-bottom:10px;font-size:13px">&#9654; SQL Console — women2women (SQLite)</h3>
    <form method="post" action="/admin/sql">
    <textarea class="sql-box" name="q">{q}</textarea>
    <div style="margin-top:8px">
      <button class="btn btn-primary" type="submit">&#9654; Run</button>
    </div></form>{result}"""
    return shell(content, flash=flash, flash_type=ft)
