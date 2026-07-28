"""
Streamlit UI for Deep Research Assistant
========================================
Interactive web interface featuring:
- Sidebar configuration for model and API settings
- Real-time progress tracking of LangGraph nodes
- Markdown preview of the final research report
"""

import streamlit as st
import os
from dotenv import load_dotenv
from research_graph import ResearchGraph

load_dotenv()

st.set_page_config(page_title="Deep Research Assistant", page_icon="🔬", layout="wide")

st.title("🔬 Deep Research Assistant")
st.markdown("*Powered by LangGraph, LangChain, and Local LLMs*")

with st.sidebar:
    st.header("⚙️ Configuration")

    st.subheader("🧠 Model Settings")
    model_provider = st.radio(
        "Model Provider",
        options=["ollama", "openai"],
        help="Choose between local Ollama or hosted OpenAI",
    )

    if model_provider == "ollama":
        model_name = st.selectbox(
            "Ollama Model",
            options=["gpt-oss:20b", "llama3.2", "qwen3:1.7b", "gemma3:4b"],
            help="Select a local Ollama model (must be pulled first)",
        )
        ollama_base_url = st.text_input(
            "Ollama Base URL",
            value=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            help="URL of your local Ollama instance",
        )
    else:
        model_name = st.selectbox(
            "OpenAI Model",
            options=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            help="Select an OpenAI model",
        )
        ollama_base_url = None

    st.subheader("🔑 API Keys")
    tavily_api_key = st.text_input(
        "Tavily API Key",
        value=os.getenv("TAVILY_API_KEY", ""),
        type="password",
        help="Required for web search functionality",
    )

    if model_provider == "openai":
        openai_api_key = st.text_input(
            "OpenAI API Key",
            value=os.getenv("OPENAI_API_KEY", ""),
            type="password",
            help="Required for OpenAI models",
        )
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key

    st.divider()
    st.caption("💡 Tip: Set keys in `.env` file for persistence")

if "messages" not in st.session_state:
    st.session_state.messages = []

st.subheader("💬 Research Query")
topic_input = st.text_area(
    "Enter your research topic or question:",
    placeholder="Example: What are the latest developments in quantum computing?",
    height=100,
)

col1, col2 = st.columns([1, 5])
with col1:
    start_research = st.button(
        "🚀 Start Research", type="primary", use_container_width=True
    )
with col2:
    st.empty()

if start_research and topic_input:
    if not tavily_api_key:
        st.error("⚠️ Please provide a Tavily API key in the sidebar")
    else:
        research_graph = ResearchGraph(
            model_provider=model_provider,
            model_name=model_name,
            tavily_api_key=tavily_api_key,
            ollama_base_url=ollama_base_url,
        )

        st.session_state.messages.append({"role": "user", "content": topic_input})

        with st.status("🔬 Conducting Research...", expanded=True) as status:
            progress_container = st.container()

            with progress_container:
                planning_status = st.empty()
                research_status = st.empty()
                synthesis_status = st.empty()

            final_state = None

            for state in research_graph.stream(topic_input):
                current_step = state.get("current_step", "")

                if current_step == "planning_complete":
                    planning_status.success("✅ **Planning Complete**")
                    with st.expander("📋 Research Plan", expanded=False):
                        for i, question in enumerate(state.get("research_plan", []), 1):
                            st.markdown(f"{i}. {question}")
                    research_status.info(
                        "🔍 **Researching...** (gathering data from web sources)"
                    )

                elif current_step == "research_complete":
                    research_status.success("✅ **Research Complete**")
                    num_results = len(state.get("search_results", []))
                    with st.expander(
                        f"📚 Search Results ({num_results} sources)", expanded=False
                    ):
                        for result in state.get("search_results", []):
                            st.markdown(f"**Q:** {result.get('question', '')}")
                            st.markdown(
                                f"*{result.get('title', '')}* - [{result.get('url', '')}]({result.get('url', '')})"
                            )
                            st.caption(result.get("content", "")[:200] + "...")
                            st.divider()
                    synthesis_status.info(
                        "✍️ **Synthesizing...** (writing final report)"
                    )

                elif current_step == "synthesis_complete":
                    synthesis_status.success("✅ **Synthesis Complete**")
                    final_state = state

            status.update(
                label="✨ Research Complete!", state="complete", expanded=False
            )

        if final_state:
            st.session_state.messages.append(
                {"role": "assistant", "content": final_state.get("final_report", "")}
            )

st.divider()

if st.session_state.messages:
    st.subheader("📄 Research Report")

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(f"**Research Topic:** {msg['content']}")
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])

    with st.expander("💾 Download Report", expanded=False):
        report_md = (
            st.session_state.messages[-1]["content"]
            if st.session_state.messages
            else ""
        )
        st.download_button(
            label="Download as Markdown",
            data=report_md,
            file_name="research_report.md",
            mime="text/markdown",
        )
else:
    st.info("👆 Enter a research topic above and click 'Start Research' to begin")

with st.sidebar:
    st.divider()
    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.rerun()
