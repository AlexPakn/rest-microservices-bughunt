"""Run the same regression suite against baseline and current service sources."""
import importlib.metadata
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def execute(label, source_root):
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    environment = dict(os.environ, BUGHUNT_SOURCE_ROOT=str(source_root))
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short",
         f"--junitxml=artifacts/{label}.xml"],
        cwd=ROOT, env=environment, text=True, capture_output=True, timeout=120,
    )
    (artifacts / f"{label}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    xml = ET.parse(artifacts / f"{label}.xml")
    counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    groups = {}
    for case in xml.iter("testcase"):
        kind = ("failed" if case.find("failure") is not None else
                "errors" if case.find("error") is not None else
                "skipped" if case.find("skipped") is not None else "passed")
        counts[kind] += 1
        match = re.search(r"test_(b\d\d)_", case.get("name", ""))
        group = match.group(1).upper() if match else "control / integration"
        groups.setdefault(group, dict.fromkeys(counts, 0))[kind] += 1
    print(f"{label}: {counts}", flush=True)
    return {"exit_code": result.returncode, "counts": counts, "groups": groups}


def main():
    baseline_sha = subprocess.check_output(
        ["git", "rev-parse", "baseline"], cwd=ROOT, text=True
    ).strip()
    with tempfile.TemporaryDirectory(prefix="rest-baseline-") as directory:
        source_root = Path(directory)
        for service in ("auth", "product", "order"):
            relative = f"{service}-service/main.py"
            target = source_root / relative
            target.parent.mkdir()
            target.write_bytes(subprocess.check_output(
                ["git", "show", f"baseline:{relative}"], cwd=ROOT
            ))
        baseline = execute("baseline", source_root)
    fixed = execute("fixed", ROOT)
    versions = {name: importlib.metadata.version(name)
                for name in ("fastapi", "uvicorn", "httpx", "pydantic", "pytest")}
    result = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_commit": baseline_sha,
        "python": platform.python_version(), "platform": platform.platform(),
        "dependencies": versions, "baseline": baseline, "fixed": fixed,
    }
    (ROOT / "artifacts/verification.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    rows = []
    for group, counts in fixed["groups"].items():
        previous = baseline["groups"][group]
        rows.append(f'| {group} | {previous["failed"]} | {previous["passed"]} | {counts["passed"]} |')
    text = f'''# Результати перевірки

Автоматично сформовано `scripts/verify.py`. Одні й ті самі тести виконано для
коду з Git-тега `baseline` та поточних файлів сервісів.

- Початковий commit: `{baseline_sha}`.
- Python: {result["python"]}; платформа: {result["platform"]}.
- Залежності: {", ".join(f"{name}=={version}" for name, version in versions.items())}.
- Початковий код: **{baseline["counts"]["failed"]} failed, {baseline["counts"]["passed"]} passed**.
- Виправлений код: **{fixed["counts"]["failed"]} failed, {fixed["counts"]["passed"]} passed**.

| Група | Падіння до | Успішні до | Успішні після |
|---|---:|---:|---:|
{chr(10).join(rows)}

Параметризовані випадки перевіряють різні прояви одного дефекту.
Додатковий інтеграційний тест перевіряє спільний сценарій трьох реальних ASGI-застосунків;
решта тестів сервісів використовують HTTP-заглушки залежностей.
Помилок підготовки тестів (pytest errors): {baseline["counts"]["errors"]} до,
{fixed["counts"]["errors"]} після.

Повні локальні протоколи: `artifacts/baseline.log`, `artifacts/fixed.log`;
машинозчитувані результати: однойменні XML та `artifacts/verification.json`.
Протоколи не додаються до Git. Цей підсумок зберігається у репозиторії.
Docker-запуск цим сценарієм не перевіряється.
'''
    (ROOT / "docs/TEST_RESULTS.md").write_text(text, encoding="utf-8")
    expected = (baseline["exit_code"] == 1 and baseline["counts"]["failed"] > 0
                and baseline["counts"]["errors"] == 0 and fixed["exit_code"] == 0)
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
