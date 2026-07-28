"""
Deep Research Assistant - LangGraph State Machine
==================================================
Multi-agent workflow for conducting comprehensive research using:
- Planning Agent: Decomposes research topics into structured plans
- Research Agent: Performs web searches and gathers data
- Synthesis Agent: Compiles findings into markdown reports
"""

from typing import TypedDict, Annotated, List, Dict
import operator
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from tavily import TavilyClient
import os


class ResearchState(TypedDict):
    """State for the research workflow"""

    topic: str
    research_plan: List[str]
    search_results: Annotated[List[Dict], operator.add]
    final_report: str
    current_step: str


class ResearchGraph:
    """LangGraph-based deep research assistant"""

    def __init__(
        self,
        model_provider: str = "ollama",
        model_name: str = "gpt-oss:20b",
        tavily_api_key: str = None,
        ollama_base_url: str = "http://localhost:11434",
    ):
        self.tavily_client = TavilyClient(
            api_key=tavily_api_key or os.getenv("TAVILY_API_KEY")
        )

        if model_provider == "ollama":
            self.llm = ChatOllama(model=model_name, base_url=ollama_base_url)
        else:
            self.llm = ChatOpenAI(model=model_name)

        self.graph = self._build_graph()

    def _planning_agent(self, state: ResearchState) -> Dict:
        """
        Planning Agent: Decomposes research topic into structured execution plan
        """
        planning_prompt = f"""You are a research planning expert. Given the research topic below, create a detailed execution plan.

Research Topic: {state["topic"]}

Generate 3-5 specific research questions or subtopics that should be investigated to comprehensively cover this topic.
Each question should be focused, specific, and answerable through web search.

Format your response as a numbered list of research questions only, no additional commentary."""

        response = self.llm.invoke(
            [
                SystemMessage(content="You are an expert research planner."),
                HumanMessage(content=planning_prompt),
            ]
        )

        plan_text = response.content
        research_questions = [
            line.strip().lstrip("0123456789.-) ")
            for line in plan_text.split("\n")
            if line.strip() and any(char.isalnum() for char in line)
        ]

        return {
            "research_plan": research_questions[:5],
            "current_step": "planning_complete",
        }

    def _research_agent(self, state: ResearchState) -> Dict:
        """
        Research Agent: Performs web searches for each question in the plan
        """
        all_results = []

        for question in state.get("research_plan", []):
            try:
                search_response = self.tavily_client.search(
                    query=question,
                    max_results=3,
                    include_raw_content=False,
                    topic="general",
                )

                for result in search_response.get("results", []):
                    all_results.append(
                        {
                            "question": question,
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "content": result.get("content", ""),
                        }
                    )
            except Exception as e:
                all_results.append(
                    {
                        "question": question,
                        "title": "Error",
                        "url": "",
                        "content": f"Search failed: {str(e)}",
                    }
                )

        return {"search_results": all_results, "current_step": "research_complete"}

    def _synthesis_agent(self, state: ResearchState) -> Dict:
        """
        Synthesis Agent: Compiles research findings into structured markdown report
        """
        results_text = "\n\n".join(
            [
                f"Question: {r['question']}\nSource: {r['title']} ({r['url']})\nContent: {r['content']}"
                for r in state.get("search_results", [])
            ]
        )

        synthesis_prompt = f"""You are an expert research writer. Based on the research findings below, write a comprehensive markdown report on the topic: {state["topic"]}

Research Findings:
{results_text}

Write a professional, publication-quality markdown report with:
1. A clear title (# header)
2. An introduction section (## Introduction)
3. Main body sections with hierarchical headers (## and ###)
4. Proper citations using [Source Title](URL) format
5. A conclusion section (## Conclusion)
6. A references section (## References) listing all sources

Format your response in clean markdown. Be factual, concise, and cite sources appropriately."""

        response = self.llm.invoke(
            [
                SystemMessage(content="You are an expert technical writer."),
                HumanMessage(content=synthesis_prompt),
            ]
        )

        return {"final_report": response.content, "current_step": "synthesis_complete"}

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph StateGraph workflow
        """
        workflow = StateGraph(ResearchState)

        workflow.add_node("planning_agent", self._planning_agent)
        workflow.add_node("research_agent", self._research_agent)
        workflow.add_node("synthesis_agent", self._synthesis_agent)

        workflow.add_edge(START, "planning_agent")
        workflow.add_edge("planning_agent", "research_agent")
        workflow.add_edge("research_agent", "synthesis_agent")
        workflow.add_edge("synthesis_agent", END)

        return workflow.compile()

    def run(self, topic: str) -> ResearchState:
        """
        Execute the research workflow

        Args:
            topic: Research topic/question

        Returns:
            Final state containing the generated report
        """
        initial_state = {
            "topic": topic,
            "research_plan": [],
            "search_results": [],
            "final_report": "",
            "current_step": "initialized",
        }

        return self.graph.invoke(initial_state)

    def stream(self, topic: str):
        """
        Stream the research workflow execution

        Args:
            topic: Research topic/question

        Yields:
            State updates after each node execution
        """
        initial_state = {
            "topic": topic,
            "research_plan": [],
            "search_results": [],
            "final_report": "",
            "current_step": "initialized",
        }

        for state in self.graph.stream(initial_state, stream_mode="values"):
            yield state
