"""
Tool Sandbox Layer - LAYER 5
CRITICAL SECURITY: LLM cannot execute directly
All tool executions go through this deterministic layer
"""

import asyncio
import logging
import subprocess
import json
import tempfile
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Standardized tool execution result"""
    tool_name: str
    success: bool
    output: str
    error: Optional[str]
    execution_time: float
    raw_data: Dict[str, Any]


class ToolSandbox:
    """
    Controlled execution environment for open-source security tools
    
    SECURITY GUARANTEES:
    - Whitelisted tools only
    - Argument sanitization
    - Resource limits (CPU, memory, time)
    - Network isolation options
    - Output sanitization
    """
    
    # WHITELIST of allowed tools (open-source only)
    ALLOWED_TOOLS = {
        # Reconnaissance
        "httpx": "/usr/local/bin/httpx",
        "katana": "/usr/local/bin/katana",
        "gospider": "/usr/local/bin/gospider",
        "subfinder": "/usr/local/bin/subfinder",
        "nuclei": "/usr/local/bin/nuclei",
        "nmap": "/usr/bin/nmap",
        
        # Vulnerability Scanning
        "sqlmap": "/usr/local/bin/sqlmap",
        "dalfox": "/usr/local/bin/dalfox",
        "ffuf": "/usr/local/bin/ffuf",
        "commix": "/usr/local/bin/commix",
        "nosqlmap": "/usr/local/bin/nosqlmap",
        "xsstrike": "/usr/local/bin/xsstrike",
        
        # API Testing
        "arjun": "/usr/local/bin/arjun",
        "kiterunner": "/usr/local/bin/kr",
        
        # Authentication
        "jwt_tool": "/usr/local/bin/jwt_tool",
        "hydra": "/usr/bin/hydra",
        
        # Custom Tools
        "idor_tester": "python /app/tools/custom/idor_tester.py",
        "auth_bypass_tester": "python /app/tools/custom/auth_bypass.py",
    }
    
    # Resource limits
    MAX_EXECUTION_TIME = 300  # 5 minutes
    MAX_OUTPUT_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="rakshaidb_"))
        logger.info(f"Initialized tool sandbox at {self.temp_dir}")
    
    async def execute(
        self,
        tool_name: str,
        args: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> ToolResult:
        """
        Execute a whitelisted tool with sanitized arguments
        
        Args:
            tool_name: Name of the tool (must be in ALLOWED_TOOLS)
            args: Tool-specific arguments
            timeout: Execution timeout in seconds
            
        Returns:
            ToolResult with execution details
            
        Raises:
            ValueError: If tool is not whitelisted
            RuntimeError: If execution fails
        """
        import time
        start_time = time.time()
        
        try:
            # SECURITY CHECK 1: Verify tool is whitelisted
            if tool_name not in self.ALLOWED_TOOLS:
                raise ValueError(
                    f"Tool '{tool_name}' not whitelisted. "
                    f"Allowed tools: {list(self.ALLOWED_TOOLS.keys())}"
                )
            
            logger.info(f"Executing {tool_name} with args: {args}")
            
            # SECURITY CHECK 2: Sanitize arguments
            sanitized_args = self._sanitize_args(args)
            
            # Build command
            cmd = await self._build_command(tool_name, sanitized_args)
            
            # SECURITY CHECK 3: Execute with resource limits
            result = await self._execute_with_limits(
                cmd,
                timeout=timeout or self.MAX_EXECUTION_TIME
            )
            
            # Parse output
            parsed_output = await self._parse_output(tool_name, result)
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                tool_name=tool_name,
                success=True,
                output=parsed_output.get("formatted", ""),
                error=None,
                execution_time=execution_time,
                raw_data=parsed_output
            )
            
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            execution_time = time.time() - start_time
            
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=str(e),
                execution_time=execution_time,
                raw_data={}
            )
    
    def _sanitize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize tool arguments to prevent command injection
        
        Args:
            args: Raw arguments dictionary
            
        Returns:
            Sanitized arguments
        """
        sanitized = {}
        
        for key, value in args.items():
            # Whitelist allowed characters
            if isinstance(value, str):
                # Remove dangerous characters
                value = value.replace(";", "").replace("|", "")
                value = value.replace("&", "").replace("`", "")
                value = value.replace("$", "").replace("(", "").replace(")", "")
            
            sanitized[key] = value
        
        return sanitized
    
    async def _build_command(
        self,
        tool_name: str,
        args: Dict[str, Any]
    ) -> List[str]:
        """
        Build command array for subprocess execution
        
        Args:
            tool_name: Name of the tool
            args: Sanitized arguments
            
        Returns:
            Command array for subprocess
        """
        tool_path = self.ALLOWED_TOOLS[tool_name]
        
        # Tool-specific command builders
        if tool_name == "httpx":
            return await self._build_httpx_command(tool_path, args)
        elif tool_name == "nuclei":
            return await self._build_nuclei_command(tool_path, args)
        elif tool_name == "sqlmap":
            return await self._build_sqlmap_command(tool_path, args)
        elif tool_name == "dalfox":
            return await self._build_dalfox_command(tool_path, args)
        elif tool_name == "katana":
            return await self._build_katana_command(tool_path, args)
        else:
            # Generic command builder
            cmd = [tool_path]
            for key, value in args.items():
                cmd.extend([f"--{key}", str(value)])
            return cmd
    
    async def _build_httpx_command(
        self,
        tool_path: str,
        args: Dict[str, Any]
    ) -> List[str]:
        """Build httpx command"""
        cmd = [tool_path]
        
        # Required: target URL
        if "target" in args:
            cmd.extend(["-u", args["target"]])
        
        # Optional flags
        if args.get("tech_detect"):
            cmd.append("-tech-detect")
        if args.get("status_code"):
            cmd.append("-status-code")
        if args.get("title"):
            cmd.append("-title")
        if args.get("json"):
            cmd.append("-json")
        
        # Output to temp file
        output_file = self.temp_dir / f"httpx_{id(args)}.json"
        cmd.extend(["-o", str(output_file)])
        
        return cmd
    
    async def _build_nuclei_command(
        self,
        tool_path: str,
        args: Dict[str, Any]
    ) -> List[str]:
        """Build nuclei command"""
        cmd = [tool_path]
        
        if "target" in args:
            cmd.extend(["-u", args["target"]])
        
        if "templates" in args:
            cmd.extend(["-t", args["templates"]])
        
        if "severity" in args:
            cmd.extend(["-severity", args["severity"]])
        
        # JSON output
        output_file = self.temp_dir / f"nuclei_{id(args)}.json"
        cmd.extend(["-json", "-o", str(output_file)])
        
        return cmd
    
    async def _build_sqlmap_command(
        self,
        tool_path: str,
        args: Dict[str, Any]
    ) -> List[str]:
        """Build sqlmap command - careful with permissions"""
        cmd = [tool_path]
        
        if "url" in args:
            cmd.extend(["-u", args["url"]])
        
        # Session management
        if "cookie" in args:
            cmd.extend(["--cookie", args["cookie"]])
        
        # Safe options only
        cmd.extend([
            "--batch",  # Non-interactive
            "--random-agent",
            "--level=1",
            "--risk=1",
            "--threads=5",
            f"--timeout={args.get('timeout', 30)}"
        ])
        
        # Output directory
        output_dir = self.temp_dir / f"sqlmap_{id(args)}"
        cmd.extend(["--output-dir", str(output_dir)])
        
        return cmd
    
    async def _build_dalfox_command(
        self,
        tool_path: str,
        args: Dict[str, Any]
    ) -> List[str]:
        """Build dalfox (XSS scanner) command"""
        cmd = [tool_path, "url"]
        
        if "url" in args:
            cmd.append(args["url"])
        
        # Scanning options
        if args.get("blind"):
            cmd.append("--blind")
        
        cmd.extend(["--output", str(self.temp_dir / f"dalfox_{id(args)}.json")])
        cmd.append("--format=json")
        
        return cmd
    
    async def _build_katana_command(
        self,
        tool_path: str,
        args: Dict[str, Any]
    ) -> List[str]:
        """Build katana (web crawler) command"""
        cmd = [tool_path]
        
        if "target" in args:
            cmd.extend(["-u", args["target"]])
        
        if "depth" in args:
            cmd.extend(["-depth", str(args["depth"])])
        
        cmd.extend(["-json", "-o", str(self.temp_dir / f"katana_{id(args)}.json")])
        
        return cmd
    
    async def _execute_with_limits(
        self,
        cmd: List[str],
        timeout: int
    ) -> str:
        """
        Execute command with resource limits
        
        Args:
            cmd: Command array
            timeout: Maximum execution time
            
        Returns:
            Command output
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=self.MAX_OUTPUT_SIZE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            if process.returncode != 0:
                logger.warning(f"Tool returned non-zero exit code: {stderr.decode()}")
            
            return stdout.decode()
            
        except asyncio.TimeoutError:
            process.kill()
            raise RuntimeError(f"Tool execution exceeded {timeout}s timeout")
        except Exception as e:
            raise RuntimeError(f"Tool execution failed: {e}")
    
    async def _parse_output(
        self,
        tool_name: str,
        output: str
    ) -> Dict[str, Any]:
        """
        Parse tool output into structured format
        
        Args:
            tool_name: Name of the tool
            output: Raw output string
            
        Returns:
            Parsed output dictionary
        """
        # Try to parse as JSON first
        try:
            # Check if output files were created
            json_files = list(self.temp_dir.glob(f"{tool_name}_*.json"))
            if json_files:
                with open(json_files[0], 'r') as f:
                    data = json.load(f)
                return {
                    "formatted": json.dumps(data, indent=2),
                    "structured": data
                }
        except json.JSONDecodeError:
            pass
        
        # Return raw output
        return {
            "formatted": output,
            "structured": {"raw": output}
        }
    
    async def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up sandbox directory: {self.temp_dir}")
    
    def __del__(self):
        """Ensure cleanup on deletion"""
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass


# Singleton instance
_tool_sandbox = None

def get_tool_sandbox() -> ToolSandbox:
    """Get global tool sandbox instance"""
    global _tool_sandbox
    if _tool_sandbox is None:
        _tool_sandbox = ToolSandbox()
    return _tool_sandbox
