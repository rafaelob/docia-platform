"""
Agent Input/Output Pydantic Models for MedflowAI.

This module defines common or base Pydantic models for agent inputs and outputs.
Specialized agents can inherit from these or define their own specific schemas.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any

class GenericInput(BaseModel):
    """A generic input model that can be used by simple agents or as a base."""
    query: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class GenericOutput(BaseModel):
    """A generic output model that can be used by simple agents or as a base."""
    response: str
    confidence_score: Optional[float] = None
    error_message: Optional[str] = None
    debug_info: Optional[Dict[str, Any]] = None

if __name__ == "__main__":
    # This is primarily for module testing or example usage.
    print("MedflowAI Agent I/O Models module.")
    input_example = GenericInput(query="Hello MedflowAI", session_id="test_session_123")
    output_example = GenericOutput(response="Acknowledged: Hello MedflowAI", confidence_score=1.0)
    print("\nExample GenericInput:")
    print(input_example.model_dump_json(indent=2))
    print("\nExample GenericOutput:")
    print(output_example.model_dump_json(indent=2))
