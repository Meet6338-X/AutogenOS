"""
AutogenOS Modular Block System.
Enables plug-and-play addition, removal, hot-swapping, and execution of features,
tools, agents, perception pipelines, and evaluators.
"""

from autogenos.blocks.base import (
    BlockType,
    BlockStatus,
    BlockMetadata,
    BaseBlock,
    FunctionalBlock,
    block,
)
from autogenos.blocks.registry import BlockRegistry
from autogenos.blocks.manager import BlockManager
from autogenos.blocks.standard import (
    ShellExecutionBlock,
    FileHashVerificationBlock,
    OfflineTTSBlock,
    BrowserScraperBlock,
    SystemDoctorBlock,
    BenchmarkEvalBlock,
    NotificationAlertBlock,
    MeetingJoinerBlock,
)

__all__ = [
    "BlockType",
    "BlockStatus",
    "BlockMetadata",
    "BaseBlock",
    "FunctionalBlock",
    "block",
    "BlockRegistry",
    "BlockManager",
    "ShellExecutionBlock",
    "FileHashVerificationBlock",
    "OfflineTTSBlock",
    "BrowserScraperBlock",
    "SystemDoctorBlock",
    "BenchmarkEvalBlock",
    "NotificationAlertBlock",
    "MeetingJoinerBlock",
]
