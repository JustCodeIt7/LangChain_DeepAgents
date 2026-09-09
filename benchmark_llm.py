#!/usr/bin/env python3
"""
benchmark_llm.py — Benchmark LLM inference performance on any OpenAI-compatible
server (LM Studio, vLLM, Ollama, llama.cpp server, ...).

Measures:
  * Sequential: time-to-first-token (TTFT), end-to-end latency, tokens/s
  * Concurrent: how the engine scales under N parallel requests (the load
    profile of sub-agents) — aggregate throughput, per-request slowdown,
    p50/p95/p99 latency and TTFT, error rate
  * Optional concurrency sweep: throughput scaling table across levels

Only dependency: requests.

Examples:
  # Quick benchmark of the default LM Studio endpoint
  python benchmark_llm.py

  # Different model / server
  python benchmark_llm.py --base-url http://localhost:11434/v1 --model llama3.2

  # Sub-agent style load: 8 in flight, 32 total requests
  python benchmark_llm.py --concurrency 8 --concurrent-requests 32

  # Sweep concurrency 1,2,4,8,16 to see how throughput scales
  python benchmark_llm.py --sweep 1,2,4,8,16

  # Save full results as JSON
  python benchmark_llm.py --json results.json
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from typing import Any

import requests

DEFAULT_BASE_URL = "http://192.168.0.39:1234/v1"
DEFAULT_MODEL = "qwen/qwen3.8-27b"
DEFAULT_PROMPT = (
    "Explain, step by step, how the attention mechanism in a transformer "
    "works, including the roles of queries, keys and values."
)

_thread_local = threading.local()


def _session() -> requests.Session:
    """One requests.Session per worker thread (connection reuse)."""
    s = getattr(_thread_local, "session", None)
    if s is None:
        s = requests.Session()
        _thread_local.session = s
    return s


@dataclass
class RequestResult:
    ok: bool
    error: str = ""
    status: int = 0
    ttft_ms: float = 0.0          # time to first token
    total_ms: float = 0.0         # end-to-end latency
    tokens: int = 0               # completion tokens (usage if available, else chunk count)
    chunks: int = 0
    itl_ms: list[float] = field(default_factory=list)  # inter-token latencies

    @property
    def tok_per_s(self) -> float:
        return self.tokens / (self.total_ms / 1000.0) if self.total_ms > 0 else 0.0


def run_one(
    base_url: str,
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
    timeout: float,
    stream: bool,
    include_usage: bool,
) -> RequestResult:
    """Run a single chat completion and measure it."""
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream,
    }
    if stream and include_usage:
        payload["stream_options"] = {"include_usage": True}

    url = base_url.rstrip("/") + "/chat/completions"
    t0 = time.perf_counter()
    res = RequestResult(ok=False)
    try:
        r = _session().post(url, json=payload, stream=stream, timeout=(10, timeout))
        res.status = r.status_code
        if r.status_code != 200:
            res.error = f"HTTP {r.status_code}: {r.text[:300]}"
            res.total_ms = (time.perf_counter() - t0) * 1000
            return res

        if not stream:
            data = r.json()
            res.total_ms = (time.perf_counter() - t0) * 1000
            res.ttft_ms = res.total_ms
            res.tokens = (data.get("usage") or {}).get("completion_tokens") or 1
            res.ok = True
            return res

        first = last = None
        for raw in r.iter_lines(decode_unicode=True):
            if not raw or raw.startswith(":") or not raw.startswith("data:"):
                continue
            data_str = raw[5:].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                continue
            usage = chunk.get("usage")
            if usage and usage.get("completion_tokens") is not None:
                res.tokens = usage["completion_tokens"]
            choices = chunk.get("choices") or []
            if choices:
                delta = choices[0].get("delta") or {}
                if delta.get("content"):
                    now = time.perf_counter()
                    if first is None:
                        first = now
                    else:
                        res.itl_ms.append((now - last) * 1000)
                    last = now
                    res.chunks += 1

        res.total_ms = (time.perf_counter() - t0) * 1000
        if first is not None:
            res.ttft_ms = (first - t0) * 1000
        if res.tokens == 0:
            res.tokens = res.chunks  # fallback: ~1 chunk per token
        res.ok = res.chunks > 0 or res.tokens > 0
        if not res.ok:
            res.error = "no tokens received"
    except requests.exceptions.Timeout:
        res.total_ms = (time.perf_counter() - t0) * 1000
        res.error = f"timeout after {timeout:.0f}s"
    except requests.exceptions.ConnectionError as e:
        res.total_ms = (time.perf_counter() - t0) * 1000
        res.error = f"connection error: {e}"
    except Exception as e:  # noqa: BLE001
        res.total_ms = (time.perf_counter() - t0) * 1000
        res.error = f"{type(e).__name__}: {e}"
    return res


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    if len(vals) == 1:
        return vals[0]
    k = (len(vals) - 1) * (p / 100.0)
    f, c = math.floor(k), math.ceil(k)
    if f == c:
        return vals[int(k)]
    return vals[f] + (vals[c] - vals[f]) * (k - f)


def stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"mean": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": statistics.fmean(values),
        "p50": percentile(values, 50),
        "p95": percentile(values, 95),
        "p99": percentile(values, 99),
        "min": min(values),
        "max": max(values),
    }


def run_phase(
    base_url: str,
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
    timeout: float,
    stream: bool,
    include_usage: bool,
    concurrency: int,
    total_requests: int,
    label: str,
) -> dict[str, Any]:
    """Fire total_requests with at most `concurrency` in flight; measure everything."""
    t0 = time.perf_counter()
    results: list[RequestResult] = []
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futs = [
            pool.submit(
                run_one, base_url, model, prompt, max_tokens,
                temperature, timeout, stream, include_usage,
            )
            for _ in range(total_requests)
        ]
        for f in as_completed(futs):
            results.append(f.result())
    wall = time.perf_counter() - t0

    ok = [r for r in results if r.ok]
    total_tokens = sum(r.tokens for r in ok)
    return {
        "label": label,
        "concurrency": concurrency,
        "requests": len(results),
        "succeeded": len(ok),
        "failed": len(results) - len(ok),
        "errors": [r.error for r in results if not r.ok][:5],
        "wall_s": wall,
        "total_tokens": total_tokens,
        "aggregate_tps": total_tokens / wall if wall > 0 else 0.0,
        "ttft_ms": stats([r.ttft_ms for r in ok]),
        "latency_ms": stats([r.total_ms for r in ok]),
        "tok_per_s": stats([r.tok_per_s for r in ok]),
        "itl_ms": stats([x for r in ok for x in r.itl_ms]),
        "results": [asdict(r) for r in results],
    }


def list_models(base_url: str) -> tuple[list[str] | None, str]:
    try:
        r = _session().get(base_url.rstrip("/") + "/models", timeout=10)
        r.raise_for_status()
        return [m.get("id") for m in r.json().get("data", [])], ""
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"


def fmt_stats(s: dict[str, float]) -> str:
    return f"mean {s['mean']:.0f}  p50 {s['p50']:.0f}  p95 {s['p95']:.0f}  p99 {s['p99']:.0f}"


def print_phase(p: dict[str, Any], show_per_request: bool) -> None:
    print(f"\n--- {p['label']} ---")
    if show_per_request:
        header = (f"  {'req':>4}  {'ttft(ms)':>9}  {'latency(s)':>10}  "
                  f"{'tokens':>6}  {'tok/s':>6}  status")
        print(header)
        for i, r in enumerate(p["results"], 1):
            if r["ok"]:
                tps = r["tokens"] / (r["total_ms"] / 1000)
                print(f"  {i:>4}  {r['ttft_ms']:>9.0f}  {r['total_ms'] / 1000:>10.2f}  "
                      f"{r['tokens']:>6}  {tps:>6.1f}  ok")
            else:
                print(f"  {i:>4}  {'-':>9}  {'-':>10}  {'-':>6}  {'-':>6}  FAIL: {r['error'][:60]}")
    print(f"  wall time      : {p['wall_s']:.1f} s")
    print(f"  succeeded      : {p['succeeded']}/{p['requests']}")
    if p["errors"]:
        for e in p["errors"]:
            print(f"  error          : {e[:120]}")
    print(f"  total tokens   : {p['total_tokens']}")
    print(f"  aggregate tok/s: {p['aggregate_tps']:.1f}")
    print(f"  TTFT ms        : {fmt_stats(p['ttft_ms'])}")
    print(f"  latency ms     : {fmt_stats(p['latency_ms'])}")
    print(f"  per-req tok/s  : {fmt_stats(p['tok_per_s'])}")
    print(f"  ITL ms         : {fmt_stats(p['itl_ms'])}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Benchmark LLM inference (sequential + concurrent) on an "
                    "OpenAI-compatible server.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL,
                    help="OpenAI-compatible base URL")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="model name to benchmark")
    ap.add_argument("--prompt", default=DEFAULT_PROMPT, help="benchmark prompt")
    ap.add_argument("--prompt-file",
                    help="read the benchmark prompt from a file (overrides --prompt)")
    ap.add_argument("--max-tokens", type=int, default=256,
                    help="max completion tokens per request")
    ap.add_argument("--temperature", type=float, default=0.0, help="sampling temperature")
    ap.add_argument("--num-requests", type=int, default=5,
                    help="sequential requests (concurrency 1)")
    ap.add_argument("--warmup", type=int, default=1, help="unmeasured warmup requests")
    ap.add_argument("--concurrency", type=int, default=4,
                    help="requests in flight for the concurrent phase")
    ap.add_argument("--concurrent-requests", type=int, default=16,
                    help="total requests in the concurrent phase")
    ap.add_argument("--sweep", default="",
                    help="comma list of concurrency levels, e.g. 1,2,4,8,16 "
                         "(replaces the single concurrent phase)")
    ap.add_argument("--sweep-requests", type=int, default=0,
                    help="requests per sweep level (default: max(4, 2x level))")
    ap.add_argument("--timeout", type=float, default=300, help="per-request read timeout (s)")
    ap.add_argument("--no-stream", action="store_true",
                    help="disable streaming (no TTFT/ITL)")
    ap.add_argument("--no-usage", action="store_true",
                    help="do not request stream usage (count chunks instead)")
    ap.add_argument("--json", dest="json_out", metavar="FILE",
                    help="write full results to a JSON file")
    args = ap.parse_args()

    prompt = args.prompt
    if args.prompt_file:
        with open(args.prompt_file, encoding="utf-8") as f:
            prompt = f.read().strip()

    stream = not args.no_stream
    include_usage = not args.no_usage

    print("=" * 64)
    print(" LLM Inference Benchmark")
    print("=" * 64)
    print(f" server     : {args.base_url}")
    print(f" model      : {args.model}")
    print(f" prompt     : {len(prompt)} chars")
    print(f" max_tokens : {args.max_tokens}   temperature: {args.temperature}   stream: {stream}")

    models, err = list_models(args.base_url)
    if models is None:
        print(f" WARNING: could not list models ({err}) — continuing anyway")
    else:
        print(f" models     : {', '.join(models) if models else '(none reported)'}")
        if args.model not in models:
            print(f" WARNING: '{args.model}' not in the server's model list")

    common = dict(
        base_url=args.base_url, model=args.model, prompt=prompt,
        max_tokens=args.max_tokens, temperature=args.temperature,
        timeout=args.timeout, stream=stream, include_usage=include_usage,
    )

    if args.warmup > 0:
        print(f"\nWarming up ({args.warmup} request(s))...")
        for _ in range(args.warmup):
            run_one(**common)

    report: dict[str, Any] = {
        "config": {
            "base_url": args.base_url, "model": args.model, "prompt": prompt,
            "max_tokens": args.max_tokens, "temperature": args.temperature,
            "stream": stream, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        },
        "models_on_server": models,
    }

    # Phase 1: sequential baseline
    seq = run_phase(concurrency=1, total_requests=args.num_requests,
                    label=f"Sequential (1 at a time, {args.num_requests} requests)", **common)
    report["sequential"] = seq
    print_phase(seq, show_per_request=True)

    # Phase 2: concurrent load (sub-agent style) or a concurrency sweep
    if args.sweep:
        levels = [int(x) for x in args.sweep.split(",") if x.strip()]
        sweep = []
        for level in levels:
            n = args.sweep_requests or max(4, level * 2)
            p = run_phase(concurrency=level, total_requests=n,
                          label=f"Concurrent (in flight {level}, {n} requests)", **common)
            sweep.append(p)
            print_phase(p, show_per_request=False)
        report["sweep"] = sweep

        print("\n--- Concurrency sweep summary ---")
        print(f"  {'conc':>4}  {'wall(s)':>8}  {'tokens':>6}  {'agg tok/s':>9}  "
              f"{'per-req tok/s':>13}  {'TTFT p50':>8}  {'lat p50':>9}  {'ok':>6}")
        base_tps = sweep[0]["aggregate_tps"] if sweep and sweep[0]["aggregate_tps"] else 0
        for p in sweep:
            speedup = (p["aggregate_tps"] / base_tps) if base_tps else 0
            print(f"  {p['concurrency']:>4}  {p['wall_s']:>8.1f}  {p['total_tokens']:>6}  "
                  f"{p['aggregate_tps']:>9.1f}  {p['tok_per_s']['mean']:>13.1f}  "
                  f"{p['ttft_ms']['p50']:>8.0f}  {p['latency_ms']['p50']:>9.0f}  "
                  f"{p['succeeded']}/{p['requests']}  ({speedup:.2f}x)")
    else:
        conc = run_phase(concurrency=args.concurrency,
                         total_requests=args.concurrent_requests,
                         label=f"Concurrent (in flight {args.concurrency}, "
                               f"{args.concurrent_requests} requests)", **common)
        report["concurrent"] = conc
        print_phase(conc, show_per_request=False)
        if seq["tok_per_s"]["mean"] > 0:
            ratio = conc["tok_per_s"]["mean"] / seq["tok_per_s"]["mean"]
            print(f"  per-request speed vs sequential: {ratio:.2f}x "
                  f"({seq['tok_per_s']['mean']:.1f} -> {conc['tok_per_s']['mean']:.1f} tok/s)")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nFull results written to {args.json_out}")

    phases = [report.get("concurrent"), report.get("sequential"), *report.get("sweep", [])]
    failed = sum(p["failed"] for p in phases if p)
    print("\nDone." if failed == 0 else f"\nDone with {failed} failed request(s).")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
