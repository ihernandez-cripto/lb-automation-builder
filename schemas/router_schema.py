from typing import Literal, Optional, Sequence
import operator
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage

class RouterDecision(BaseModel):
    next_agent: Literal["ingress_agent", "constructor_agent", "validator_agent", "documenter_agent", "supervisor"] = Field(
        description="Selecciona el agente especializado para ejecutar la siguiente fase de la automatización."
    )
    reasoning: str = Field(description="Justificación técnica de la selección del agente.")

class LBAutomationState(BaseModel):
    messages: Annotated[Sequence[BaseMessage], operator.add] if False else Sequence[BaseMessage]  # Typings para LangGraph
    next_node: str = Field(default="")
    raw_requirements: str = Field(default="")
    generated_json_config: str = Field(default="")
    validation_status: bool = Field(default=False)
    validation_errors: Optional[str] = Field(default=None)
    oci_object_link: Optional[str] = Field(default=None)
    final_documentation: str = Field(default="")