from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ASTNodeInfo:
    type: str
    start_byte: int
    end_byte: int
    parent_type: Optional[str] = None
