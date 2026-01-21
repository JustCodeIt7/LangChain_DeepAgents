"""
Utility functions for LangChain Deep Agents
"""
import json
from typing import Dict, List, Any


def print_agent_execution(result: Dict[str, Any], verbose: bool = True) -> None:
    """
    Print the agent's execution path in a readable format.
    
    Shows:
    - User queries
    - Tool calls made by the agent
    - Tool results
    - Agent responses
    
    Args:
        result: The result dictionary from agent.invoke() containing messages
        verbose: If True, show full tool results; if False, truncate long outputs
    """
    messages = result.get("messages", [])
    
    print("\n" + "═" * 80)
    print("🤖 AGENT EXECUTION TRACE")
    print("═" * 80)
    
    step = 1
    
    for i, msg in enumerate(messages):
        # Handle different message types
        msg_type = getattr(msg, 'type', None)
        
        if msg_type == "human":
            # User message
            print(f"\n📨 USER INPUT:")
            print(f"   └─ {msg.content}")
            print()
            
        elif msg_type == "ai":
            # AI message - check if it has tool calls
            tool_calls = getattr(msg, 'tool_calls', [])
            
            if tool_calls:
                # Agent is calling tools
                print(f"🔧 STEP {step}: AGENT TOOL CALLS")
                for tc in tool_calls:
                    tool_name = tc.get('name', 'unknown')
                    tool_args = tc.get('args', {})
                    print(f"   ├─ Tool: {tool_name}")
                    print(f"   └─ Args: {json.dumps(tool_args, indent=6)}")
                print()
                step += 1
            else:
                # Final agent response
                content = msg.content
                if content:
                    print(f"✅ FINAL RESPONSE:")
                    print(f"   {content}")
                    print()
                    
        elif msg_type == "tool":
            # Tool result
            tool_name = getattr(msg, 'name', 'unknown')
            content = msg.content
            
            print(f"📊 TOOL RESULT: {tool_name}")
            
            # Try to parse as JSON for better formatting
            try:
                parsed_content = json.loads(content)
                
                # Handle different tool result structures
                if "results" in parsed_content:
                    results = parsed_content["results"]
                    print(f"   ├─ Found {len(results)} results")
                    
                    if verbose:
                        for idx, res in enumerate(results[:3], 1):  # Show first 3
                            print(f"   ├─ Result {idx}:")
                            print(f"   │  ├─ Title: {res.get('title', 'N/A')}")
                            print(f"   │  ├─ URL: {res.get('url', 'N/A')}")
                            print(f"   │  └─ Score: {res.get('score', 'N/A')}")
                        if len(results) > 3:
                            print(f"   └─ ... and {len(results) - 3} more results")
                    else:
                        print(f"   └─ (Use verbose=True to see details)")
                elif "Error" in content:
                    print(f"   └─ ❌ {content}")
                else:
                    # Generic JSON output
                    print(f"   └─ {json.dumps(parsed_content, indent=6)[:500]}")
                    
            except (json.JSONDecodeError, AttributeError):
                # Not JSON, print as text
                if len(content) > 200 and not verbose:
                    print(f"   └─ {content[:200]}... (truncated)")
                else:
                    print(f"   └─ {content}")
            
            print()
    
    print("═" * 80)
    print("✨ Execution complete!")
    print("═" * 80 + "\n")


def print_agent_summary(result: Dict[str, Any]) -> None:
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


def save_agent_result(result: Dict[str, Any], filename: str = "agent_response.json") -> None:
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
