from __future__ import annotations

from typing import Any, Dict, List, Optional

from .types import ASTNodeInfo


FEATURE_HANDOFF_VERSION = "ast-handoff-v1"


def _stable_node_token(node: ASTNodeInfo) -> str:
    parent = node.parent_type if node.parent_type is not None else "ROOT"
    return f"{parent}>{node.type}"


def build_feature_handoff_payload(
    *,
    language: str,
    root_type: str,
    error_count: int,
    canonical_nodes: List[ASTNodeInfo],
    normalize_statements: bool,
    file_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a JSON-safe AST feature handoff payload for downstream similarity.

    Stable representation:
    - Feature token per node: "<parent_type_or_ROOT>><node_type>"

    Explainability metadata:
    - Byte spans + node labels for each token index to map matched features
      back to source code locations.
    """
    feature_tokens: List[str] = []
    token_spans: List[Dict[str, Any]] = []

    for idx, node in enumerate(canonical_nodes):
        token = _stable_node_token(node)
        feature_tokens.append(token)
        token_spans.append(
            {
                "token_index": idx,
                "token": token,
                "node_type": node.type,
                "parent_type": node.parent_type,
                "start_byte": node.start_byte,
                "end_byte": node.end_byte,
                "span_length": node.end_byte - node.start_byte,
            }
        )

    return {
        "feature_version": FEATURE_HANDOFF_VERSION,
        "language": language,
        "root_type": root_type,
        "file_path": file_path,
        "parse_ok": error_count == 0,
        "error_count": error_count,
        "uses_canonical_nodes": True,
        "uses_statement_normalization": normalize_statements,
        "token_count": len(feature_tokens),
        "feature_tokens": feature_tokens,
        "token_spans": token_spans,
    }
