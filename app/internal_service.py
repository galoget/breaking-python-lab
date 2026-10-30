"""SIMULATED internal service (fake metadata) for the SSRF challenge.

Listens only on 127.0.0.1:8081. It is not reachable from outside the
container, but it is reachable from the vulnerable application, which runs
on the same host.
"""
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/latest/meta-data/")
def root():
    return "iam/credentials\n"


@app.route("/latest/meta-data/iam/credentials")
def creds():
    return jsonify(
        {
            "AccessKeyId": "AKIA-LAB-FAKE",
            "SecretAccessKey": "not-a-real-credential",
            "Flag": "FLAG{ssrf_internal_service}",
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8081)
