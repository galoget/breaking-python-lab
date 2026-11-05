# Breaking Python Lab

*Read this in other languages: [Español](README.es.md).*

Lab for the talk & hands-on workshop **Breaking Python: AppSec vs. OffSec — From Code to Exploit**.

An **intentionally vulnerable** Flask application so you can download the code, analyze it, run it locally and exploit it. Every vulnerability has its fixed counterpart in the `fixed` branch.

> **Warning.** This code is insecure on purpose. Use it only on your own machine or in an isolated environment. Do not deploy it to an Internet-facing server, and do not run the exploits against systems that are not yours.

> **Scope and design.** This lab deliberately strips each challenge down to the vulnerability itself: no frontend, no styling, no REST/API conventions — just the route, the `source` (where attacker input enters) and the `sink` (where it causes harm), marked with comments. That keeps the focus on *why* the flaw exists and how the fix closes it, without UI or framework noise. It is a teaching tool, not a polished application.

> **Not a Python problem.** These flaws come from insecure *coding patterns* — trusting input, mixing code and data, picking an unsafe default — not from Python itself. The same vulnerability classes (SQL injection, command injection, XXE, SSRF, IDOR, ...) show up in Java, PHP, Node.js, C#, Go and every other ecosystem; only the syntax of the sink changes. Python is just the vehicle for the talk, and the lessons transfer directly to whatever language you write.

## How it is organized

| Branch | Content |
|--------|---------|
| `main` | Vulnerable application |
| `fixed` | Same application, with every flaw fixed |

To see all the fixes at once: `git diff main fixed -- app/app.py`

## Releases

Each branch is published as a release:

| Release | Branch | Use it to |
|---------|--------|-----------|
| [`v1.0.0`](https://github.com/galoget/breaking-python-lab/releases/tag/v1.0.0) | `main` | Attack the lab — every vulnerability is live |
| [`v1.0.1`](https://github.com/galoget/breaking-python-lab/releases/tag/v1.0.1) | `fixed` | Study the mitigations — every vulnerability is patched |

GitHub shows **`v1.0.1` (fixed) as the "Latest" release**, simply because it has the higher version number. That is expected and it is **not** where you start: the newest tag is the *patched* code. Begin on the default `main` branch (`v1.0.0`, vulnerable), exploit each flaw, then switch to `fixed` (`v1.0.1`) to see how each one was closed:

```
git checkout main    # vulnerable (v1.0.0) -> exploit this first
git checkout fixed   # patched    (v1.0.1) -> compare the fixes
```

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
| 10 | Broken Access Control / IDOR | CWE-639 | `/note?id=` | Ownership enforced from the signed session |

**Why each fix works** (defense in depth, fail-closed, output encoding, input validation, allowlisting): see [`fixes-explained.md`](docs/fixes-explained.md).

## Quick start

### With Docker

```
git clone https://github.com/galoget/breaking-python-lab
cd breaking-python-lab
docker compose up --build
```

The application is then available at http://127.0.0.1:5000 (only reachable from your own machine).

#### Installing Docker on Debian/Ubuntu

If you do not have Docker yet, install the engine and Compose v2 from the distribution packages. The Compose package name differs by distribution:

```
# Debian / Kali
sudo apt update
sudo apt install -y docker.io docker-compose

# Ubuntu
sudo apt update
sudo apt install -y docker.io docker-compose-v2
```

Then enable the service and (optionally) let your user run Docker without sudo:

```
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"   # add your user to the 'docker' group; log out
                                  # and back in, or run `newgrp docker`, so the
                                  # new group membership takes effect in your shell
```

Verify (both packages provide Compose v2, i.e. the `docker compose` subcommand):

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

A single `pip install` covers both branches, so you do not need to reinstall after `git checkout fixed`. Everything below (the PoCs and the SAST tools) assumes this virtual environment is active (`source .venv/bin/activate`).

### Optional: `make` shortcuts

A `Makefile` wraps the commands used throughout this README so you do not have to retype them. It is **entirely optional** — each target just runs the same command documented elsewhere. Run `make help` to list them:

| Target | What it does |
|--------|--------------|
| `make install` | Install runtime dependencies (both branches) |
| `make install-dev` | Install the SAST tools (bandit + semgrep) |
| `make run` | Start the lab + the simulated internal service (SSRF) |
| `make poc` | Run all proof-of-concept tests against a running lab |
| `make lint` | Check code style (flake8, 79 columns) |
| `make sast` | Run static analysis on `app/` (bandit + semgrep) |
| `make docker-up` / `make docker-down` | Start / stop the lab with Docker |
| `make clean` | Remove the local database and Python caches |

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
6. **Verify and detect.** With the fixed application running, `poc.py` must report `0/10` findings and exit with code `0`. Use it as a regression test.

## Flags

**Not every challenge has a flag — that is by design, because of the nature of each vulnerability.** Only four flaws disclose a stored secret, so only those hide a literal `FLAG{...}` to capture (SQLi, LFI, SSRF, IDOR). The other six (command injection, XXE, XSS, SSTI, pickle, yaml) grant code execution or in-place disclosure, so there is no flag string — the successful exploitation *is* the proof. The four real flags are censored below on purpose: the prefix and the location are the hint, not the answer.

| # | Challenge | Flag (censored) | Where to find it |
|---|-----------|-----------------|------------------|
| 1 | SQL Injection | `FLAG{sqli_****}` | Database, `users` table (admin row) — via `/login` |
| 2 | Command Injection | *(proof)* output of your command, e.g. `id` → `uid=...` | runs on the server |
| 3 | Path Traversal / LFI | `FLAG{lfi_****}` | `app/.env` — via `/download` |
| 4 | XXE | *(proof)* contents of a local file, e.g. `/etc/passwd` | read by the XML parser |
| 5 | Reflected XSS | *(proof)* your `<script>` executes | in the browser (client-side) |
| 6 | SSTI | *(proof)* template math runs (`{{7*7}}`→`49`) → RCE | on the server |
| 7 | Deserialization (pickle) | *(proof)* your code runs when `/session` loads | on the server |
| 8 | Deserialization (yaml) | *(proof)* your code runs on `POST /config` | on the server |
| 9 | SSRF | `FLAG{ssrf_****}` | Simulated internal service (JSON) — via `/preview` |
| 10 | Broken Access Control / IDOR | `FLAG{idor_****}` | Database, `notes` table (admin's note) — via `/note` |

Once you reach code execution (SSTI, pickle, yaml, command injection) or arbitrary file read (LFI, XXE), you can read any stored flag — that overlap is realistic.

## Static analysis (SAST)

With the virtual environment active:

```
pip install -r requirements-dev.txt   # bandit + semgrep (not runtime deps)
bandit -r app/
semgrep --config auto app/
```

Compare what each tool detects on `main` and on `fixed`. Not every flaw shows up: part of the exercise is identifying which ones slip through. Real results (exact versions, the catches and the misses) and the limitations of SAST are written up in [`docs/sast-notes.md`](docs/sast-notes.md).

## Advanced exercise (out of scope): SSRF and DNS rebinding

> **Out of scope.** The `fixed` branch applies the standard SSRF mitigation (an explicit allowlist plus blocking internal IPs). The hardening described here is intentionally left as an exercise and is **not** implemented in `fixed`.

The SSRF fix validates the destination host and then fetches it, but the hostname is resolved **twice**: once by the check (`_is_public`) and again by the HTTP client when it connects. That is a time-of-check / time-of-use (TOCTOU) gap: a hostname whose DNS the attacker controls can return a public IP during the check and an internal IP (`127.0.0.1`, `169.254.169.254`, ...) during the fetch. This is **DNS rebinding**.

It becomes exploitable when an attacker controls the DNS for a host that passes your checks — most commonly an app that fetches a **user-supplied URL** (webhook, "import from URL", link preview) defended only by "resolve and check the IP is public", or an allowlist containing a host whose DNS the attacker can influence. This lab is **not** exploitable: the allowlist is `example.com`, whose DNS the attacker does not control, so the check and the fetch always see the same public IP.

The concrete scenarios and the proper fix — resolve once, validate every returned IP, and **pin** it for the connection — are explained in [`fixes-explained.md`](docs/fixes-explained.md#deep-dive-ssrf-and-dns-rebinding).

## Structure

```
app/
  app.py               Flask application (vulnerable on main, fixed on fixed)
  internal_service.py  Simulated internal service for SSRF (127.0.0.1 only)
  templates/           Templates (search.html, used by the fixed branch)
  uploads/             Files allowed for download
  .env                 FAKE values used in the LFI challenge
exploits/poc.py                 Harmless proofs of concept and regression check
exploits/manual-exploits.md     Manual curl exploitation cheat sheet (English)
exploits/manual-exploits.es.md  Manual curl exploitation cheat sheet (Spanish)
docs/fixes-explained.md         Why each fix works (English)
docs/fixes-explained.es.md      Why each fix works (Spanish)
docs/sast-notes.md              What SAST catches and misses (English)
docs/sast-notes.es.md           What SAST catches and misses (Spanish)
SECURITY.md, SECURITY.es.md     Security policy (intentionally-vulnerable notice)
Dockerfile, docker-compose.yml, start.sh
Makefile                        Convenience targets (run `make help`)
.dockerignore, .flake8, .editorconfig
requirements.txt, requirements-dev.txt   Runtime deps / dev tools (SAST)
```

## License

This project — **code and documentation** — is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/) license. See [`LICENSE`](LICENSE).

You may use, share and adapt it for **non-commercial** purposes, as long as you **credit** "Galoget Latorre / Hackem Cybersecurity", link to the license, note any changes, and release any derivative (fork or variant) under the **same** license.

Author: Galoget Latorre · Hackem Cybersecurity · https://hackem.org
