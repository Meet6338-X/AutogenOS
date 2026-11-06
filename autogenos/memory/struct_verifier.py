"""
StructAgent & SolveBind Causal Verification Engine.
Enforces deterministic environmental grounding over digital task execution.
Gives bounded failure attribution if verification fails, preventing hallucinated task completion.
"""

from __future__ import annotations
import re
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from autogenos.core.state import DeterministicEvidence, EvidenceType


class StructAgentVerifier:
    """
    Evaluates proposed state transitions against deterministic environmental evidence.
    """

    @staticmethod
    def verify_shell_execution(
        exit_code: int,
        output_text: str,
        expected_exit_code: int = 0,
        expected_patterns: Optional[List[str]] = None
    ) -> DeterministicEvidence:
        """Verifies shell execution return code and output regex."""
        passed = (exit_code == expected_exit_code)
        failures = []

        if not passed:
            failures.append(f"Exit code mismatch: expected {expected_exit_code}, got {exit_code}")

        if expected_patterns:
            for pattern in expected_patterns:
                if not re.search(pattern, output_text, re.MULTILINE):
                    passed = False
                    failures.append(f"Expected pattern '{pattern}' not found in output.")

        return DeterministicEvidence(
            evidence_type=EvidenceType.SHELL_OUTPUT,
            source_target="shell_execution",
            raw_payload=output_text[:500],
            passed=passed,
            details={"exit_code": exit_code, "failures": failures}
        )

    @staticmethod
    def verify_file_hash(
        file_path: str | Path,
        expected_sha256: Optional[str] = None
    ) -> DeterministicEvidence:
        """Verifies file existence and SHA-256 hash."""
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            return DeterministicEvidence(
                evidence_type=EvidenceType.FILE_HASH,
                source_target=str(file_path),
                raw_payload="FileDoesNotExist",
                passed=False,
                details={"error": f"Path {file_path} not found"}
            )

        h = hashlib.sha256()
        with open(p, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        digest = h.hexdigest()

        passed = True
        if expected_sha256 and digest.lower() != expected_sha256.lower():
            passed = False

        return DeterministicEvidence(
            evidence_type=EvidenceType.FILE_HASH,
            source_target=str(file_path),
            raw_payload=f"sha256:{digest}",
            verified_hash=digest,
            passed=passed,
            details={"computed_hash": digest, "expected_hash": expected_sha256}
        )

    @staticmethod
    def verify_accessibility_node(
        ax_nodes: List[Dict[str, Any]],
        target_role: str,
        target_name_regex: str
    ) -> DeterministicEvidence:
        """Verifies that target accessibility element exists in AX tree."""
        matched = False
        match_details = {}

        for node in ax_nodes:
            role = str(node.get("role", "")).lower()
            name = str(node.get("name", {}).get("value", node.get("name", "")))
            if target_role.lower() in role and re.search(target_name_regex, name, re.IGNORECASE):
                matched = True
                match_details = {"nodeId": node.get("nodeId"), "role": role, "name": name}
                break

        return DeterministicEvidence(
            evidence_type=EvidenceType.ACCESSIBILITY_TREE,
            source_target="accessibility_tree",
            raw_payload=str(match_details),
            passed=matched,
            details=match_details
        )
