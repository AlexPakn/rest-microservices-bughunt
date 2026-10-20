"""Create the prepared PR chain using the same Git credential as HTTPS push.

No credential is printed, written to disk or passed in command-line arguments.
Only run this after explicitly choosing the destination repository.
"""
import argparse
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="GitHub owner/name")
    parser.add_argument("--default-branch", help="Optionally choose the repository landing branch")
    parser.add_argument("--check", action="store_true", help="Show GitHub Actions delivery status")
    args = parser.parse_args()
    if len(args.repository.split("/")) != 2 or any(
        not part or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-" for c in part)
        for part in args.repository.split("/")
    ):
        parser.error("Expected a GitHub owner/name")
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", "credential", "fill"],
        input=f"protocol=https\nhost=github.com\npath={args.repository}.git\n\n",
        text=True, capture_output=True, cwd=ROOT, timeout=120,
    )
    if result.returncode:
        raise RuntimeError("Git credential manager did not provide a credential")
    credential = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    token = credential.get("password")
    if not token:
        raise RuntimeError("No HTTPS credential available; sign in through Git first")

    def request(endpoint="", body=None, method=None):
        req = urllib.request.Request(
            f"https://api.github.com/repos/{args.repository}" + (f"/{endpoint}" if endpoint else ""),
            data=None if body is None else json.dumps(body).encode("utf-8"),
            method=method,
            headers={"Authorization": f"Bearer {token}",
                     "Accept": "application/vnd.github+json",
                     "Content-Type": "application/json", "User-Agent": "rest-microservices-bughunt",
                     "X-GitHub-Api-Version": "2022-11-28"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            message = json.loads(error.read().decode("utf-8")).get("message", "request rejected")
            raise RuntimeError(f"GitHub HTTP {error.code}: {message}") from None

    existing = request("pulls?state=all&per_page=100")
    plan = json.loads((ROOT / "docs/pr-plan.json").read_text(encoding="utf-8"))
    links = []
    output = ROOT / "artifacts/pull-requests.json"
    output.parent.mkdir(exist_ok=True)
    for item in plan:
        pull = next((p for p in existing
                     if p["head"]["ref"] == item["branch"] and p["base"]["ref"] == item["base"]), None)
        if pull is None:
            pull = request("pulls", {"head": item["branch"], "base": item["base"],
                                     "title": item["title"],
                                     "body": (ROOT / item["body_file"]).read_text(encoding="utf-8"),
                                     "draft": False})
        links.append({"id": item["id"], "number": pull["number"], "url": pull["html_url"],
                      "head": item["branch"], "base": item["base"]})
        output.write_text(json.dumps(links, indent=2), encoding="utf-8")
        print(f'{item["id"]}: {pull["html_url"]}', flush=True)
    repository = request()
    if args.default_branch and repository["default_branch"] != args.default_branch:
        repository = request(body={"default_branch": args.default_branch}, method="PATCH")
    delivery = {"repository": repository["html_url"], "default_branch": repository["default_branch"],
                "visibility": repository["visibility"], "pull_requests": links}
    if args.check:
        runs = request("actions/runs?branch=solution&per_page=5")["workflow_runs"]
        delivery["actions"] = [{key: run.get(key) for key in
                                ("id", "head_sha", "status", "conclusion", "html_url")} for run in runs]
    (ROOT / "artifacts/github-delivery.json").write_text(json.dumps(delivery, indent=2), encoding="utf-8")
    print(f'Default branch: {delivery["default_branch"]}')
    for run in delivery.get("actions", []):
        print(f'Actions: {run["status"]} / {run["conclusion"]} / {run["html_url"]}')


if __name__ == "__main__":
    main()
