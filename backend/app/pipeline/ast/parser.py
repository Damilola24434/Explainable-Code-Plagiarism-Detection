from __future__ import annotations

from typing import List, Tuple
from tree_sitter import Tree, Node

from .languages import make_parser
from .types import ASTNodeInfo


def parse_code(code: str, language: str) -> Tree:
    """
    Parse raw source code into a Tree-sitter Tree.
    Byte offsets in nodes refer to the UTF-8 encoded bytes of `code`.
    """
    parser = make_parser(language)
    return parser.parse((code or "").encode("utf-8"))


def collect_nodes_with_spans(
    tree: Tree,
    max_nodes: int = 50_000,
    include_unnamed_nodes: bool = True,
) -> List[ASTNodeInfo]:
    """
    Walk the AST and return nodes with byte offsets.

    By default this includes named and unnamed nodes (punctuation/operators).
    Set `include_unnamed_nodes=False` to reduce token noise for downstream
    similarity analysis.
    """
    out: List[ASTNodeInfo] = []
    root = tree.root_node

    stack: List[Tuple[Node, str | None]] = [(root, None)]  # (node, parent_type)

    while stack and len(out) < max_nodes:
        node, parent_type = stack.pop()

        if include_unnamed_nodes or node.is_named:
            out.append(
                ASTNodeInfo(
                    type=node.type,
                    start_byte=node.start_byte,
                    end_byte=node.end_byte,
                    parent_type=parent_type,
                )
            )

        # Push children reversed so traversal is left-to-right overall.
        children = node.children
        for child in reversed(children):
            stack.append((child, node.type))

    return out


def count_error_nodes(tree: Tree, max_nodes: int = 100_000) -> int:
    """
    Count parse-error indicators in the AST.

    Tree-sitter syntax failures are not always emitted as explicit `ERROR` nodes.
    Some grammars insert `MISSING` nodes during recovery. As a final fallback,
    if the root reports `has_error` but no concrete error/missing nodes are
    present, return 1.
    """
    root = tree.root_node
    stack = [root]
    errors = 0
    seen = 0

    while stack and seen < max_nodes:
        node = stack.pop()
        seen += 1

        # Explicit parser error node.
        if node.type == "ERROR":
            errors += 1
        # Missing tokens inserted during error recovery (common for bad syntax).
        elif getattr(node, "is_missing", False):
            errors += 1

        # Include named and unnamed children
        stack.extend(node.children)

    if errors == 0 and getattr(root, "has_error", False):
        return 1

    return errors


def parse_and_collect(
    code: str,
    language: str,
    max_nodes: int = 50_000,
    include_unnamed_nodes: bool = True,
    include_tree: bool = False,
) -> dict:
    """
    Convenience wrapper used by the pipeline/worker.

    Returns:
      {
        "language": str,
        "root_type": str,
        "nodes": List[ASTNodeInfo],
        "node_count": int,
        "include_unnamed_nodes": bool,
        "error_count": int,
        # Optional (internal use only)
        "tree": <Tree>,
      }
    """
    tree = parse_code(code, language)
    nodes = collect_nodes_with_spans(
        tree,
        max_nodes=max_nodes,
        include_unnamed_nodes=include_unnamed_nodes,
    )
    error_count = count_error_nodes(tree)
    result = {
        "language": (language or "").lower().strip(),
        "root_type": tree.root_node.type,
        "nodes": nodes,
        "node_count": len(nodes),
        "include_unnamed_nodes": include_unnamed_nodes,
        "error_count": error_count,
    }
    if include_tree:
        result["tree"] = tree
    return result
