from time import time, perf_counter
from functools import wraps
from lyzr_agents.storm import StormAgent
from dotenv import load_dotenv
import os

load_dotenv()

# Environment variables (avoid hardcoding secrets in code)
LYZR_API_KEY = os.getenv("LYZR_API_KEY")
LYZR_USER_ID = os.getenv("LYZR_USER_ID", "user@example.com")

if not LYZR_API_KEY:
    raise RuntimeError(
        "Missing LYZR_API_KEY. Set it in your environment, e.g.:\n"
        "  export LYZR_API_KEY='...'\n"
        "Optionally also set LYZR_USER_ID='you@company.com'."
    )

# Initialize with default Lyzr agents
agent = StormAgent(
    lyzr_api_key=LYZR_API_KEY,
    user_id=LYZR_USER_ID,
    on_event=lambda e: print(f"Event: {e.event_type.value}"),
    no_of_personas=2,    # Number of expert perspectives
    no_of_questions=1,   # Questions per persona
    no_of_sections=4,    # Article sections
)

# Generate an article (sync)
# result = agent.write("Internet of Things")
# result.toFile("internet_of_things.md")

# Or use async for parallel execution (faster)
import asyncio

def async_timeit(func):
    """An asynchronous decorator to time a function."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            end_time = perf_counter()
            total_time = end_time - start_time
            print(f"Function `{func.__name__}` took {total_time:.4f} seconds")
    return wrapper

@async_timeit
async def main():
    result = await agent.write_async("Internet of Things")
    result.toFile("internet_of_things_async_1.md")
    graph_data = result.get_graph_data()
    print(graph_data)
    # result.print()

asyncio.run(main())