"""Capture actual pytest output and HTML pages for browser screenshots."""
import html
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/evidence/pytest"
CASES = [
    ("B01", "POST login", "tests/test_auth.py::test_b01_login_accepts_json_post"),
    ("B02", "Invalid credentials", "tests/test_auth.py::test_b02_bad_credentials_are_unauthorized"),
    ("B03", "Authorization header", "tests/test_auth.py::test_b03_whoami_reads_authorization_header"),
    ("B04", "Missing token", "tests/test_auth.py::test_b04_missing_token_returns_401"),
    ("B05", "Forged token", "tests/test_auth.py::test_b05_unissued_or_malformed_token_rejected[Bearer fake-token-for-alice@example.com]"),
    ("B06", "Unknown product", "tests/test_products.py::test_b06_unknown_product_returns_404"),
    ("B07", "Product schema", "tests/test_products.py::test_b07_product_price_is_json_number"),
    ("B08", "Order authentication", "tests/test_orders.py::test_b08_order_requires_authorization"),
    ("B09", "Order validation", "tests/test_orders.py::test_b09_invalid_order_payload_rejected[payload0]"),
    ("B10", "Product existence", "tests/test_orders.py::test_b10_unknown_product_cannot_be_ordered"),
    ("B11", "Stock check", "tests/test_orders.py::test_b11_insufficient_stock_rejected[0-1]"),
    ("B12", "Dependency failure", "tests/test_orders.py::test_b12_dependency_transport_failure_is_explicit[ConnectError-502-auth]"),
    ("B13", "Order privacy", "tests/test_orders.py::test_b13_order_list_requires_authentication"),
]


def capture(identifier, title, arguments, source_root, revision, expected):
    environment = dict(os.environ, BUGHUNT_SOURCE_ROOT=str(source_root), PYTHONIOENCODING="utf-8")
    options = ["-q", "--color=no", "-p", "no:warnings"]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *arguments, *options], cwd=ROOT,
        env=environment, capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    if result.returncode != expected:
        raise RuntimeError(f"Unexpected pytest exit for {identifier}: {result.returncode}")
    output = result.stdout + result.stderr
    (OUTPUT / f"{identifier}.txt").write_text(output, encoding="utf-8")
    command = subprocess.list2cmdline(["python", "-m", "pytest", *arguments, *options])
    color = "#16835b" if expected == 0 else "#c43131"
    page = f'''<!doctype html>
<html lang="uk"><meta charset="utf-8"><title>pytest — {identifier}</title>
<style>
* {{box-sizing:border-box}} body {{margin:0;padding:28px;background:#edf1f5;color:#172333;
font-family:Arial,sans-serif}} article {{background:#fff;border:1px solid #d5dce5;border-radius:12px;
overflow:hidden}} header {{padding:22px 26px;border-bottom:1px solid #dce2ea}}
h1 {{margin:0 0 10px;font-size:25px}} p {{margin:6px 0;font-size:15px;color:#455366}}
.status {{color:{color};font-weight:bold}} .command {{padding:18px 26px;background:#f2f5f8;
font:14px Consolas,monospace;overflow-wrap:anywhere}}
pre {{margin:0;padding:22px 26px;white-space:pre-wrap;overflow-wrap:anywhere;
font:15px/1.55 Consolas,"Courier New",monospace;color:#172333}}
footer {{padding:15px 26px;border-top:1px solid #dce2ea;font-size:13px;color:#536278}}
</style><article><header><h1>{html.escape(identifier)} · {html.escape(title)}</h1>
<p>Код сервісів: <strong>{html.escape(revision)}</strong></p>
<p class="status">pytest exit code: {result.returncode}</p></header>
<div class="command">{html.escape(command)}</div>
<pre>{html.escape(output)}</pre>
<footer>Знімок HTML-звіту з дослівним stdout/stderr реального запуску pytest.
Початкові сервіси завантажуються через BUGHUNT_SOURCE_ROOT; тести в обох версіях однакові.</footer>
</article></html>'''
    (OUTPUT / f"{identifier}.html").write_text(page, encoding="utf-8")
    print(f"{identifier}: captured (exit {result.returncode})", flush=True)
    return {"id": identifier, "title": title, "command": command,
            "service_revision": revision, "exit_code": result.returncode,
            "output": f"{identifier}.txt", "page": f"{identifier}.html",
            "screenshot": f"../../screenshots/pytest-{identifier}.png"}


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    baseline_sha = subprocess.check_output(["git", "rev-parse", "baseline"], cwd=ROOT, text=True).strip()
    manifest = []
    with tempfile.TemporaryDirectory(prefix="pytest-evidence-") as directory:
        baseline_root = Path(directory)
        for service in ("auth", "product", "order"):
            relative = f"{service}-service/main.py"
            target = baseline_root / relative
            target.parent.mkdir()
            target.write_bytes(subprocess.check_output(["git", "show", f"baseline:{relative}"], cwd=ROOT))
        for identifier, title, node in CASES:
            traceback = "--tb=line" if identifier == "B12" else "--tb=short"
            manifest.append(capture(identifier, title, [node, traceback], baseline_root,
                                    f"baseline ({baseline_sha[:7]})", 1))
        manifest.append(capture("baseline", "Before fixes: full suite",
                                ["--tb=no", "--no-summary"], baseline_root,
                                f"baseline ({baseline_sha[:7]})", 1))
    manifest.append(capture("fixed", "After fixes: full suite",
                            ["--tb=short"], ROOT, "solution (B01–B13)", 0))
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
