# Deep Research Assistant

A comprehensive Python-based local deep research assistant using LangChain, LangGraph, and LangChain-Ollama to leverage local LLMs for private, high-fidelity information synthesis.

## Features

- **Multi-Agent Workflow**: Orchestrates Planning, Research, and Synthesis agents using LangGraph
- **Planning Agent**: Decomposes research topics into structured execution plans
- **Research Agent**: Performs iterative web searches using Tavily API
- **Synthesis Agent**: Compiles findings into publication-quality Markdown reports with citations
- **Interactive UI**: Built with Streamlit featuring real-time progress tracking and markdown preview
- **Local-First**: Designed to work with local Ollama models for privacy

## Architecture

```
┌──────────────┐
│ Streamlit UI │
└──────┬───────┘
       │
       v
┌─────────────────────────────────────────┐
│         LangGraph StateGraph            │
├─────────────────────────────────────────┤
│                                         │
│  START → Planning → Research → Synthesis → END
│                                         │
│  State: {topic, plan, results, report}  │
└─────────────────────────────────────────┘
```

## Installation

### Prerequisites

1. **Python 3.12 or later**
2. **Ollama** (for local LLMs) - [Install Ollama](https://ollama.ai)
3. **Tavily API Key** - [Get API Key](https://tavily.com)

### Setup

```bash
# Navigate to the DeepResearch directory
cd DeepResearch

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Pull an Ollama model (if using local LLMs)
ollama pull gpt-oss:20b  # or llama3.2, qwen3:1.7b, etc.

# Configure environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Environment Configuration

Create a `.env` file with the following variables:

```env
OLLAMA_BASE_URL=http://localhost:11434
TAVILY_API_KEY=your_tavily_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # Optional, only if using OpenAI
```

## Usage

### Running the Streamlit App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

### Using the Interface

1. **Configure Settings** (Sidebar):
   - Select model provider (Ollama or OpenAI)
   - Choose a model
   - Enter API keys (or load from `.env`)

2. **Enter Research Topic**:
   - Type your research question or topic in the text area
   - Click "Start Research"

3. **Monitor Progress**:
   - Watch real-time updates as the system progresses through:
     - Planning: Generating research questions
     - Research: Gathering data from web sources
     - Synthesis: Writing the final report

4. **View Results**:
   - Read the generated markdown report
   - Download as `.md` file for later use

### Programmatic Usage

You can also use the research graph directly in Python:

```python
from research_graph import ResearchGraph

# Initialize the graph
graph = ResearchGraph(
    model_provider="ollama",
    model_name="gpt-oss:20b",
    tavily_api_key="your_api_key"
)

# Run research
result = graph.run("What are the latest developments in quantum computing?")

# Access the final report
print(result['final_report'])

# Or stream the execution
for state in graph.stream("Your research topic"):
    print(f"Current step: {state['current_step']}")
```

## Project Structure

```
DeepResearch/
├── app.py                  # Streamlit UI
├── research_graph.py       # LangGraph workflow implementation
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variable template
└── README.md              # This file
```

## Key Components

### `research_graph.py`

- **ResearchState**: TypedDict defining the workflow state
- **ResearchGraph**: Main class implementing the LangGraph workflow
  - `_planning_agent()`: Decomposes topic into research questions
  - `_research_agent()`: Performs web searches for each question
  - `_synthesis_agent()`: Compiles findings into markdown report
  - `_build_graph()`: Constructs the LangGraph StateGraph

### `app.py`

- Streamlit interface with:
  - Sidebar configuration for model and API settings
  - Research query input
  - Real-time progress tracking with `st.status()`
  - Markdown preview and download functionality

## Development

### Modifying the Workflow

To customize the research workflow, edit `research_graph.py`:

```python
def _planning_agent(self, state: ResearchState) -> Dict:
    # Customize planning logic
    pass

def _research_agent(self, state: ResearchState) -> Dict:
    # Customize research sources or search parameters
    pass

def _synthesis_agent(self, state: ResearchState) -> Dict:
    # Customize report format or structure
    pass
```

### Adding New Nodes

```python
def _build_graph(self) -> StateGraph:
    workflow = StateGraph(ResearchState)

    # Add your custom node
    workflow.add_node("custom_node", self._custom_agent)

    # Wire it into the graph
    workflow.add_edge("research_agent", "custom_node")
    workflow.add_edge("custom_node", "synthesis_agent")

    return workflow.compile()
```

## Configuration Options

### Supported Models

**Ollama (Local)**:

- `gpt-oss:20b` (recommended for quality)
- `llama3.2` (fast, good balance)
- `qwen3:1.7b` (lightweight)
- `gemma3:4b` (efficient)

**OpenAI (Hosted)**:

- `gpt-4o` (highest quality)
- `gpt-4o-mini` (cost-effective)
- `gpt-4-turbo` (fast)

### Tavily Search Parameters

Modify in `research_graph.py`:

```python
search_response = self.tavily_client.search(
    query=question,
    max_results=3,           # Number of results per query
    include_raw_content=False,  # Include full page content
    topic="general"          # "general", "news", or "finance"
)
```

## Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama (if not running)
ollama serve
```

### Missing Dependencies

```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

### API Key Errors

- Verify your Tavily API key is valid at [tavily.com](https://tavily.com)
- Ensure the key is properly set in `.env` or entered in the Streamlit sidebar

## Contributing

This project is part of the LangChain Deep Agents tutorial series. Feel free to:

- Report issues
- Submit pull requests
- Suggest improvements

## License

See the main repository LICENSE file.

## Related

- Main Project: [LangChain_DeepAgents](../)
- Tutorial: [01-Intro](../01-Intro/)
- Utilities: [utils.py](../utils.py)
