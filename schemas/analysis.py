from pydantic import BaseModel, Field
from typing import List, Dict, Any

class AnalysisSchema(BaseModel):
    files: List[Dict[str, Any]] = Field(default_factory=list)
    functions: List[Dict[str, Any]] = Field(default_factory=list)
    tests: List[Dict[str, Any]] = Field(default_factory=list)
    edge_cases: List[Dict[str, Any]] = Field(default_factory=list)
    signals: List[Dict[str, Any]] = Field(default_factory=list)
    signals_raw: List[Dict[str, Any]] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)
    test_ratio: float = 0.0
    severity_counts: Dict[str, Any] = Field(default_factory=dict)