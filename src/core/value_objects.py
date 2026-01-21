from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass(frozen=True)
class ClassificationResult:
    """Immutable value object representing AI classification output."""

    topics: List[str]
    summary: str
    confidence: float
    model_used: str
    classified_at: datetime
