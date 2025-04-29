import asyncio
import shlex
import re
from typing import List, Dict, Any, Optional
import os

from .base import BaseTool, ToolResult
from ..config.settings import settings
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class ShellTool(BaseTool):
    name = "shell"
    description = "Execute shell commands safely"
    parameters_schema = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute"
            },
            "timeout": {
                "type": "integer",
                "description": "Command timeout in seconds",
                "default": 30
            },
            "working_dir": {
                "type": "string",
                "description": "Working directory for command execution",
                "default": "/workspace"
            }
        },
        "required": ["command"]
    }
    
    def __init__(self, workspace_dir: str = "/workspace") -> None:
        super().__init__()
        self.workspace_dir = workspace_dir
        self.allowed_commands = set(settings.allowed_shell_commands)
        
        if not os.path.exists(self.workspace_dir):
            os.makedirs(self.workspace_dir, exist_ok=True)
    
    def _is_command_allowed(self, command: str) -> bool:
        cmd_parts = shlex.split(command)
        if not cmd_parts:
            return False
        
        base_cmd = os.path.basename(cmd_parts[0])
        return base_cmd in self.allowed_commands
    
    async def execute(
        self,
        command: str,
        timeout: int = 30,
        working_dir: Optional[str] = None,
    ) -> ToolResult:
        if not command or not command.strip():
            return ToolResult(
                success=False,
                error="Empty command",
                result="Command cannot be empty"
            )
        
        if not self._is_command_allowed(command):
            cmd_parts = shlex.split(command)
            base_cmd = os.path.basename(cmd_parts[0]) if cmd_parts else "unknown"
            return ToolResult(
                success=False,
                error="Command not allowed",
                result=f"Command '{base_cmd}' is not in the allowed list: {', '.join(sorted(self.allowed_commands))}"
            )
        
        try:
            cmd_dir = working_dir or self.workspace_dir
            
            logger.debug(f"Executing shell command: {command}")
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cmd_dir,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                
                stdout_text = stdout.decode("utf-8", errors="replace").strip()
                stderr_text = stderr.decode("utf-8", errors="replace").strip()
                
                success = process.returncode == 0
                
                if success:
                    result = stdout_text
                    error = None
                else:
                    result = f"Command failed with exit code {process.returncode}\n\nSTDOUT:\n{stdout_text}\n\nSTDERR:\n{stderr_text}"
                    error = f"Command exit code: {process.returncode}"
                
                return ToolResult(
                    success=success,
                    result=result,
                    error=error,
                    metadata={
                        "command": command,
                        "exit_code": process.returncode,
                        "has_stderr": bool(stderr_text),
                        "stdout": stdout_text,
                        "stderr": stderr_text,
                    }
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except Exception:
                    pass
                
                return ToolResult(
                    success=False,
                    error="Command timeout",
                    result=f"Command timed out after {timeout} seconds"
                )
                
        except Exception as e:
            logger.error(f"Error executing shell command: {str(e)}")
            return ToolResult(
                success=False,
                error="Command execution error",
                result=f"Failed to execute command: {str(e)}"
            ) 