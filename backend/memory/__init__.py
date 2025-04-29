import logging
from typing import Dict, Any, Optional, List

from .memory_manager import MemoryManager

logger = logging.getLogger(__name__)

# Create singleton instance
memory_manager = MemoryManager() 