"""
AutogenOS Modular Block System: Central Block Registry.
Manages block registration, dependency validation, hot-swapping, filtering, and serialization.
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from autogenos.blocks.base import BaseBlock, BlockType, BlockStatus, BlockMetadata

logger = logging.getLogger("autogenos.blocks")


class BlockRegistry:
    """
    Central repository of all modular feature blocks in the AutogenOS ecosystem.
    """

    def __init__(self, manifest_path: Optional[str] = None):
        self._blocks: Dict[str, BaseBlock] = {}
        self._listeners: List[Callable[[str, str, BaseBlock], None]] = []
        self.manifest_path = Path(manifest_path or ".autogenos/blocks_manifest.json")

    def register(self, block: BaseBlock, enable: bool = True) -> BaseBlock:
        """
        Registers a new block or hot-swaps an existing block.
        """
        if not isinstance(block, BaseBlock):
            raise TypeError(f"Expected BaseBlock instance, got {type(block)}")

        if enable:
            block.enable()
        else:
            block.disable()

        old_block = self._blocks.get(block.block_id)
        self._blocks[block.block_id] = block

        event = "UPDATE" if old_block else "REGISTER"
        self._emit_event(event, block.block_id, block)
        logger.info(f"Block '{block.block_id}' ({block.block_type.value}) {event.lower()}ed successfully.")
        return block

    def unregister(self, block_id: str) -> Optional[BaseBlock]:
        """
        Removes a block from the registry.
        """
        block = self._blocks.pop(block_id, None)
        if block:
            self._emit_event("UNREGISTER", block_id, block)
            logger.info(f"Block '{block_id}' unregistered successfully.")
        return block

    def get(self, block_id: str) -> Optional[BaseBlock]:
        """Retrieves a block by its unique identifier."""
        return self._blocks.get(block_id)

    def enable(self, block_id: str) -> bool:
        """Enables an existing block."""
        block = self._blocks.get(block_id)
        if not block:
            return False
        block.enable()
        self._emit_event("ENABLE", block_id, block)
        return True

    def disable(self, block_id: str) -> bool:
        """Disables an existing block without removing it."""
        block = self._blocks.get(block_id)
        if not block:
            return False
        block.disable()
        self._emit_event("DISABLE", block_id, block)
        return True

    def list_blocks(
        self,
        block_type: Optional[BlockType] = None,
        enabled_only: bool = False,
        tag: Optional[str] = None
    ) -> List[BaseBlock]:
        """Queries registered blocks filtered by type, enabled status, or tags."""
        blocks = list(self._blocks.values())

        if block_type is not None:
            blocks = [b for b in blocks if b.block_type == block_type]

        if enabled_only:
            blocks = [b for b in blocks if b.is_enabled]

        if tag is not None:
            blocks = [b for b in blocks if tag in b.metadata.tags]

        return sorted(blocks, key=lambda b: b.block_id)

    def count(self) -> int:
        return len(self._blocks)

    def validate_dependencies(self, block_id: str) -> List[str]:
        """
        Checks whether all dependencies for a block exist and are enabled.
        Returns list of missing/disabled dependency IDs.
        """
        block = self.get(block_id)
        if not block:
            return [f"Block '{block_id}' not found"]

        missing = []
        for dep_id in block.metadata.dependencies:
            dep_block = self.get(dep_id)
            if not dep_block:
                missing.append(f"Missing dependency '{dep_id}'")
            elif not dep_block.is_enabled:
                missing.append(f"Disabled dependency '{dep_id}'")
        return missing

    def check_circular_dependencies(self) -> Optional[List[str]]:
        """
        Detects if there are any cyclic dependencies among registered blocks.
        Returns cycle path if detected, else None.
        """
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        cycle_path: List[str] = []

        def dfs(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            b = self.get(node)
            deps = b.metadata.dependencies if b else []

            for dep in deps:
                if dep not in visited:
                    if dfs(dep, path + [dep]):
                        return True
                elif dep in rec_stack:
                    cycle_path.extend(path + [dep])
                    return True

            rec_stack.remove(node)
            return False

        for block_id in self._blocks:
            if block_id not in visited:
                if dfs(block_id, [block_id]):
                    return cycle_path
        return None

    def add_listener(self, callback: Callable[[str, str, BaseBlock], None]) -> None:
        """Subscribes an event listener to registry mutations."""
        self._listeners.append(callback)

    def _emit_event(self, event_type: str, block_id: str, block: BaseBlock) -> None:
        for listener in self._listeners:
            try:
                listener(event_type, block_id, block)
            except Exception as e:
                logger.debug(f"Block event listener error: {e}")

    def save_manifest(self, path: Optional[str] = None) -> None:
        """Persists registered blocks metadata to JSON file."""
        target = Path(path or self.manifest_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "version": "1.0.0",
            "blocks_count": len(self._blocks),
            "blocks": {bid: b.to_dict() for bid, b in self._blocks.items()}
        }
        target.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def to_catalog(self) -> Dict[str, Any]:
        """Returns catalog summary of all registered blocks."""
        by_type: Dict[str, int] = {}
        for b in self._blocks.values():
            t_name = b.block_type.value
            by_type[t_name] = by_type.get(t_name, 0) + 1

        return {
            "total_blocks": len(self._blocks),
            "active_blocks": sum(1 for b in self._blocks.values() if b.is_enabled),
            "disabled_blocks": sum(1 for b in self._blocks.values() if not b.is_enabled),
            "by_type": by_type,
            "blocks": [b.to_dict() for b in self.list_blocks()]
        }
