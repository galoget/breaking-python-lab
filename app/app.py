"""Breaking Python Lab: FIXED version (fixed branch).

Each function keeps its route, but the flaw from `main` is fixed.
Compare with: git diff main fixed -- app/app.py
"""
import ipaddress
import os
import socket
import sqlite3
import subprocess
from urllib.parse import urlparse

import defusedxml.ElementTree as ET
import requests
import yaml
from flask import Flask, abort, render_template, render_template_string, request, send_from_directory
from itsdangerous import BadSignature, URLSafeSerializer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lab.db")

app = Flask(__name__)
# Random key per startup; on a real system it would come from a secrets manager.
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32).hex()
signer = URLSafeSerializer(app.secret_key, salt="lab-session")

# Allowed destinations for /preview (explicit allowlist).
ALLOWED_HOSTS = set(filter(None, os.environ.get("ALLOWED_HOSTS", "example.com").split(",")))


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
        "<h1>Breaking Python Lab (fixed branch)</h1>"
        "<p>Fixed version. Run exploits/poc.py: there must be no findings.</p>"
    )


# 1. SQL Injection -> parameterized query
@app.route("/login")
def login():
    u = request.args["user"]
    q = "SELECT * FROM users WHERE name=?"
    row = db().execute(q, (u,)).fetchone()
    return render_template_string("Hello {{ n }}: {{ t }}", n=row[1], t=row[3]) if row else ("User not found", 404)


# 2. Command Injection -> no shell, input validated as an IP
@app.route("/ping")
def ping():
    try:
        h = str(ipaddress.ip_address(request.args["host"]))
    except ValueError:
        abort(400)
    r = subprocess.run(["ping", "-c", "1", h], capture_output=True, text=True, timeout=10)
    return render_template_string("<pre>{{ out }}</pre>", out=r.stdout)


# 3. Path Traversal / LFI -> send_from_directory resolves and validates the path
@app.route("/download")
def download():
    name = request.args["file"]
    return send_from_directory("uploads", name)


# 4. XXE -> defusedxml rejects DTDs and entities
@app.post("/import")
def import_xml():
    try:
        doc = ET.fromstring(request.data)
    except Exception:
        abort(400)
    return doc.findtext("name") or ""


# 5. XSS -> template with autoescaping (templates/search.html)
@app.route("/search")
def search():
    q = request.args.get("q", "")
    return render_template("search.html", q=q)


# 6. SSTI -> fixed template, the input travels as a variable
@app.route("/hello")
def hello():
    name = request.args.get("name", "world")
    return render_template_string("<p>Hello {{ name }}</p>", name=name)


# 7. Deserialization -> signed cookie (JSON data), not pickle
@app.route("/session/new")
def session_new():
    resp = app.make_response("Cookie 's' issued")
    resp.set_cookie("s", signer.dumps({"user": "guest"}), httponly=True, samesite="Lax")
    return resp


@app.route("/session")
def session_load():
    try:
        data = signer.loads(request.cookies["s"])
    except (KeyError, BadSignature):
        abort(400)
    return render_template_string("Session for: {{ u }}", u=data["user"])


# 8. yaml.load -> yaml.safe_load
@app.post("/config")
def config():
    try:
        data = yaml.safe_load(request.data)
    except yaml.YAMLError:
        abort(400)
    return repr(data)


# 9. SSRF -> allowlist + blocking internal IPs + no redirects
def _is_public(host):
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    return all(ipaddress.ip_address(i[4][0]).is_global for i in infos)


@app.route("/preview")
def preview():
    url = request.args["url"]
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or parsed.hostname not in ALLOWED_HOSTS:
        abort(400)
    if not _is_public(parsed.hostname):
        abort(400)
    # Note: a complete defense also pins the resolved IP to prevent DNS rebinding.
    r = requests.get(url, timeout=3, allow_redirects=False)
    return render_template_string("{{ body }}", body=r.text)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
