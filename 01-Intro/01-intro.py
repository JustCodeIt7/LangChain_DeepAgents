"""
LangChain Deep Agents - Intro Tutorial
======================================
Deep agents are built for complex, multi-step tasks with:
- Planning capabilities (todo lists)
- File system tools (for context management)
- Subagent spawning (for task delegation)

This example demonstrates a research agent that can:
1. Search the web
2. Plan its approach
3. Manage context with files
4. Generate a report
"""

# %% Step 1: Import dependencies
import os
import sys
from typing import Literal
from dotenv import load_dotenv
from tavily import TavilyClient
from deepagents import create_deep_agent
from langchain_ollama import ChatOllama

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import print_agent_execution, print_agent_summary, save_agent_result

# Load API keys from .env file
load_dotenv()
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
# %% Step 2: Initialize the LLM
# Using Ollama locally (free)
model = ChatOllama(model="gpt-oss:20b", base_url=OLLAMA_BASE_URL)

# Alternative: Use OpenAI (requires API key)
# from langchain_openai import ChatOpenAI
# model = ChatOpenAI(model="gpt-4o-mini")

# %% Step 3: Create a search tool
# Initialize Tavily search client
tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search to find information about a query.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 5)
        topic: Search topic category (general, news, or finance)
        include_raw_content: Whether to include full page content
    """
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


# %% Step 4: Create the deep agent
# System prompt defines agent behavior
research_instructions = """You are an expert researcher and writer.

Your job is to:
1. Conduct thorough research using the internet_search tool
2. Break down complex tasks into manageable steps
3. Organize your findings clearly
4. Write a concise, informative report

Always cite your sources and be factual."""

# Create the agent with tools and instructions
agent = create_deep_agent(model=model, tools=[internet_search], system_prompt=research_instructions)

# %% Step 5: Run the agent
# Ask the agent to research a topic
result = agent.invoke({
    "messages": [{"role": "user", "content": "Research what LangGraph is and write a brief summary."}]
})

# %%
# Print the agent's execution trace - shows all steps
print_agent_execution(result, verbose=True)

# Print a quick summary of what happened
print_agent_summary(result)

# %%
