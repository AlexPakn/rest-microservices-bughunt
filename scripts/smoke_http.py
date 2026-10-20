"""Verify real HTTP interactions. With --start, run and stop local services."""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def check(response, expected):
    if response.status_code != expected:
        raise AssertionError(f"Expected HTTP {expected}, got HTTP {response.status_code}")
    return response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", action="store_true")
    args = parser.parse_args()
    processes = []
    try:
        if args.start:
            # Refuse occupied ports so requests cannot hit an unrelated app.
            import socket
            for port in (8001, 8002, 8003):
                with socket.socket() as probe:
                    probe.bind(("127.0.0.1", port))
            for service, port in (("auth", 8001), ("product", 8002), ("order", 8003)):
                environment = dict(os.environ,
                                   AUTH_URL="http://127.0.0.1:8001",
                                   PRODUCT_URL="http://127.0.0.1:8002")
                processes.append(subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "main:app", "--app-dir",
                     str(ROOT / f"{service}-service"), "--host", "127.0.0.1",
                     "--port", str(port), "--no-access-log"],
                    env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                ))
        with httpx.Client(timeout=5, trust_env=False) as client:
            for port in (8001, 8002, 8003):
                deadline = time.monotonic() + 15
                while True:
                    try:
                        check(client.get(f"http://127.0.0.1:{port}/openapi.json"), 200)
                        break
                    except httpx.ConnectError:
                        if time.monotonic() >= deadline:
                            raise RuntimeError(f"Service on port {port} did not start") from None
                        time.sleep(0.2)
            auth, product, order = [f"http://127.0.0.1:{port}" for port in (8001, 8002, 8003)]
            alice = check(client.post(f"{auth}/login", json={
                "email": "alice@example.com", "password": "alice123"}), 200).json()
            headers = {"Authorization": f'Bearer {alice["access_token"]}'}
            assert check(client.get(f"{auth}/whoami", headers=headers), 200).json()["user_id"] == 1
            check(client.get(f"{auth}/login"), 405)
            check(client.post(f"{auth}/login", json={
                "email": "alice@example.com", "password": "wrong"}), 401)
            check(client.get(f"{auth}/whoami", headers={"Authorization": "Bearer forged"}), 401)
            assert isinstance(check(client.get(f"{product}/products/100"), 200).json()["price"], float)
            check(client.get(f"{product}/products/9999"), 404)
            check(client.post(f"{order}/orders", json={"productId": 100, "qty": 1}), 401)
            for payload, expected in (({"productId": 100, "qty": 0}, 422),
                                      ({"productId": 9999, "qty": 1}, 404),
                                      ({"productId": 101, "qty": 1}, 409)):
                check(client.post(f"{order}/orders", headers=headers, json=payload), expected)
            created = check(client.post(f"{order}/orders", headers=headers,
                                         json={"productId": 100, "qty": 1}), 201).json()
            assert created["user_id"] == 1
            bob = check(client.post(f"{auth}/login", json={
                "email": "bob@example.com", "password": "bob123"}), 200).json()
            bob_headers = {"Authorization": f'Bearer {bob["access_token"]}'}
            assert check(client.get(f"{order}/orders", headers=bob_headers), 200).json() == {"orders": []}
            own = check(client.get(f"{order}/orders", headers=headers), 200).json()["orders"]
            assert any(item["order_id"] == created["order_id"] for item in own)
            check(client.get(f"{order}/orders"), 401)
        print("HTTP smoke: PASS (three services, authentication, validation, ownership)")
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
