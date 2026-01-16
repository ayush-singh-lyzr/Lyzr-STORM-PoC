# Storm PoC (Lyzr Agents)

Small proof-of-concept showing how to use **Lyzr StormAgent** to generate a multi-section article (async) and how to call a deployed agent via the `LyzrAgent` client.

## Requirements

- **Python**: `>= 3.14` (per `pyproject.toml`)
- A valid **Lyzr API key**

## Setup

Set environment variables (.env file):

```bash
LYZR_API_KEY="YOUR_LYZR_API_KEY"
LYZR_USER_ID="you@company.com"
```

Install dependencies:

```bash
uv sync
uv add -r requirments.txt
```

## Run: Storm article generation (async)

Runs `StormAgent.write_async(...)`, prints event updates, writes a markdown file, and prints graph data:

```bash
uv run main.py
```

Expected outputs:
- **File**: `internet_of_things_async_1.md`
- **Console**: Storm event stream + a timing line from the `async_timeit` decorator + printed graph data

## Run: Basic Lyzr client call

`test_lyzr.py` demonstrates calling a deployed agent by `agent_id`:

```bash
python test_lyzr.py
```

## Notes

- **Secrets**: `LYZR_API_KEY` is read from the environment in `main.py`
- **Tuning**: In `main.py`, tweak `no_of_personas`, `no_of_questions`, and `no_of_sections` to change the depth/length of the generated content.