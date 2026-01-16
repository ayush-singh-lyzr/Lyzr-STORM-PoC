"""
Benchmark StormAgent.write_async by varying personas/questions/sections.

Default grid (matches the TODO):
- personas: 1, 2, 3
- questions: 1
- sections: 1, 2, 3

Outputs:
- CSV: performance_results/perf_results.csv
- JSONL: performance_results/perf_results.jsonl
- Plot (optional): performance_results/perf_plot.png (requires matplotlib)
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Iterable, List, Optional

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # optional dependency
    def load_dotenv(*_args, **_kwargs) -> bool:  # type: ignore
        return False
from lyzr_agents.storm import StormAgent
from lyzr_agents.storm.config import test_config


@dataclass(frozen=True)
class PerfRow:
    ts_utc: str
    topic: str
    test_mode: bool
    personas: int
    questions: int
    sections: int
    run_index: int
    elapsed_s: float
    success: bool
    article_chars: int
    events_count: int
    error: str


def _parse_int_list(value: str) -> List[int]:
    parts = [p.strip() for p in value.split(",") if p.strip()]
    if not parts:
        raise argparse.ArgumentTypeError("Empty list")
    try:
        parsed = [int(p) for p in parts]
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid int list: {value}") from e
    if any(x <= 0 for x in parsed):
        raise argparse.ArgumentTypeError("All values must be positive integers")
    return parsed


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _bench_once(
    *,
    topic: str,
    personas: int,
    questions: int,
    sections: int,
    test_mode: bool,
    print_events: bool,
) -> PerfRow:
    if test_mode:
        agent = StormAgent(
            lyzr_api_key="test",
            user_id="test",
            config=test_config(),
            no_of_personas=personas,
            no_of_questions=questions,
            no_of_sections=sections,
            on_event=(lambda e: print(f"Event: {e.event_type.value}")) if print_events else None,
        )
    else:
        lyzr_api_key = os.getenv("LYZR_API_KEY")
        lyzr_user_id = os.getenv("LYZR_USER_ID", "user@example.com")
        if not lyzr_api_key:
            raise RuntimeError(
                "Missing LYZR_API_KEY. Put it in a .env file or export it, e.g.:\n"
                '  echo \'LYZR_API_KEY="..."\' > .env\n'
                "Optionally set LYZR_USER_ID as well."
            )

        agent = StormAgent(
            lyzr_api_key=lyzr_api_key,
            user_id=lyzr_user_id,
            no_of_personas=personas,
            no_of_questions=questions,
            no_of_sections=sections,
            on_event=(lambda e: print(f"Event: {e.event_type.value}")) if print_events else None,
        )

    started = perf_counter()
    result = await agent.write_async(topic)
    elapsed = perf_counter() - started

    return PerfRow(
        ts_utc=_iso_utc_now(),
        topic=topic,
        test_mode=test_mode,
        personas=personas,
        questions=questions,
        sections=sections,
        run_index=0,  # filled by caller
        elapsed_s=elapsed,
        success=bool(result),
        article_chars=len(result.article or ""),
        events_count=len(result.events or []),
        error=(result.error or "") if not bool(result) else "",
    )


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _write_csv(path: Path, rows: Iterable[PerfRow]) -> None:
    _ensure_parent(path)
    rows = list(rows)
    fieldnames = list(asdict(rows[0]).keys()) if rows else list(asdict(PerfRow("", "", False, 0, 0, 0, 0, 0.0, False, 0, 0, "")).keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(asdict(r))


def _write_jsonl(path: Path, rows: Iterable[PerfRow]) -> None:
    _ensure_parent(path)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")


def _print_summary_table(rows: List[PerfRow]) -> None:
    # Compact table: elapsed mean by personas x sections (assumes single questions)
    by_key: dict[tuple[int, int], List[float]] = {}
    for r in rows:
        by_key.setdefault((r.personas, r.sections), []).append(r.elapsed_s)

    personas_vals = sorted({p for (p, _s) in by_key.keys()})
    sections_vals = sorted({s for (_p, s) in by_key.keys()})

    def mean(xs: List[float]) -> float:
        return sum(xs) / max(len(xs), 1)

    header = ["personas\\sections", *[str(s) for s in sections_vals]]
    print("\n" + " | ".join(header))
    print("-" * (len(" | ".join(header))))
    for p in personas_vals:
        row = [str(p)]
        for s in sections_vals:
            xs = by_key.get((p, s), [])
            row.append(f"{mean(xs):.2f}s" if xs else "-")
        print(" | ".join(row))
    print()


def _try_plot(path: Path, rows: List[PerfRow]) -> Optional[Path]:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return None

    # Plot lines: x=sections, y=mean elapsed, one line per personas (fixed questions)
    by_key: dict[tuple[int, int], List[float]] = {}
    for r in rows:
        by_key.setdefault((r.personas, r.sections), []).append(r.elapsed_s)

    personas_vals = sorted({p for (p, _s) in by_key.keys()})
    sections_vals = sorted({s for (_p, s) in by_key.keys()})

    def mean(xs: List[float]) -> float:
        return sum(xs) / max(len(xs), 1)

    plt.figure(figsize=(8, 5))
    for p in personas_vals:
        ys = [mean(by_key.get((p, s), [])) for s in sections_vals]
        plt.plot(sections_vals, ys, marker="o", label=f"personas={p}")

    plt.title("StormAgent.write_async performance")
    plt.xlabel("Number of sections")
    plt.ylabel("Elapsed time (s)")
    plt.grid(True, alpha=0.3)
    plt.legend()

    _ensure_parent(path)
    plt.tight_layout()
    plt.savefig(path)
    return path


async def _amain() -> int:
    parser = argparse.ArgumentParser(description="Benchmark StormAgent.write_async")
    parser.add_argument("--topic", default="Internet of Things")
    parser.add_argument("--personas", type=_parse_int_list, default=[1, 2], help="Comma-separated, e.g. 1,2,3")
    parser.add_argument("--questions", type=_parse_int_list, default=[1], help="Comma-separated, e.g. 1")
    parser.add_argument("--sections", type=_parse_int_list, default=[1, 2], help="Comma-separated, e.g. 1,2,3")
    parser.add_argument("--runs", type=int, default=1, help="Repeats per config (>=1)")
    parser.add_argument("--test-mode", action="store_true", help="Use mock mode (no API calls)")
    parser.add_argument("--print-events", action="store_true", help="Print Storm events while running")
    parser.add_argument("--out-csv", default="performance_results/perf_results.csv")
    parser.add_argument("--out-jsonl", default="performance_results/perf_results.jsonl")
    parser.add_argument("--plot", action="store_true", help="Try to generate perf_plot.png (requires matplotlib)")
    parser.add_argument("--out-plot", default="performance_results/perf_plot.png")
    args = parser.parse_args()

    if args.runs < 1:
        raise ValueError("--runs must be >= 1")

    load_dotenv()

    rows: List[PerfRow] = []

    total = len(args.personas) * len(args.questions) * len(args.sections) * args.runs
    idx = 0
    for p in args.personas:
        for q in args.questions:
            for s in args.sections:
                for run_index in range(args.runs):
                    idx += 1
                    print(f"[{idx}/{total}] personas={p} questions={q} sections={s} run={run_index + 1}/{args.runs}")
                    row = await _bench_once(
                        topic=args.topic,
                        personas=p,
                        questions=q,
                        sections=s,
                        test_mode=bool(args.test_mode),
                        print_events=bool(args.print_events),
                    )
                    rows.append(
                        PerfRow(
                            **{
                                **asdict(row),
                                "run_index": run_index + 1,
                            }
                        )
                    )

    out_csv = Path(args.out_csv)
    out_jsonl = Path(args.out_jsonl)
    _write_csv(out_csv, rows)
    _write_jsonl(out_jsonl, rows)

    print(f"\nSaved CSV:   {out_csv}")
    print(f"Saved JSONL: {out_jsonl}")
    _print_summary_table(rows)

    if args.plot:
        out_plot = Path(args.out_plot)
        plotted = _try_plot(out_plot, rows)
        if plotted:
            print(f"Saved plot:  {plotted}")
        else:
            print("Plot skipped: matplotlib not installed. Install with `uv add matplotlib` (or `pip install matplotlib`).")

    return 0


def main() -> None:
    raise SystemExit(asyncio.run(_amain()))


if __name__ == "__main__":
    main()