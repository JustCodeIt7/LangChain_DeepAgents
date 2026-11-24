"""
11 - Structured Output
======================
- Pass a Pydantic model as `response_format` to get typed results
- Read it from `result["structured_response"]` — a real object, not a string
- No more regex-parsing the model's prose

Run:  python 11-structured_output.py
"""

# %% Step 1: Imports and setup
import os

from deepagents import create_deep_agent
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from rich import print

from langchain_ollama import ChatOllama

load_dotenv()


# Choose your LLM provider by commenting/uncommenting:
#
# Option 1: Ollama (local)
# Make sure Ollama is running and you have pulled the model (e.g., ollama pull qwen3.5:2b)
model = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "qwen3.5:2b"),
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    temperature=0,  # repeatable output: the run you rehearse is the run you record
    reasoning=False,  # skip hidden "thinking" tokens: faster, and no empty answers
)
#
# Option 2: OpenRouter
# from langchain_openrouter import ChatOpenRouter
# model = ChatOpenRouter(model="meta/muse-spark-1.3-contributor", temperature=0)

# %% Step 2: Describe the shape you want back
# Field descriptions are sent to the model as part of the schema, so they act
# as per-field instructions. Keep schemas flat and simple — smaller models
# handle a few scalar fields far more reliably than deep nesting.
class BookReview(BaseModel):
    """A structured verdict on a book."""

    title: str = Field(description="The title of the book being reviewed.")
    rating: int = Field(description="A rating from 1 to 5, where 5 is best.")
    one_liner: str = Field(description="A single sentence summarizing the verdict.")


# %% Step 3: Attach the schema to the agent
agent = create_deep_agent(
    model=model,
    response_format=BookReview,
    system_prompt="You are a book critic. Answer using the structured format.",
)

# %% Step 4: Ask a question whose answer fits the schema
# Do NOT add "don't use tools" here: the structured answer is delivered as a
# tool call named after your schema, so that instruction silently breaks it.
task = "Review the book 'The Hobbit' by J.R.R. Tolkien."

# Structured output relies on the model following a tool/JSON schema. Smaller
# local models sometimes drift, so fail gracefully rather than crashing.
try:
    result = agent.invoke({"messages": [{"role": "user", "content": task}]})
    review = result.get("structured_response")
except Exception as error:  # noqa: BLE001 - tutorial-friendly catch-all
    print(f"[red]The model did not produce valid structured output:[/red] {error}")
    review = None

# %% Step 5: Use it like the Python object it is
if isinstance(review, BookReview):
    print("[bold cyan]Typed object returned:[/bold cyan]")
    print(f"  type:      [yellow]{type(review).__name__}[/yellow]")
    print(f"  title:     {review.title}")
    print(f"  rating:    {'★' * review.rating}{'☆' * (5 - review.rating)} ({review.rating}/5)")
    print(f"  one_liner: {review.one_liner}")

    # Because it is a Pydantic model, you get validation and serialization free.
    print("\n[bold cyan]As JSON (ready for an API or database):[/bold cyan]")
    print(review.model_dump_json(indent=2))
else:
    print("[yellow]No structured response — try a larger model.[/yellow]")

