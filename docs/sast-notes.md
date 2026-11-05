# SAST notes: what the tools catch (and miss)

*Read this in other languages: [Español](sast-notes.es.md).*

Static analysis (SAST) scans source code for risky patterns without running it. This lab is a good place to see **what SAST does well and where it fails** — a core point of the talk: tools find *patterns*, humans find *logic*.

The results below are **real**, produced by running the tools on this repo. They are a snapshot: rule packs change over time, so re-run them yourself.

## Environment and exact commands

```
Python   3.14.7
bandit   1.9.4
semgrep  1.183.0
```

With the virtual environment active (`pip install -r requirements-dev.txt`), run on each branch:

```
# on main (vulnerable), then: git checkout fixed, and run again
bandit -r app/
semgrep --config auto app/
```

> `semgrep --config auto` downloads a rule pack from the Semgrep registry (needs network) and enables anonymous metrics. Offline, pin a local/registry pack instead, e.g. `semgrep --config p/python app/`.

## Per-challenge results on `main` (vulnerable)

| # | Vulnerability | bandit | semgrep | Detected by |
|---|---------------|--------|---------|-------------|
| 1 | SQL Injection | `B608` (Medium, Low conf.) | `tainted-sql-string`, `formatted-sql-query`, `sql-injection-db-cursor-execute` | both |
| 2 | Command Injection | `B605` start_process_with_a_shell (**High**) | `dangerous-system-call` | both |
| 3 | Path Traversal / LFI | — | — | **neither** |
| 4 | XXE | — | — | **neither** |
| 5 | Reflected XSS | `B704` markupsafe_markup_xss (Medium) | `explicit-unescape-with-markup` | both |
| 6 | SSTI | — | `dangerous-template-string`, `render-template-string` | semgrep only |
| 7 | Deserialization (pickle) | `B301`/`B403` (Medium/Low) | `insecure-deserialization`, `avoid-pickle` | both |
| 8 | Deserialization (yaml) | `B506` yaml_load (Medium) | `avoid-pyyaml-load` | both |
| 9 | SSRF | — | `ssrf-requests`, `ssrf-injection-requests` | semgrep only |
| 10 | Broken Access Control / IDOR | — | — | **neither** |

**Coverage:** bandit flagged 5 of 10, semgrep 7 of 10. **Even combined, 3 of 10 slip through completely: Path Traversal / LFI, XXE, and IDOR** — including Broken Access Control, OWASP's #1 category.

Raw counts (there is overlap — several rules can hit one line): bandit reported **7 issues** on `main` (1 High, 4 Medium, 2 Low); semgrep reported **25 findings** across 15 rules.

## Before vs after (`main` → `fixed`)

| Tool | `main` | `fixed` |
|------|--------|---------|
| bandit | 7 issues (incl. 1 High, 4 Medium) | 3 issues (all **Low**) |
| semgrep | 25 findings / 15 rules | 8 findings / 3 rules |

The *dangerous* findings disappear on `fixed` — but the residue is **all false positives**, which is itself a lesson:

- **bandit on `fixed`:** `B404` (subprocess import), `B607` (partial path `ping`), `B603` (subprocess "check for untrusted input"). All **Low**, all benign: the fix runs `ping` with an argument list (no shell) *and* validates the input as an IP. The scanner cannot see that the input is already safe.
- **semgrep on `fixed`:** `render-template-string` (×6) and `ssrf-requests` (×2). All false positives: the templates are constant with autoescaped variables, and the request goes through an allowlist + internal-IP block. The scanner flags the *function call*, not the *safety around it*.

## Why SAST misses things (and over-reports)

1. **It cannot reason about authorization or business logic.** IDOR is invisible to both tools in both branches: deciding *who may read which note* is a policy the scanner has no model of. Access-control bugs are the OWASP #1 category and the hardest for SAST.
2. **Context defeats pattern matching.** XXE here builds a parser object with `resolve_entities=True` and uses it elsewhere; the LFI concatenates a path. Neither matched a rule, because the dangerous property is spread across statements rather than a single recognizable sink.
3. **False positives are the norm on safe code.** Every finding on `fixed` is a false positive. Someone must triage each one — "is this *actually* exploitable?" — which is manual, offensive-minded work. Alert fatigue causes real bugs to be dismissed.
4. **Severity and confidence are rough.** bandit rated a working SQL injection `Medium / Low confidence`, and raised the lab's throwaway secret (`B105`) and a bare `import pickle` (`B403`) as issues — noise competing with the real High finding.
5. **Tools disagree.** semgrep caught SSTI and SSRF; bandit did not. bandit caught the hardcoded string; semgrep did not treat it the same way. Run more than one — and still do not assume full coverage.

## Takeaway

SAST is a fast first pass that reliably catches well-known injection and deserialization sinks, but it does **not** replace manual review and offensive testing. On this lab, two industry tools together left **30%** of the vulnerabilities undetected — exactly the ones that need a human who understands the application: logic, context, and authorization. That gap is the whole point of pairing AppSec with OffSec.

## Reproduce it

```
git checkout main  && bandit -r app/ ; semgrep --config auto app/
git checkout fixed && bandit -r app/ ; semgrep --config auto app/
```

Compare the output against `exploits/poc.py` (which proves what is *actually* exploitable) and the [manual cheat sheet](../exploits/manual-exploits.md).
