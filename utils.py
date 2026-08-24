"""
Utility functions for LangChain Deep Agents
"""
import json
from typing import Any

from rich import print


def print_agent_execution(result: dict[str, Any], max_length: int = 500) -> None:
    """
    Print the agent's execution path in a simple, readable format.

    Shows the message type and content for each message in the conversation.

    Args:
        result: The result dictionary from agent.invoke() containing messages
        max_length: Maximum characters to show per message (default: 500)
    """
    messages = result.get("messages", [])
    
    print("\n" + "═" * 80)
    print("🤖 AGENT EXECUTION TRACE")
    print("═" * 80 + "\n")

    for i, msg in enumerate(messages, 1):
        # Get message type
        msg_type = getattr(msg, "type", "unknown")

        # Choose emoji based on type
        emoji_map = {"human": "👤", "ai": "🤖", "tool": "🔧"}
        emoji = emoji_map.get(msg_type, "❓")

        # Get content
        content = getattr(msg, "content", "")

        # Truncate if too long
        if len(content) > max_length:
            content = content[:max_length] + "..."

        # Check if AI message has tool calls
        tool_call_info = ""
        if msg_type == "ai":
            tool_calls = getattr(msg, "tool_calls", [])
            if tool_calls:
                tool_names = [tc.get("name", "unknown") for tc in tool_calls]
                tool_call_info = f" - Calling: {', '.join(tool_names)}"

        # Print message
        print(f"{emoji} Message {i} [{msg_type.upper()}]{tool_call_info}:")
        print(f"{content}")
        print()
    
    print("═" * 80)
    print("✨ Execution complete!")
    print("═" * 80 + "\n")


def print_agent_summary(result: dict[str, Any]) -> None:
    """
    Print a concise summary of the agent's execution.
    
    Args:
        result: The result dictionary from agent.invoke() containing messages
    """
    messages = result.get("messages", [])
    
    # Count different message types
    human_msgs = sum(1 for m in messages if getattr(m, 'type', None) == 'human')
    ai_msgs = sum(1 for m in messages if getattr(m, 'type', None) == 'ai')
    tool_msgs = sum(1 for m in messages if getattr(m, 'type', None) == 'tool')
    
    # Count tool calls
    total_tool_calls = sum(
        len(getattr(m, 'tool_calls', []))
        for m in messages
        if getattr(m, 'type', None) == 'ai'
    )
    
    print("\n" + "─" * 60)
    print("📊 EXECUTION SUMMARY")
    print("─" * 60)
    print(f"   Total messages:  {len(messages)}")
    print(f"   User inputs:     {human_msgs}")
    print(f"   AI responses:    {ai_msgs}")
    print(f"   Tool calls:      {total_tool_calls}")
    print(f"   Tool results:    {tool_msgs}")
    print("─" * 60 + "\n")


def save_agent_result(result: dict[str, Any], filename: str = "agent_response.json") -> None:
    """
    Save agent result to a JSON file.
    
    Args:
        result: The result dictionary from agent.invoke()
        filename: Output filename (default: agent_response.json)
    """
    # Convert message objects to dictionaries for JSON serialization
    serializable_result = {}
    
    for key, value in result.items():
        if key == "messages":
            # Convert message objects to dicts
            serializable_result[key] = [
                msg.dict() if hasattr(msg, 'dict') else msg
                for msg in value
            ]
        else:
            serializable_result[key] = value
    
    with open(filename, "w") as f:
        json.dump(serializable_result, f, indent=4)
    
    print(f"💾 Agent response saved to {filename}")
