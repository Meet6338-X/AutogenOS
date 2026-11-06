"""
AutogenOS Modular Block System: Base Block Architecture & Decorators.
Defines the atomic building blocks (Tools, Agents, Memory, Actions, Bridges, Evaluators)
enabling dynamic hot-swapping, runtime registration, removal, and updates of system capabilities.
"""

from __future__ import annotations
import time
import inspect
import asyncio
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type
from pydantic import BaseModel, Field


class BlockType(str, Enum):
    TOOL = "TOOL"
    AGENT = "AGENT"
    MEMORY = "MEMORY"
    PERCEPTION = "PERCEPTION"
    ACTION = "ACTION"
    BRIDGE = "BRIDGE"
    EVAL = "EVAL"
    WORKFLOW = "WORKFLOW"
    CUSTOM = "CUSTOM"


class BlockStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    ERROR = "ERROR"
    UNINITIALIZED = "UNINITIALIZED"


class BlockMetadata(BaseModel):
    block_id: str
    block_type: BlockType
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = "AutogenOS Core"
    dependencies: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    parameters_schema: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    status: BlockStatus = BlockStatus.UNINITIALIZED
    created_at: float = Field(default_factory=time.time)


class BaseBlock:
    """
    Abstract Base Class for all modular building blocks in AutogenOS.
    """

    def __init__(
        self,
        block_id: str,
        block_type: BlockType = BlockType.TOOL,
        name: Optional[str] = None,
        version: str = "1.0.0",
        description: str = "",
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        parameters_schema: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
    ):
        self.metadata = BlockMetadata(
            block_id=block_id,
            block_type=block_type,
            name=name or block_id,
            version=version,
            description=description,
            dependencies=dependencies or [],
            tags=tags or [],
            parameters_schema=parameters_schema or {},
            enabled=enabled,
            status=BlockStatus.ACTIVE if enabled else BlockStatus.DISABLED,
        )

    @property
    def block_id(self) -> str:
        return self.metadata.block_id

    @property
    def block_type(self) -> BlockType:
        return self.metadata.block_type

    @property
    def is_enabled(self) -> bool:
        return self.metadata.enabled and self.metadata.status == BlockStatus.ACTIVE

    def enable(self) -> None:
        self.metadata.enabled = True
        self.metadata.status = BlockStatus.ACTIVE

    def disable(self) -> None:
        self.metadata.enabled = False
        self.metadata.status = BlockStatus.DISABLED

    async def initialize(self) -> None:
        """Lifecycle hook called upon block registration."""
        pass

    async def execute(self, *args, **kwargs) -> Any:
        """Executes the block's core capability."""
        raise NotImplementedError("Subclasses of BaseBlock must implement execute()")

    async def shutdown(self) -> None:
        """Lifecycle hook called when the block is removed or the runtime exits."""
        pass

    async def health_check(self) -> Dict[str, Any]:
        """Returns health telemetry for this block."""
        return {
            "block_id": self.block_id,
            "status": self.metadata.status.value,
            "healthy": self.is_enabled,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializes block metadata to dictionary."""
        return self.metadata.model_dump()


class FunctionalBlock(BaseBlock):
    """
    Wraps a standalone Python function or coroutine as an executable BaseBlock.
    """

    def __init__(
        self,
        func: Callable[..., Any],
        block_id: str,
        block_type: BlockType = BlockType.TOOL,
        name: Optional[str] = None,
        version: str = "1.0.0",
        description: str = "",
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        enabled: bool = True,
    ):
        doc = description or (func.__doc__ or "").strip()
        super().__init__(
            block_id=block_id,
            block_type=block_type,
            name=name or func.__name__,
            version=version,
            description=doc,
            dependencies=dependencies,
            tags=tags,
            enabled=enabled,
        )
        self.func = func
        self._is_coroutine = inspect.iscoroutinefunction(func)

    async def execute(self, *args, **kwargs) -> Any:
        if not self.is_enabled:
            raise RuntimeError(f"Cannot execute disabled block '{self.block_id}'")
        try:
            if self._is_coroutine:
                return await self.func(*args, **kwargs)
            else:
                return self.func(*args, **kwargs)
        except Exception as e:
            self.metadata.status = BlockStatus.ERROR
            raise e


def block(
    block_id: str,
    block_type: BlockType = BlockType.TOOL,
    name: Optional[str] = None,
    version: str = "1.0.0",
    description: str = "",
    dependencies: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    enabled: bool = True,
):
    """
    Decorator to wrap any Python function or class into an AutogenOS Block.
    """
    def decorator(target: Any) -> Any:
        if inspect.isfunction(target):
            b = FunctionalBlock(
                func=target,
                block_id=block_id,
                block_type=block_type,
                name=name,
                version=version,
                description=description,
                dependencies=dependencies,
                tags=tags,
                enabled=enabled,
            )
            target.__autogenos_block__ = b
            return target
        elif inspect.isclass(target) and issubclass(target, BaseBlock):
            # Class-level attributes
            target._default_block_id = block_id
            target._default_block_type = block_type
            return target
        else:
            raise TypeError("@block decorator can only be applied to functions or subclasses of BaseBlock")

    return decorator
