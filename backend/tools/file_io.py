import os
import pathlib
from typing import List, Dict, Any, Optional

from .base import BaseTool, ToolResult
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class FileIOTool(BaseTool):
    name = "file_io"
    description = "Perform file operations like reading, writing, and listing files/directories"
    parameters_schema = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["read", "write", "list", "exists", "delete"],
                "description": "The file operation to perform"
            },
            "path": {
                "type": "string",
                "description": "The file or directory path"
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file (only for write operation)"
            },
            "recursive": {
                "type": "boolean",
                "description": "Whether to list directories recursively (only for list operation)",
                "default": False
            },
            "working_dir": {
                "type": "string",
                "description": "Working directory to use as base for relative paths",
                "default": "/workspace"
            }
        },
        "required": ["operation", "path"]
    }
    
    def __init__(self, workspace_dir: str = "/workspace") -> None:
        super().__init__()
        self.workspace_dir = workspace_dir
        if not os.path.exists(self.workspace_dir):
            os.makedirs(self.workspace_dir, exist_ok=True)
            logger.info(f"Created workspace directory: {self.workspace_dir}")
    
    def _normalize_path(self, path: str, working_dir: Optional[str] = None) -> str:
        base_dir = working_dir or self.workspace_dir
        
        if os.path.isabs(path):
            normalized_path = path
        else:
            normalized_path = os.path.normpath(os.path.join(base_dir, path))
        
        if not normalized_path.startswith(base_dir):
            raise ValueError(f"Path {path} is outside the allowed workspace directory")
        
        return normalized_path
    
    async def execute(
        self,
        operation: str,
        path: str,
        content: Optional[str] = None,
        recursive: bool = False,
        working_dir: Optional[str] = None,
    ) -> ToolResult:
        try:
            base_dir = working_dir or self.workspace_dir
            
            if not operation in ["read", "write", "list", "exists", "delete"]:
                return ToolResult(
                    success=False,
                    error="Invalid operation",
                    result=f"Operation '{operation}' not supported. Use 'read', 'write', 'list', 'exists', or 'delete'."
                )
            
            try:
                file_path = self._normalize_path(path, base_dir)
            except ValueError as e:
                return ToolResult(
                    success=False,
                    error="Path security error",
                    result=str(e)
                )
            
            if operation == "read":
                return await self._read_file(file_path)
            elif operation == "write":
                return await self._write_file(file_path, content)
            elif operation == "list":
                return await self._list_dir(file_path, recursive)
            elif operation == "exists":
                return await self._file_exists(file_path)
            elif operation == "delete":
                return await self._delete_file(file_path)
            
        except Exception as e:
            logger.error(f"Error in FileIOTool: {str(e)}")
            return ToolResult(
                success=False,
                error=f"File operation error",
                result=f"Failed to perform {operation}: {str(e)}"
            )
    
    async def _read_file(self, file_path: str) -> ToolResult:
        if not os.path.exists(file_path):
            return ToolResult(
                success=False,
                error="File not found",
                result=f"File does not exist: {file_path}"
            )
        
        if not os.path.isfile(file_path):
            return ToolResult(
                success=False,
                error="Not a file",
                result=f"Path is not a file: {file_path}"
            )
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return ToolResult(
                success=True,
                result=content,
                metadata={
                    "path": file_path,
                    "size": os.path.getsize(file_path),
                    "operation": "read"
                }
            )
        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                error="File encoding error",
                result=f"File is not text or has unknown encoding: {file_path}"
            )
    
    async def _write_file(self, file_path: str, content: Optional[str]) -> ToolResult:
        if content is None:
            return ToolResult(
                success=False,
                error="Missing content",
                result="Content parameter is required for write operation"
            )
        
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return ToolResult(
            success=True,
            result=f"File written successfully: {file_path}",
            metadata={
                "path": file_path,
                "size": len(content),
                "operation": "write"
            }
        )
    
    async def _list_dir(self, dir_path: str, recursive: bool) -> ToolResult:
        if not os.path.exists(dir_path):
            return ToolResult(
                success=False,
                error="Directory not found",
                result=f"Directory does not exist: {dir_path}"
            )
        
        if not os.path.isdir(dir_path):
            return ToolResult(
                success=False,
                error="Not a directory",
                result=f"Path is not a directory: {dir_path}"
            )
        
        if recursive:
            file_list = []
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), dir_path)
                    file_list.append(rel_path)
            
            result_text = "\n".join(sorted(file_list))
        else:
            entries = os.listdir(dir_path)
            formatted_entries = []
            
            for entry in sorted(entries):
                full_path = os.path.join(dir_path, entry)
                if os.path.isdir(full_path):
                    formatted_entries.append(f"{entry}/")
                else:
                    formatted_entries.append(entry)
            
            result_text = "\n".join(formatted_entries)
        
        return ToolResult(
            success=True,
            result=result_text,
            metadata={
                "path": dir_path,
                "recursive": recursive,
                "operation": "list"
            }
        )
    
    async def _file_exists(self, file_path: str) -> ToolResult:
        exists = os.path.exists(file_path)
        is_file = os.path.isfile(file_path) if exists else False
        is_dir = os.path.isdir(file_path) if exists else False
        
        return ToolResult(
            success=True,
            result=f"Path {'exists' if exists else 'does not exist'}: {file_path}",
            metadata={
                "path": file_path,
                "exists": exists,
                "is_file": is_file,
                "is_dir": is_dir,
                "operation": "exists"
            }
        )
    
    async def _delete_file(self, file_path: str) -> ToolResult:
        if not os.path.exists(file_path):
            return ToolResult(
                success=False,
                error="File not found",
                result=f"Path does not exist: {file_path}"
            )
        
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                result_text = f"File deleted: {file_path}"
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
                result_text = f"Empty directory deleted: {file_path}"
            else:
                return ToolResult(
                    success=False,
                    error="Unknown file type",
                    result=f"Path is neither a file nor an empty directory: {file_path}"
                )
            
            return ToolResult(
                success=True,
                result=result_text,
                metadata={
                    "path": file_path,
                    "operation": "delete"
                }
            )
        except OSError as e:
            return ToolResult(
                success=False,
                error="Delete error",
                result=f"Failed to delete: {str(e)}"
            ) 