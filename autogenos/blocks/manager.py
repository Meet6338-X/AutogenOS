"""
AutogenOS Modular Block System: Master Block Manager.
High-level orchestrator for loading, removing, updating, hot-swapping,
and executing dynamic feature blocks across the runtime.
"""

from __future__ import annotations
import sys
import types
import inspect
import logging
import textwrap
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from autogenos.blocks.base import BaseBlock, BlockType, FunctionalBlock
from autogenos.blocks.registry import BlockRegistry
from autogenos.blocks.standard import (
    ShellExecutionBlock,
    FileHashVerificationBlock,
    OfflineTTSBlock,
    BrowserScraperBlock,
    SystemDoctorBlock,
    BenchmarkEvalBlock,
    NotificationAlertBlock,
)

logger = logging.getLogger("autogenos.blocks")


class BlockManager:
    """
    High-level manager for dynamic component block lifecycle.
    """

    def __init__(self, registry: Optional[BlockRegistry] = None, auto_load_standard: bool = True):
        self.registry = registry or BlockRegistry()
        if auto_load_standard:
            self._load_standard_blocks()

    def _load_standard_blocks(self) -> None:
        """Registers default out-of-the-box system blocks."""
        standard_blocks = [
            ShellExecutionBlock(),
            FileHashVerificationBlock(),
            OfflineTTSBlock(),
            BrowserScraperBlock(),
            SystemDoctorBlock(),
            BenchmarkEvalBlock(),
            NotificationAlertBlock(),
        ]
        for b in standard_blocks:
            self.registry.register(b)

    def register_block(self, block: BaseBlock, enable: bool = True) -> BaseBlock:
        return self.registry.register(block, enable=enable)

    def remove_block(self, block_id: str) -> Optional[BaseBlock]:
        return self.registry.unregister(block_id)

    def enable_block(self, block_id: str) -> bool:
        return self.registry.enable(block_id)

    def disable_block(self, block_id: str) -> bool:
        return self.registry.disable(block_id)

    def get_block(self, block_id: str) -> Optional[BaseBlock]:
        return self.registry.get(block_id)

    def list_blocks(
        self,
        block_type: Optional[BlockType] = None,
        enabled_only: bool = False,
        tag: Optional[str] = None
    ) -> List[BaseBlock]:
        return self.registry.list_blocks(block_type=block_type, enabled_only=enabled_only, tag=tag)

    async def execute_block(self, block_id: str, *args, **kwargs) -> Any:
        block = self.registry.get(block_id)
        if not block:
            raise KeyError(f"Block '{block_id}' not found in registry")
        if not block.is_enabled:
            raise RuntimeError(f"Block '{block_id}' is currently disabled")

        missing = self.registry.validate_dependencies(block_id)
        if missing:
            raise RuntimeError(f"Cannot execute '{block_id}'. Unresolved dependencies: {missing}")

        return await block.execute(*args, **kwargs)

    def add_block_from_code(
        self,
        python_code: str,
        block_id: Optional[str] = None,
        block_type: BlockType = BlockType.CUSTOM
    ) -> BaseBlock:
        """
        Dynamically compiles Python source code into a live registered block.
        """
        clean_code = textwrap.dedent(python_code).strip()
        module_name = f"autogenos_dynamic_block_{abs(hash(clean_code))}"
        mod = types.ModuleType(module_name)
        mod.__file__ = f"<{module_name}>"

        exec(clean_code, mod.__dict__)

        # Check for BaseBlock subclasses or instances
        found_block: Optional[BaseBlock] = None

        for val in mod.__dict__.values():
            if isinstance(val, BaseBlock):
                found_block = val
                break
            elif inspect.isclass(val) and issubclass(val, BaseBlock) and val is not BaseBlock and val is not FunctionalBlock:
                # Instantiate class
                default_id = getattr(val, "_default_block_id", block_id or f"custom.{val.__name__.lower()}")
                default_type = getattr(val, "_default_block_type", block_type)
                try:
                    found_block = val()
                except Exception:
                    found_block = val(block_id=default_id, block_type=default_type)
                break
            elif inspect.isfunction(val) and hasattr(val, "__autogenos_block__"):
                found_block = getattr(val, "__autogenos_block__")
                break

        # Fallback: wrap first defined function
        if not found_block:
            for name, val in mod.__dict__.items():
                if inspect.isfunction(val) and not name.startswith("_"):
                    b_id = block_id or f"custom.func.{name}"
                    found_block = FunctionalBlock(
                        func=val,
                        block_id=b_id,
                        block_type=block_type,
                        name=name,
                        description=(val.__doc__ or f"Dynamic functional block for {name}").strip()
                    )
                    break

        if not found_block:
            raise ValueError("No valid BaseBlock, @block function, or callable found in supplied code.")

        self.registry.register(found_block)
        return found_block

    def add_block_from_file(self, file_path: str | Path) -> BaseBlock:
        """Loads and registers a block from a .py file on disk."""
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"Block file not found: {file_path}")

        code = p.read_text(encoding="utf-8")
        b_id = f"custom.file.{p.stem}"
        return self.add_block_from_code(code, block_id=b_id)

    def get_catalog(self) -> Dict[str, Any]:
        return self.registry.to_catalog()
