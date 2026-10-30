# Breaking Python Lab

*Read this in other languages: [Español](README.es.md).*

Lab for the talk **Breaking Python: AppSec vs. OffSec — From Code to Exploit**.

An **intentionally vulnerable** Flask application so you can download the code, analyze it, run it locally and exploit it. Every vulnerability has its fixed counterpart in the `fixed` branch.

> **Warning.** This code is insecure on purpose. Use it only on your own machine or in an isolated environment. Do not deploy it to an Internet-facing server, and do not run the exploits against systems that are not yours.

## How it is organized

| Branch | Content |
|--------|---------|
| `main` | Vulnerable application |
| `fixed` | Same application, with every flaw fixed |

To see all the fixes at once: `git diff main fixed -- app/app.py`

## Vulnerabilities

| # | Flaw | CWE | Endpoint | Fix in `fixed` |
|---|------|-----|----------|-----------------|
| 1 | SQL Injection | CWE-89 | `/login?user=` | Parameterized query |
| 2 | Command Injection | CWE-78 | `/ping?host=` | `subprocess` without a shell + validation with `ipaddress` |
| 3 | Path Traversal / LFI | CWE-22 | `/download?file=` | `send_from_directory` |
| 4 | XXE | CWE-611 | `POST /import` | `defusedxml` |
| 5 | Reflected XSS | CWE-79 | `/search?q=` | Template with autoescaping |
| 6 | SSTI (Jinja2) | CWE-1336 | `/hello?name=` | Input as a variable, fixed template |
| 7 | Deserialization (`pickle`) | CWE-502 | `/session` (cookie `s`) | Cookie signed with `itsdangerous` |
| 8 | Deserialization (`yaml.load`) | CWE-502 | `POST /config` | `yaml.safe_load` |
| 9 | SSRF | CWE-918 | `/preview?url=` | Allowlist of destinations + blocking internal IPs |

## Quick start

### With Docker

```
git clone https://github.com/galoget/breaking-python-lab
cd breaking-python-lab
docker compose up --build
```

The application is then available at http://127.0.0.1:5000 (only reachable from your own machine).

#### Installing Docker on Debian/Ubuntu

If you do not have Docker yet, install the engine and the Compose plugin from the distribution packages:

```
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"   # log out and back in to use docker without sudo
```

Verify the installation:

```
docker --version
docker compose version
```

### Without Docker

Requires Python 3.10 or later and `ping` installed.

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd app
python internal_service.py &     # simulated internal service for the SSRF challenge
python app.py
```

Everything below (the PoCs and the SAST tools) assumes this virtual environment is active (`source .venv/bin/activate`).

## How to practice: from code to exploit

Follow the method from the talk on every challenge:

1. **Read the code.** Open `app/app.py`. Each function marks the `source` and the `sink` with comments.
2. **Understand the flaw.** Why does the data reach the sink without any control?
3. **Exploit it by hand.** With `curl` or Burp Suite. Harmless examples:
   - SQLi: `curl "http://127.0.0.1:5000/login?user=x'%20OR%20name='admin'%20--"`
   - SSTI: `curl "http://127.0.0.1:5000/hello?name=%7B%7B7*7%7D%7D"` (should answer 49)
   - LFI: `curl "http://127.0.0.1:5000/download?file=../.env"`
   - Full manual exploitation (one real `curl` per flaw, pentest-style): see [`exploits/manual-exploits.md`](exploits/manual-exploits.md)
4. **Automate.** `exploits/poc.py` runs one test per vulnerability with harmless payloads:
   ```
   python exploits/poc.py                  # all
   python exploits/poc.py --only lfi sqli  # some
   ```
5. **Fix.** Switch to `fixed` and compare: `git checkout fixed`
6. **Verify and detect.** With the fixed application running, `poc.py` must report `0/9` findings and exit with code `0`. Use it as a regression test.

Tiered hints for the CTF-style challenges: the flags use the `FLAG{...}` format and live in the database, in `app/.env` and in the simulated internal service.

## Static analysis (SAST)

With the virtual environment active:

```
pip install bandit semgrep
bandit -r app/
semgrep --config auto app/
```

Compare what each tool detects on `main` and on `fixed`. Not every flaw shows up: part of the exercise is identifying which ones slip through.

## Advanced exercise (out of scope): SSRF and DNS rebinding

> **Out of scope.** The `fixed` branch applies the standard SSRF mitigation (an explicit allowlist plus blocking internal IPs). The hardening described here is intentionally left as an exercise and is **not** implemented in `fixed`.

The SSRF fix validates the destination host and then fetches it, but the hostname is resolved **twice**: once by the check (`_is_public`) and again by the HTTP client when it connects. That is a time-of-check / time-of-use (TOCTOU) gap: a hostname whose DNS the attacker controls can return a public IP during the check and an internal IP (`127.0.0.1`, `169.254.169.254`, ...) during the fetch. This is **DNS rebinding**.

With the default allowlist (`example.com`) it is not exploitable, because the attacker does not control that domain's DNS. It only matters if an allowlisted host is one whose DNS an attacker controls.

How you would close it (resolve once, validate, then connect to that exact IP — "pin" the IP):

- Resolve the hostname once, validate **every** returned IP (reject private, loopback, link-local, CGNAT and reserved ranges, plus IPv4-mapped IPv6), and connect only to a validated IP while keeping the original `Host` header and TLS SNI. A custom `requests` `HTTPAdapter` / `urllib3` pool is the clean way to do this without breaking HTTPS.
- Or validate the real peer IP **after** connecting (`socket.getpeername()`) and abort if it is not public.
- Re-validate every hop if redirects are ever enabled (the fix keeps `allow_redirects=False`).
- Infrastructure level: a dedicated egress proxy with no route to internal ranges, a locked-down network namespace, or cloud IMDSv2 with a hop limit.

## Structure

```
app/
  app.py               Flask application (vulnerable on main, fixed on fixed)
  internal_service.py  Simulated internal service for SSRF (127.0.0.1 only)
  templates/           Templates
  uploads/             Files allowed for download
  .env                 FAKE values used in the LFI challenge
exploits/poc.py              Harmless proofs of concept and regression check
exploits/manual-exploits.md  Manual curl exploitation cheat sheet (pentest-style)
Dockerfile, docker-compose.yml, start.sh
```

## License

MIT. See `LICENSE`.

Author: Galoget Latorre · Hackem Cybersecurity · https://hackem.org
