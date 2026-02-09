# schemas/analysis.py
from pydantic import BaseModel
from typing import List, Dict, Any


class AnalysisSchema(BaseModel):
    files: List[Dict[str, Any]]
    functions: List[Dict[str, Any]]
    tests: List[Dict[str, Any]]
    edge_cases: List[Dict[str, Any]]
    signals: List[Dict[str, Any]]
    signals_raw: List[Dict[str, Any]]
