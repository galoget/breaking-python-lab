"""Breaking Python Lab: INTENTIONALLY VULNERABLE application (main branch).

For educational use only, in an isolated environment of your own.
Do NOT deploy it to production or expose it to the Internet.
The fixed version lives in the `fixed` branch.
"""
import base64
import os
import pickle
import sqlite3

import requests
import yaml
from flask import Flask, request, render_template_string, send_file
from lxml import etree
from markupsafe import Markup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lab.db")

app = Flask(__name__)
app.secret_key = "lab-secret-not-real"


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "id INTEGER PRIMARY KEY, name TEXT, password TEXT, note TEXT)"
    )
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO users (name, password, note) VALUES "
            "('guest', 'guest', 'Unprivileged user'),"
            "('admin', 'Adm1n-lab-only', 'FLAG{sqli_you_found_the_admin}')"
        )
        conn.commit()
    return conn


@app.route("/")
def index():
    return (
        "<h1>Breaking Python Lab</h1>"
        "<p>Intentionally vulnerable application. Educational use only.</p>"
        "<ul>"
        "<li>/login?user=guest</li>"
        "<li>/ping?host=127.0.0.1</li>"
        "<li>/download?file=report.txt</li>"
        "<li>POST /import (XML)</li>"
        "<li>/search?q=python</li>"
        "<li>/hello?name=world</li>"
        "<li>/session/new and /session</li>"
        "<li>POST /config (YAML)</li>"
        "<li>/preview?url=https://example.com</li>"
        "</ul>"
    )


# 1. SQL Injection (CWE-89)
@app.route("/login")
def login():
    u = request.args["user"]  # source
    q = f"SELECT * FROM users WHERE name='{u}'"
    row = db().execute(q).fetchone()  # sink
    return f"Hello {row[1]}: {row[3]}" if row else ("User not found", 404)


# 2. Command Injection (CWE-78)
@app.route("/ping")
def ping():
    h = request.args["host"]  # source
    cmd = f"ping -c 1 {h}"
    return "<pre>" + os.popen(cmd).read() + "</pre>"  # sink


# 3. Path Traversal / LFI (CWE-22)
@app.route("/download")
def download():
    name = request.args["file"]  # source
    return send_file("uploads/" + name)  # sink


# 4. XXE (CWE-611)
@app.post("/import")
def import_xml():
    p = etree.XMLParser(resolve_entities=True)
    doc = etree.fromstring(request.data, p)  # sink
    return doc.findtext("name") or ""


# 5. Reflected XSS (CWE-79)
@app.route("/search")
def search():
    q = request.args.get("q", "")  # source
    return Markup(f"<h1>Results: {q}</h1>")  # sink


# 6. SSTI (CWE-1336)
@app.route("/hello")
def hello():
    name = request.args.get("name", "world")  # source
    tpl = f"<p>Hello {name}</p>"
    return render_template_string(tpl)  # sink


# 7. Insecure deserialization: pickle (CWE-502)
@app.route("/session/new")
def session_new():
    raw = pickle.dumps({"user": "guest"})
    resp = app.make_response("Cookie 's' issued")
    resp.set_cookie("s", base64.b64encode(raw).decode())
    return resp


@app.route("/session")
def session_load():
    raw = base64.b64decode(request.cookies["s"])  # source
    data = pickle.loads(raw)  # sink
    return f"Session for: {data['user']}"


# 8. Insecure deserialization: yaml.load (CWE-502)
@app.post("/config")
def config():
    data = yaml.load(request.data, Loader=yaml.Loader)  # sink
    return repr(data)


# 9. SSRF (CWE-918)
@app.route("/preview")
def preview():
    url = request.args["url"]  # source
    r = requests.get(url, timeout=3)  # sink
    return r.text


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
