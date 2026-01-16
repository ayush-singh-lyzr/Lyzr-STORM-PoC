# Storm PoC (Lyzr Agents)

Small proof-of-concept showing how to use **Lyzr StormAgent** to generate a multi-section article (async) and how to call a deployed agent via the `LyzrAgent` client.

## Requirements

- **Python**: `>= 3.14` (per `pyproject.toml`)
- A valid **Lyzr API key**

## Setup

Create a `.env` file in the project root (you can copy from `env.example`):

```bash
LYZR_API_KEY="YOUR_LYZR_API_KEY"
LYZR_USER_ID="you@company.com"   # optional
```

Install dependencies:

```bash
uv sync
```

## Run: Storm article generation (async)

Runs `StormAgent.write_async(...)`, prints event updates, writes a markdown file, and prints graph data:

```bash
uv run python main.py
```

Expected outputs:
- **File**: `internet_of_things_async_1.md`
- **Console**: Storm event stream + a timing line from the `async_timeit` decorator + printed graph data

## Run: Performance benchmark

Benchmarks `StormAgent.write_async` across a small grid and saves results to `performance_results/`:

```bash
uv run python test_performance.py --plot
```

To run without real API calls (fast, deterministic mock mode):

```bash
uv run python test_performance.py --test-mode --plot
```

## Notes

- **Secrets**: `LYZR_API_KEY` is read from the environment in `main.py`
- **Plotting**: `--plot` needs `matplotlib` (`uv add matplotlib`)
- **Tuning**: In `main.py`, tweak `no_of_personas`, `no_of_questions`, and `no_of_sections` to change the depth/length of the generated content.