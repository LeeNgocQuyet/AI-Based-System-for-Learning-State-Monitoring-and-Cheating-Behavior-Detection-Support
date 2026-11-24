#!/usr/bin/env python3
"""
benchmark_api.py — Backend Quality v1.4
Concurrent API benchmark: đo latency/throughput/error rate trên nhiều session đồng thời.

Cách dùng (từ thư mục backend/):
    python scripts/issue_user_token.py --email learner.one@example.edu
    python scripts/benchmark_api.py --token "<TOKEN>" --concurrent-sessions 10 --rounds 5

Kết quả lưu tại: benchmark-results/backend_benchmark_report.json
                  benchmark-results/backend_benchmark_samples.csv
"""
import argparse
import asyncio
import csv
import json
import os
import platform
import statistics
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx

try:
    import psutil
except ImportError:
    psutil = None


def pct(values: list[float], p: float) -> float:
    """Tính percentile p (0–100) của danh sách đã có."""
    if not values:
        return 0.0
    v = sorted(values)
    return v[min(len(v) - 1, round((p / 100) * (len(v) - 1)))]


async def run(a: argparse.Namespace) -> int:
    headers = {"Authorization": f"Bearer {a.token}"}
    limits = httpx.Limits(max_connections=max(a.concurrent_sessions * 3, 10))
    rows: list[dict] = []
    errors: list[dict] = []
    session_ids: list[str] = []

    async with httpx.AsyncClient(
        base_url=a.base_url.rstrip("/"),
        headers=headers,
        timeout=a.timeout,
        limits=limits,
    ) as client:
        # --- Tạo N session trước khi bắt đầu đo ---
        print(f"[benchmark] Tạo {a.concurrent_sessions} session(s)...")
        for i in range(a.concurrent_sessions):
            r = await client.post("/api/v1/sessions", json={"session_type": "LEARNING"})
            if r.status_code != 201:
                raise SystemExit(f"Tạo session #{i+1} thất bại: {r.status_code} {r.text}")
            session_ids.append(r.json()["data"]["session_id"])
        print(f"[benchmark] Tạo xong. Bắt đầu {a.rounds} round(s)...")

        async def req(op: str, method: str, path: str, payload: dict | None = None) -> None:
            t = time.perf_counter()
            try:
                r = await client.request(method, path, json=payload)
                latency_ms = round((time.perf_counter() - t) * 1000, 3)
                ok = r.status_code in (200, 201)
                rows.append({"operation": op, "status_code": r.status_code, "latency_ms": latency_ms, "ok": ok})
                if not ok:
                    errors.append({"operation": op, "status": r.status_code, "body": r.text[:300]})
            except Exception as exc:
                latency_ms = round((time.perf_counter() - t) * 1000, 3)
                rows.append({"operation": op, "status_code": 0, "latency_ms": latency_ms, "ok": False})
                errors.append({"operation": op, "error": repr(exc)})

        process = psutil.Process() if psutil else None
        if process:
            process.cpu_percent(None)  # Khởi động sampler (giá trị đầu không dùng)

        resource_samples: list[dict] = []
        start = time.perf_counter()

        for n in range(a.rounds):
            jobs = []
            for sid in session_ids:
                event_payload = {
                    "event_id": str(uuid.uuid4()),
                    "schema_version": "1.0.0",
                    "session_id": sid,
                    "event_type": "TAB_HIDDEN",
                    "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "source": "BROWSER",
                    "metadata": {"benchmark_round": n + 1},
                }
                jobs += [
                    req("event_ingest", "POST", f"/api/v1/sessions/{sid}/events", event_payload),
                    req("event_list", "GET", f"/api/v1/sessions/{sid}/events?page=1&page_size=100"),
                    req("session_report", "GET", f"/api/v1/sessions/{sid}/report"),
                ]
            await asyncio.gather(*jobs)
            if process:
                resource_samples.append({
                    "round": n + 1,
                    "client_cpu_percent": process.cpu_percent(None),
                    "client_rss_mb": round(process.memory_info().rss / 1_048_576, 2),
                })
            print(f"[benchmark] Round {n+1}/{a.rounds} hoàn thành.")

        elapsed = time.perf_counter() - start

    # --- Tổng hợp kết quả ---
    lat = [x["latency_ms"] for x in rows]
    ok_count = sum(x["ok"] for x in rows)
    total = len(rows)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target": a.base_url,
        "machine": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "processor": platform.processor() or "unknown",
            "logical_cpu_count": os.cpu_count(),
            "psutil_available": bool(psutil),
        },
        "configuration": {
            "concurrent_sessions": a.concurrent_sessions,
            "rounds": a.rounds,
            "requests_per_session_per_round": 3,  # event_ingest + event_list + session_report
            "total_requests": total,
        },
        "results": {
            "success": ok_count,
            "failed": total - ok_count,
            "error_rate_percent": round((total - ok_count) / max(total, 1) * 100, 3),
            "throughput_req_s": round(ok_count / max(elapsed, 1e-9), 3),
            "elapsed_seconds": round(elapsed, 3),
            "latency_ms": {
                "mean": round(statistics.mean(lat), 3) if lat else 0,
                "median": round(statistics.median(lat), 3) if lat else 0,
                "p95": pct(lat, 95),
                "p99": pct(lat, 99),
                "max": max(lat, default=0),
            },
        },
        "resource_samples": resource_samples,
        "notes": {
            "resource_scope": (
                "CPU/RSS là của tiến trình benchmark client, KHÔNG phải server "
                "trừ khi chạy trên cùng máy. Dùng 'docker stats --no-stream' "
                "để đo resource phía server khi chạy trong container."
            ),
            "fps_note": (
                "FPS của AI model do AI Core (Quyết) đo riêng: "
                "frames_processed / elapsed_time, không phải API latency."
            ),
        },
        "errors": errors[:100],
    }

    # --- Ghi file kết quả ---
    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "backend_benchmark_report.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    csv_path = out / "backend_benchmark_samples.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["operation", "status_code", "latency_ms", "ok"])
        writer.writeheader()
        writer.writerows(rows)

    print("\n" + "=" * 60)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("=" * 60)
    print(f"\n[benchmark] Báo cáo JSON : {json_path.resolve()}")
    print(f"[benchmark] Mẫu CSV      : {csv_path.resolve()}")

    return 0 if not errors else 1


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Concurrent API benchmark cho Backend v1.4",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--base-url", default="http://127.0.0.1:8000", help="Base URL của API (default: http://127.0.0.1:8000)")
    p.add_argument("--token", required=True, help="Learner JWT access token (phát bằng issue_user_token.py)")
    p.add_argument("--concurrent-sessions", type=int, default=5, help="Số phiên đồng thời (default: 5)")
    p.add_argument("--rounds", type=int, default=3, help="Số vòng lặp đo (default: 3)")
    p.add_argument("--timeout", type=float, default=15.0, help="Timeout mỗi request tính bằng giây (default: 15)")
    p.add_argument("--output-dir", default="benchmark-results", help="Thư mục lưu kết quả (default: benchmark-results)")
    return p


if __name__ == "__main__":
    parser = _build_parser()
    args = parser.parse_args()
    if args.concurrent_sessions < 1:
        parser.error("--concurrent-sessions phải >= 1")
    if args.rounds < 1:
        parser.error("--rounds phải >= 1")
    if args.timeout <= 0:
        parser.error("--timeout phải > 0")
    raise SystemExit(asyncio.run(run(args)))
