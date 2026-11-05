# Security policy

*Read this in other languages: [Español](SECURITY.es.md).*

## This repository is intentionally vulnerable

`breaking-python-lab` is a teaching lab for the talk & hands-on workshop
**Breaking Python: AppSec vs. OffSec**. The `main` branch contains **deliberate,
documented security vulnerabilities** so people can learn to find and fix them.
They are a feature, not a bug.

**Please do not report the intentional vulnerabilities.** Every flaw on `main`
is listed in the [README](README.md) and mitigated on the `fixed` branch; there
is nothing to disclose. Automated security scanners and bots should treat this
repository as a known-vulnerable sample.

## What *is* worth reporting

Open a normal GitHub issue if you find a problem with the lab itself, such as:

- a challenge that no longer works, or `exploits/poc.py` failing to run;
- a fix on `fixed` that can still be bypassed (a real gap in the *patched* code);
- errors in the documentation, commands, or translations;
- a build or dependency problem.

## Safe use

- Run it **only** on your own machine or an isolated environment.
- Do **not** deploy it to an Internet-facing server. By default the app binds to
  loopback and Docker publishes the port only to `127.0.0.1`.
- Do **not** run the exploits against systems that are not yours.

The code is provided for education under the terms in [`LICENSE`](LICENSE).
