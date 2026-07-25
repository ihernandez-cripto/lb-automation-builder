import operator
from typing import Annotated, Sequence, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END, START

from nodes.router import router_node
from nodes.agents import ingress_agent_node, constructor_agent_node, validator_agent_node, documenter_agent_node
from nodes.supervisor import supervisor_node

class LBAutomationState(BaseModel):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_node: str = Field(default="")
    raw_requirements: str = Field(default="")
    generated_json_config: str = Field(default="")
    validation_status: bool = Field(default=False)
    validation_errors: Optional[str] = Field(default=None)
    oci_object_link: Optional[str] = Field(default=None)
    final_documentation: str = Field(default="")

def build_graph():
    builder = StateGraph(LBAutomationState)

    builder.add_node("router", router_node)
    builder.add_node("ingress_agent", ingress_agent_node)
    builder.add_node("constructor_agent", constructor_agent_node)
    builder.add_node("validator_agent", validator_agent_node)
    builder.add_node("documenter_agent", documenter_agent_node)
    builder.add_node("supervisor", supervisor_node)

    builder.add_edge(START, "router")

    builder.add_conditional_edges(
        "router",
        lambda state: state.next_node,
        {
            "ingress_agent": "ingress_agent",
            "constructor_agent": "constructor_agent",
            "validator_agent": "validator_agent",
            "documenter_agent": "documenter_agent",
            "supervisor": "supervisor"
        }
    )

    builder.add_edge("ingress_agent", "router")
    builder.add_edge("constructor_agent", "validator_agent")
    builder.add_edge("validator_agent", "router")
    builder.add_edge("documenter_agent", "router")
    builder.add_edge("supervisor", END)

    return builder.compile()

app = build_graph()