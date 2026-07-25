"""Бенчмарк latency всех основных API-эндпоинтов.

Считывает ``X-Process-Time-Ms`` (серверное время) и wall-clock RTT.
Требует: запущенный API + ``scripts/seed_demo_data.py``.

Пример:
  docker compose exec app python scripts/benchmark_api.py
  python scripts/benchmark_api.py --base-url http://localhost:8000 --runs 20
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable

import requests

DEFAULT_BASE = "http://localhost:8000"
DEMO_LOGIN = "demo"
DEMO_PASSWORD = "demo12345"
TIMEZONE = "Europe/Moscow"


@dataclass
class Sample:
    name: str
    status: int
    wall_ms: float
    process_ms: float | None


@dataclass
class EndpointResult:
    name: str
    method: str
    path: str
    samples: list[Sample] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.samples) and all(200 <= s.status < 400 for s in self.samples)

    def _values(self, attr: str) -> list[float]:
        vals: list[float] = []
        for s in self.samples:
            v = getattr(s, attr)
            if v is not None:
                vals.append(float(v))
        return vals

    def summary(self) -> dict[str, Any]:
        wall = self._values("wall_ms")
        proc = self._values("process_ms")
        return {
            "name": self.name,
            "method": self.method,
            "path": self.path,
            "ok": self.ok,
            "n": len(self.samples),
            "wall_ms": _stats(wall),
            "process_ms": _stats(proc) if proc else None,
            "last_status": self.samples[-1].status if self.samples else None,
        }


def _stats(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    values = sorted(values)
    p95_idx = min(len(values) - 1, int(round(0.95 * (len(values) - 1))))
    return {
        "min": round(values[0], 2),
        "median": round(statistics.median(values), 2),
        "mean": round(statistics.mean(values), 2),
        "p95": round(values[p95_idx], 2),
        "max": round(values[-1], 2),
    }


class ApiClient:
    def __init__(self, base_url: str):
        self.base = base_url.rstrip("/")
        self.session = requests.Session()
        self.token: str | None = None

    def _headers(self) -> dict[str, str]:
        h = {"X-Timezone": TIMEZONE, "Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        params: dict | None = None,
    ) -> Sample:
        url = f"{self.base}{path}"
        started = time.perf_counter()
        resp = self.session.request(
            method,
            url,
            headers=self._headers(),
            json=json_body,
            params=params,
            timeout=60,
        )
        wall_ms = (time.perf_counter() - started) * 1000.0
        process_ms = None
        raw = resp.headers.get("X-Process-Time-Ms")
        if raw:
            try:
                process_ms = float(raw)
            except ValueError:
                process_ms = None
        return Sample(
            name=f"{method} {path}",
            status=resp.status_code,
            wall_ms=wall_ms,
            process_ms=process_ms,
        )

    def login(self, login: str, password: str) -> dict:
        resp = self.session.post(
            f"{self.base}/v1/auth/login",
            headers=self._headers(),
            json={"login": login, "password": password},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data["access_token"]
        return data

    def get_json(self, path: str, params: dict | None = None) -> Any:
        resp = self.session.get(
            f"{self.base}{path}",
            headers=self._headers(),
            params=params,
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()


def _run_endpoint(
    client: ApiClient,
    name: str,
    method: str,
    path: str,
    runs: int,
    *,
    json_body: dict | None = None,
    params: dict | None = None,
    setup: Callable[[], None] | None = None,
) -> EndpointResult:
    result = EndpointResult(name=name, method=method, path=path)
    for _ in range(runs):
        if setup:
            setup()
        sample = client.request(method, path, json_body=json_body, params=params)
        result.samples.append(sample)
    return result


def benchmark(base_url: str, runs: int, login: str, password: str) -> list[EndpointResult]:
    client = ApiClient(base_url)
    results: list[EndpointResult] = []

    # health (без auth)
    results.append(_run_endpoint(client, "health", "GET", "/health", runs))

    # auth
    results.append(
        _run_endpoint(
            client,
            "auth.login",
            "POST",
            "/v1/auth/login",
            runs,
            json_body={"login": login, "password": password},
        )
    )

    client.login(login, password)

    today = date.today()
    month_start = today.replace(day=1).isoformat()
    month_end = today.isoformat()
    half_year_start = (today - timedelta(days=180)).isoformat()

    accounts = client.get_json("/v1/accounts")["accounts"]
    if not accounts:
        raise RuntimeError("У demo нет счетов — сначала seed_demo_data.py")
    account_id = accounts[0]["id"]

    categories = client.get_json("/v1/categories", params={"include": "children"})["categories"]
    expense_cat = next((c for c in categories if c["type"] == "expense" and not c.get("is_custom")), None)
    category_id = expense_cat["id"] if expense_cat else None

    txs = client.get_json(
        "/v1/transactions",
        params={"from": half_year_start, "to": month_end},
    )["transactions"]
    if not txs:
        raise RuntimeError("Нет транзакций для бенчмарка detail/patch")
    tx_id = txs[0]["id"]
    qr_tx = next((t for t in txs if t.get("source") == "qr_receipt" and t.get("items")), None)
    item_id = None
    if qr_tx and qr_tx["items"]:
        item_id = qr_tx["items"][0]["id"]
        # для patch item нужен detail с category_id
        detail = client.get_json(f"/v1/transactions/{qr_tx['id']}")
        items = detail.get("transaction", {}).get("items") or []
        if items:
            item_id = items[0]["id"]
            if items[0].get("category_id"):
                category_id = items[0]["category_id"]
            elif category_id is None and categories:
                category_id = categories[0]["id"]

    results.append(_run_endpoint(client, "accounts.list", "GET", "/v1/accounts", runs))
    results.append(
        _run_endpoint(
            client,
            "categories.list",
            "GET",
            "/v1/categories",
            runs,
            params={"include": "children"},
        )
    )
    results.append(
        _run_endpoint(
            client,
            "transactions.list.month",
            "GET",
            "/v1/transactions",
            runs,
            params={"from": month_start, "to": month_end},
        )
    )
    results.append(
        _run_endpoint(
            client,
            "transactions.list.6m",
            "GET",
            "/v1/transactions",
            runs,
            params={"from": half_year_start, "to": month_end},
        )
    )
    results.append(
        _run_endpoint(
            client,
            "transactions.list.filtered",
            "GET",
            "/v1/transactions",
            runs,
            params={
                "from": half_year_start,
                "to": month_end,
                "type": "expense",
                "account_id": account_id,
            },
        )
    )
    results.append(
        _run_endpoint(
            client,
            "transactions.list.page",
            "GET",
            "/v1/transactions",
            runs,
            params={
                "from": half_year_start,
                "to": month_end,
                "limit": "20",
                "offset": "0",
            },
        )
    )
    results.append(
        _run_endpoint(
            client,
            "transactions.detail",
            "GET",
            f"/v1/transactions/{tx_id}",
            runs,
        )
    )
    results.append(
        _run_endpoint(
            client,
            "stats.month",
            "GET",
            "/v1/stats",
            runs,
            params={"from": month_start, "to": month_end},
        )
    )
    results.append(
        _run_endpoint(
            client,
            "stats.6m",
            "GET",
            "/v1/stats",
            runs,
            params={"from": half_year_start, "to": month_end},
        )
    )

    # Мутации create + cleanup
    created_ids: list[str] = []
    create_result = EndpointResult(
        name="transactions.create",
        method="POST",
        path="/v1/transactions",
    )
    for _ in range(runs):
        body = {
            "account_id": account_id,
            "type": "expense",
            "amount": 123_00,
            "currency": "RUB",
            "occurred_at": f"{today.isoformat()}T12:00:00",
            "category_id": category_id,
            "comment": "benchmark",
        }
        started = time.perf_counter()
        resp = client.session.post(
            f"{client.base}/v1/transactions",
            headers=client._headers(),
            json=body,
            timeout=60,
        )
        wall_ms = (time.perf_counter() - started) * 1000.0
        process_ms = None
        raw = resp.headers.get("X-Process-Time-Ms")
        if raw:
            try:
                process_ms = float(raw)
            except ValueError:
                pass
        create_result.samples.append(
            Sample("transactions.create", resp.status_code, wall_ms, process_ms)
        )
        if resp.ok:
            tid = resp.json()["transaction"]["id"]
            created_ids.append(tid)
            client.request("DELETE", f"/v1/transactions/{tid}")
    results.append(create_result)

    if category_id and item_id and qr_tx:
        results.append(
            _run_endpoint(
                client,
                "transactions.patch_item",
                "PATCH",
                f"/v1/transactions/{qr_tx['id']}/items/{item_id}",
                min(runs, 5),
                json_body={"category_id": category_id},
            )
        )

    # cleanup leftover
    for tid in created_ids:
        try:
            client.request("DELETE", f"/v1/transactions/{tid}")
        except Exception:
            pass

    return results


def _print_table(results: list[EndpointResult]) -> None:
    print()
    print(f"{'endpoint':<32} {'ok':<4} {'proc p50':>10} {'proc p95':>10} {'wall p50':>10} {'wall p95':>10}")
    print("-" * 82)
    for r in results:
        s = r.summary()
        proc = s["process_ms"] or {}
        wall = s["wall_ms"] or {}
        print(
            f"{s['name']:<32} "
            f"{'yes' if s['ok'] else 'NO':<4} "
            f"{proc.get('median', float('nan')):>10.1f} "
            f"{proc.get('p95', float('nan')):>10.1f} "
            f"{wall.get('median', float('nan')):>10.1f} "
            f"{wall.get('p95', float('nan')):>10.1f}"
        )
    print()
    print("proc = X-Process-Time-Ms (сервер), wall = RTT клиента. Все значения в мс.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Бенчмарк API Finance Manager")
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--runs", type=int, default=15, help="Число прогонов на эндпоинт")
    parser.add_argument("--login", default=DEMO_LOGIN)
    parser.add_argument("--password", default=DEMO_PASSWORD)
    parser.add_argument("--json", type=Path, help="Сохранить полный отчёт в JSON")
    args = parser.parse_args()

    # Внутри docker-сети localhost:8000 — сам uvicorn
    base = args.base_url
    try:
        health = requests.get(f"{base.rstrip('/')}/health", timeout=5)
        health.raise_for_status()
    except Exception as exc:
        # fallback: если скрипт внутри контейнера app, uvicorn слушает 0.0.0.0:8000
        print(f"Не удалось достучаться до {base}: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Бенчмарк {base} × {args.runs} runs, user={args.login}")
    results = benchmark(base, args.runs, args.login, args.password)
    _print_table(results)

    slow = []
    for r in results:
        s = r.summary()
        proc = s.get("process_ms") or {}
        if proc.get("p95", 0) >= 100:
            slow.append((s["name"], proc["p95"]))
    if slow:
        print("Медленные (process p95 ≥ 100 мс):")
        for name, p95 in sorted(slow, key=lambda x: -x[1]):
            print(f"  {name}: p95={p95:.1f} ms")
    else:
        print("Все эндпоинты: process p95 < 100 мс (на текущем объёме данных).")

    if args.json:
        payload = {
            "base_url": base,
            "runs": args.runs,
            "results": [r.summary() for r in results],
        }
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Отчёт: {args.json}")


if __name__ == "__main__":
    main()
