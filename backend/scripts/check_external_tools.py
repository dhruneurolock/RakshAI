import asyncio
import json
import sys
import os

# Ensure the project root is on the PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app.agents.base_agent import ToolSandbox, ToolResult

# List of tools we want to verify. The dict maps tool name to a minimal set of params.
TOOLS_TO_CHECK = {
    "httpx": {"target": "https://example.com"},
    "katana": {"url": "https://example.com"},
    "nuclei": {"target": "https://example.com"},
    "sqlmap": {"url": "https://example.com/vuln"},
    "dalfox": {"url": "https://example.com"},
    "idor_tester": {"url": "https://example.com"},
    "auth_bypass_tester": {"url": "https://example.com"},
}

async def check_tool(sandbox: ToolSandbox, name: str, params: dict) -> ToolResult:
    """Execute a tool via the sandbox and return the result.

    The sandbox already handles binary detection and fallback simulation.
    """
    result = await sandbox.execute(name, params)
    return result

async def main():
    sandbox = ToolSandbox()
    print("=== External Tool Connectivity Check ===\n")
    for tool_name, params in TOOLS_TO_CHECK.items():
        print(f"Checking {tool_name}...", end=" ")
        try:
            result = await check_tool(sandbox, tool_name, params)
            if result.success:
                print("✅ SUCCESS")
                # Show a trimmed version of the output for quick debugging
                output_preview = (result.output[:200] + "...") if len(result.output) > 200 else result.output
                print(f"    Output: {output_preview}\n")
            else:
                print("⚠️ FAILED")
                print(f"    Error: {result.error}\n")
        except Exception as exc:
            print("❌ EXCEPTION")
            print(f"    Exception: {exc}\n")

    print("=== Check Complete ===")

if __name__ == "__main__":
    # On Windows we need the selector event loop policy for compatibility.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
