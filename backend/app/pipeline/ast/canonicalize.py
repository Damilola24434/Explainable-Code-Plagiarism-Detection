from __future__ import annotations

from typing import Dict, List, Tuple

from tree_sitter import Node, Tree

from .types import ASTNodeInfo


IDENTIFIER_NODE_TYPES = {
    "identifier",
    "field_identifier",
    "namespace_identifier",
    "property_identifier",
    "type_identifier",
}

STRING_LITERAL_NODE_TYPES = {
    "string",
    "string_literal",
    "string_content",
}

CHAR_LITERAL_NODE_TYPES = {
    "char_literal",
    "character_literal",
}

NUMERIC_LITERAL_NODE_TYPES = {
    "integer",
    "integer_literal",
    "decimal_integer_literal",
    "hex_integer_literal",
    "octal_integer_literal",
    "binary_integer_literal",
    "float",
    "float_literal",
    "decimal_floating_point_literal",
}

BOOL_LITERAL_TEXT = {"true", "false"}
NULL_LITERAL_TEXT = {"null", "none"}

# Conservative statement-family labels used to reduce syntactic variance while
# preserving core control/data-flow structure.
STATEMENT_NORMALIZATION_MAP = {
    "python": {
        "function_definition": "STMT_FUNCTION_DEF",
        "class_definition": "STMT_CLASS_DEF",
        "assignment": "STMT_ASSIGN",
        "augmented_assignment": "STMT_ASSIGN",
        "return_statement": "STMT_RETURN",
        "if_statement": "STMT_IF",
        "for_statement": "STMT_FOR",
        "while_statement": "STMT_WHILE",
        "break_statement": "STMT_BREAK",
        "continue_statement": "STMT_CONTINUE",
        "expression_statement": "STMT_EXPR",
        "pass_statement": "STMT_PASS",
    },
    "java": {
        "method_declaration": "STMT_FUNCTION_DEF",
        "constructor_declaration": "STMT_FUNCTION_DEF",
        "class_declaration": "STMT_CLASS_DEF",
        "local_variable_declaration": "STMT_ASSIGN",
        "return_statement": "STMT_RETURN",
        "if_statement": "STMT_IF",
        "for_statement": "STMT_FOR",
        "enhanced_for_statement": "STMT_FOR",
        "while_statement": "STMT_WHILE",
        "do_statement": "STMT_WHILE",
        "break_statement": "STMT_BREAK",
        "continue_statement": "STMT_CONTINUE",
        "expression_statement": "STMT_EXPR",
    },
    "cpp": {
        "function_definition": "STMT_FUNCTION_DEF",
        "declaration": "STMT_ASSIGN",
        "init_declarator": "STMT_ASSIGN",
        "assignment_expression": "STMT_ASSIGN",
        "return_statement": "STMT_RETURN",
        "if_statement": "STMT_IF",
        "for_statement": "STMT_FOR",
        "while_statement": "STMT_WHILE",
        "do_statement": "STMT_WHILE",
        "break_statement": "STMT_BREAK",
        "continue_statement": "STMT_CONTINUE",
        "expression_statement": "STMT_EXPR",
        "class_specifier": "STMT_CLASS_DEF",
        "struct_specifier": "STMT_CLASS_DEF",
    },
    "c": {
        "function_definition": "STMT_FUNCTION_DEF",
        "declaration": "STMT_ASSIGN",
        "init_declarator": "STMT_ASSIGN",
        "assignment_expression": "STMT_ASSIGN",
        "return_statement": "STMT_RETURN",
        "if_statement": "STMT_IF",
        "for_statement": "STMT_FOR",
        "while_statement": "STMT_WHILE",
        "do_statement": "STMT_WHILE",
        "break_statement": "STMT_BREAK",
        "continue_statement": "STMT_CONTINUE",
        "expression_statement": "STMT_EXPR",
        "struct_specifier": "STMT_CLASS_DEF",
    },
    "javascript": {
        "function_declaration": "STMT_FUNCTION_DEF",
        "method_definition": "STMT_FUNCTION_DEF",
        "class_declaration": "STMT_CLASS_DEF",
        "lexical_declaration": "STMT_ASSIGN",
        "variable_declaration": "STMT_ASSIGN",
        "variable_declarator": "STMT_ASSIGN",
        "assignment_expression": "STMT_ASSIGN",
        "return_statement": "STMT_RETURN",
        "if_statement": "STMT_IF",
        "for_statement": "STMT_FOR",
        "for_in_statement": "STMT_FOR",
        "while_statement": "STMT_WHILE",
        "do_statement": "STMT_WHILE",
        "break_statement": "STMT_BREAK",
        "continue_statement": "STMT_CONTINUE",
        "expression_statement": "STMT_EXPR",
    },
}


def _node_text(source_bytes: bytes, node: Node) -> str:
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="ignore")


def _canonical_label(
    node: Node,
    node_text: str,
    identifier_map: Dict[str, str],
) -> str:
    node_type = node.type
    lowered_text = node_text.strip().lower()

    if node_type in IDENTIFIER_NODE_TYPES:
        if node_text not in identifier_map:
            identifier_map[node_text] = f"IDENT_{len(identifier_map) + 1}"
        return identifier_map[node_text]

    if node_type in STRING_LITERAL_NODE_TYPES:
        return "STR_LIT"

    if node_type in CHAR_LITERAL_NODE_TYPES:
        return "CHAR_LIT"

    if node_type in NUMERIC_LITERAL_NODE_TYPES:
        return "NUM_LIT"

    if lowered_text in BOOL_LITERAL_TEXT:
        return "BOOL_LIT"

    if lowered_text in NULL_LITERAL_TEXT:
        return "NULL_LIT"

    # Catch-all for grammars that encode literal categories as *_literal names.
    if node_type.endswith("_literal"):
        return "LIT"

    return node_type


def _normalize_statement_label(label: str, node_type: str, language: str) -> str:
    lang = (language or "").lower().strip()
    if lang not in STATEMENT_NORMALIZATION_MAP:
        return label
    return STATEMENT_NORMALIZATION_MAP[lang].get(node_type, label)


def canonicalize_nodes_with_spans(
    tree: Tree,
    code: str,
    language: str,
    max_nodes: int = 50_000,
    include_unnamed_nodes: bool = True,
    normalize_statements: bool = False,
) -> Tuple[List[ASTNodeInfo], Dict[str, str]]:
    """
    Walk the AST and return canonicalized node labels with original byte spans.

    Canonicalization rules:
    - Alpha-renaming identifiers into IDENT_1, IDENT_2, ...
    - Normalizing literals into STR_LIT / CHAR_LIT / NUM_LIT / BOOL_LIT / NULL_LIT
    - Optional statement-family normalization into STMT_* labels
    """
    source_bytes = (code or "").encode("utf-8")
    out: List[ASTNodeInfo] = []
    identifier_map: Dict[str, str] = {}
    root = tree.root_node

    stack: List[Tuple[Node, str | None]] = [(root, None)]  # (node, parent_label)

    while stack and len(out) < max_nodes:
        node, parent_label = stack.pop()
        label = _canonical_label(node, _node_text(source_bytes, node), identifier_map)
        if normalize_statements:
            label = _normalize_statement_label(label, node.type, language)

        if include_unnamed_nodes or node.is_named:
            out.append(
                ASTNodeInfo(
                    type=label,
                    start_byte=node.start_byte,
                    end_byte=node.end_byte,
                    parent_type=parent_label,
                )
            )

        # Push children reversed so traversal is left-to-right overall.
        for child in reversed(node.children):
            stack.append((child, label))

    return out, identifier_map
