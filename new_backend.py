# new_backend.py
import os
import sqlite3
import warnings
from typing import List, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

warnings.filterwarnings("ignore", message=".*TqdmWarning.*")

load_dotenv()

# Clave de API de Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

# 1. Estado del Agente con las 5 variables requeridas
class LBState(TypedDict):
    client_ip: str
    lb_ip: str
    num_nodes: int
    node_ips: str
    header_length: int
    plan: str
    config_draft: str
    critique: str
    revision_number: int
    max_revisions: int

# Conexión a la base de datos de checkpoints
conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
memory = SqliteSaver(conn)

# Inicialización del modelo
model = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest", 
    temperature=0, 
    google_api_key=GOOGLE_API_KEY
)

# Prompts adaptados a los 5 parámetros técnicos
PLAN_PROMPT = """Eres un Arquitecto de Redes y Balanceadores de Carga para entornos transaccionales.
Analiza la siguiente topología para estructurar la regla de balanceo:

- IP Cliente (Origen): {client_ip}
- IP VIP Load Balancer: {lb_ip}
- Cantidad de Nodos Backend: {num_nodes}
- IPs de Nodos: {node_ips}
- Longitud de Cabecera (Header Length): {header_length} bytes

Genera un plan técnico especificando:
1. Esquema de filtrado/permisos para la IP de Origen.
2. Método de distribución hacia los {num_nodes} nodos.
3. Tratamiento y parseo de la cabecera fija de {header_length} bytes.
4. Health Checks hacia los puertos backend."""

CONFIG_PROMPT = """Eres un Ingeniero Senior de Automatización de Redes.
Genera el script/definición de configuración formal del Load Balancer basándote en el plan y los parámetros:

- IP Cliente: {client_ip}
- VIP Load Balancer: {lb_ip}
- Pool de Nodos ({num_nodes} activos):
{node_ips}
- Header Offset/Length: {header_length} bytes

Plan de Arquitectura:
{plan}

Si existen críticas previas, realiza las correcciones necesarias."""

CRITIQUE_PROMPT = """Eres un Auditor de Seguridad y Performance de Transacciones.
Revisa la configuración propuesta del Load Balancer teniendo en cuenta:
1. Coincidencia entre la cantidad de nodos indicada y las IPs provistas.
2. Manejo adecuado de la cabecera ({header_length} bytes) sin provocar truncamiento de mensajes.
3. Reglas de ACL para asegurar que solo la IP Cliente ({client_ip}) pueda enviar tráfico.
Proporciona recomendaciones específicas o aprueba la configuración."""

# Nodos del Grafo
def plan_node(state: LBState):
    prompt_content = PLAN_PROMPT.format(
        client_ip=state['client_ip'],
        lb_ip=state['lb_ip'],
        num_nodes=state['num_nodes'],
        node_ips=state['node_ips'],
        header_length=state['header_length']
    )
    messages = [
        SystemMessage(content="Eres un experto en infraestructura transaccional."),
        HumanMessage(content=prompt_content)
    ]
    response = model.invoke(messages)
    return {"plan": response.content}

def generation_node(state: LBState):
    user_msg = f"Revisión {state.get('revision_number', 0) + 1}\nCrítica previa: {state.get('critique', 'N/A')}"
    prompt_content = CONFIG_PROMPT.format(
        client_ip=state['client_ip'],
        lb_ip=state['lb_ip'],
        num_nodes=state['num_nodes'],
        node_ips=state['node_ips'],
        header_length=state['header_length'],
        plan=state['plan']
    )
    
    messages = [
        SystemMessage(content=prompt_content),
        HumanMessage(content=user_msg)
    ]
    response = model.invoke(messages)
    return {
        "config_draft": response.content,
        "revision_number": state.get("revision_number", 0) + 1
    }

def reflection_node(state: LBState):
    prompt_content = CRITIQUE_PROMPT.format(
        client_ip=state['client_ip'],
        header_length=state['header_length']
    )
    messages = [
        SystemMessage(content=prompt_content),
        HumanMessage(content=state['config_draft'])
    ]
    response = model.invoke(messages)
    return {"critique": response.content}

def should_continue(state: LBState):
    if state["revision_number"] > state["max_revisions"]:
        return END
    return "reflect"

# Construcción del Grafo
builder = StateGraph(LBState)

builder.add_node("planner", plan_node)
builder.add_node("generate_config", generation_node)
builder.add_node("audit_reflect", reflection_node)

builder.set_entry_point("planner")

builder.add_edge("planner", "generate_config")
builder.add_conditional_edges(
    "generate_config",
    should_continue,
    {END: END, "reflect": "audit_reflect"}
)
builder.add_edge("audit_reflect", "generate_config")

graph = builder.compile(checkpointer=memory)