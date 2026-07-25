import os
import sqlite3
import warnings
from typing import TypedDict, List, Optional
from dotenv import load_dotenv

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

warnings.filterwarnings("ignore", message=".*TqdmWarning.*")

# 1. Cargar variables de entorno
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("No se encontró GEMINI_API_KEY o GOOGLE_API_KEY en el archivo .env")

# 2. Definir el Estado del Flujo Multiagente (AgentState)
class AgentState(TypedDict):
    customer_request: str        # Requerimiento inicial del cliente (IPs, puertos, cabeceras, etc.)
    architecture_plan: str      # Estrategia de enrutamiento/balanceo analizada por el Experto
    json_rule_draft: str        # Borrador de la regla JSON generada por el Constructor
    validation_feedback: str   # Resultado de la validación sintáctica/técnica
    is_valid: bool              # Indicador si la regla JSON pasa la validación
    documentation: str          # Reporte técnico final generado por el Documentador
    revision_number: int        # Contador de intentos/reparaciones
    max_revisions: int          # Límite de reintentos en caso de error

# 3. Modelos Pydantic para Salida Estructurada y Validación de Regla SVLB
class SVLBRuleSchema(BaseModel):
    rule_name: str = Field(description="Nombre descriptivo de la regla de balanceo")
    listen_port: int = Field(description="Puerto de escucha de la regla")
    target_servers: List[str] = Field(description="Lista de IPs o hostnames de destino")
    algorithm: str = Field(description="Algoritmo de balanceo (e.g., round-robin, least-connections, ip-hash)")
    headers_filter: Optional[List[str]] = Field(default=[], description="Filtros de cabeceras si aplica")
    status: str = Field(default="active", description="Estado inicial de la regla")

# 4. Inicializar Modelo Gemini y Persistencia
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GEMINI_API_KEY
)

conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
memory = SqliteSaver(conn)

# 5. Prompts de los Agentes Especializados

EXPERT_PROMPT = """Eres el **Agente Experto en SmartVista Load Balancer (SVLB)** de BPC-BT.
Tu objetivo es analizar los requerimientos del cliente y proponer el diseño de balanceo adecuado.
Analiza la solicitud y detalla:
1. Estrategia de enrutamiento recomendada.
2. Puertos, IP de origen/destino y filtros necesarios.
3. Consideraciones técnicas específicas para transacciones bancarias/ISO 8583 o HTTP/REST."""

CONSTRUCTOR_PROMPT = """Eres el **Agente Constructor de Reglas SVLB**.
Tu tarea es tomar el plan técnico redactado por el Experto y generar la regla de balanceo final.
Debes estructurar o corregir el formato JSON con base en el esquema oficial y el feedback de validación previo.

Plan técnico / Correcciones requeridas:
{plan_and_feedback}"""

VALIDATOR_PROMPT = """Eres el **Agente Validador de Reglas**.
Tu trabajo es revisar la regla JSON producida por el Constructor.
Verifica que:
1. Sea un JSON válido sintácticamente.
2. Contenga los campos clave: `rule_name`, `listen_port`, `target_servers` y `algorithm`.
3. Los puertos y direcciones sean coherentes.

Responde detallando si es 'VÁLIDO' o 'INVÁLIDO' y enumera los errores detectados si los hay."""

DOCUMENTER_PROMPT = """Eres el **Agente Documentador**.
Genera un informe técnico completo para la implementación en SmartVista Load Balancer.
El reporte debe incluir:
1. Resumen de la Solicitud del Cliente.
2. Explicación de la Regla de Balanceo y su Uso.
3. Regla JSON Final.
4. Diagrama de Conectividad / Flujo sugerido en formato de texto o Mermaid."""

# 6. Definición de Nodos del Grafo

def expert_node(state: AgentState):
    """Agente Experto: Analiza los requerimientos de la solicitud."""
    messages = [
        SystemMessage(content=EXPERT_PROMPT),
        HumanMessage(content=state['customer_request'])
    ]
    response = model.invoke(messages)
    return {"architecture_plan": response.content}

def constructor_node(state: AgentState):
    """Agente Constructor: Genera o corrige la regla en JSON."""
    feedback = state.get("validation_feedback", "Ninguna (Primera versión)")
    context = (
        f"Requerimiento original: {state['customer_request']}\n\n"
        f"Plan de Arquitectura: {state['architecture_plan']}\n\n"
        f"Feedback de Validación Anterior: {feedback}"
    )
    
    messages = [
        SystemMessage(content=CONSTRUCTOR_PROMPT.format(plan_and_feedback=context)),
        HumanMessage(content="Genera la regla JSON para SmartVista Load Balancer.")
    ]
    response = model.invoke(messages)
    return {
        "json_rule_draft": response.content,
        "revision_number": state.get("revision_number", 0) + 1
    }

def validator_node(state: AgentState):
    """Agente Validador: Revisa la integridad y sintaxis de la regla."""
    messages = [
        SystemMessage(content=VALIDATOR_PROMPT),
        HumanMessage(content=f"Regla a evaluar:\n\n{state['json_rule_draft']}")
    ]
    response = model.invoke(messages)
    content = response.content.upper()
    
    # Determina si pasa o requiere corrección
    is_valid = "INVÁLIDO" not in content and "INVALID" not in content
    return {
        "validation_feedback": response.content,
        "is_valid": is_valid
    }

def documenter_node(state: AgentState):
    """Agente Documentador: Elabora el entregable técnico final."""
    context = (
        f"Solicitud Cliente: {state['customer_request']}\n\n"
        f"Plan Arquitectura: {state['architecture_plan']}\n\n"
        f"Regla JSON Final: {state['json_rule_draft']}"
    )
    messages = [
        SystemMessage(content=DOCUMENTER_PROMPT),
        HumanMessage(content=context)
    ]
    response = model.invoke(messages)
    return {"documentation": response.content}

# 7. Lógica Condicional del Grafo
def route_after_validation(state: AgentState):
    """Determina si la regla pasa a documentación o a reparación por el Constructor."""
    if state["is_valid"]:
        return "documenter"
    
    if state["revision_number"] >= state["max_revisions"]:
        print("\n⚠️ Se alcanzó el límite máximo de revisiones. Forzando documentación con advertencias...")
        return "documenter"
        
    return "constructor"

# 8. Construcción del Grafo Multiagente con LangGraph
workflow = StateGraph(AgentState)

# Agregar Nodos
workflow.add_node("expert", expert_node)
workflow.add_node("constructor", constructor_node)
workflow.add_node("validator", validator_node)
workflow.add_node("documenter", documenter_node)

# Establecer Punto de Entrada
workflow.set_entry_point("expert")

# Flujo de Aristas (Edges)
workflow.add_edge("expert", "constructor")
workflow.add_edge("constructor", "validator")

# Transición Condicional según la Validación
workflow.add_conditional_edges(
    "validator",
    route_after_validation,
    {
        "documenter": "documenter",
        "constructor": "constructor"
    }
)

workflow.add_edge("documenter", END)

# Compilar el Grafo con Persistencia SQLite
graph = workflow.compile(checkpointer=memory)

# 9. Ejemplo de Ejecución en Consola
if __name__ == "__main__":
    thread_config = {"configurable": {"thread_id": "svlb_session_1"}}
    
    initial_input = {
        "customer_request": (
            "Necesito balancear el tráfico del switch transaccional ISO 8583. "
            "Puerto de entrada: 8080. Servidores destino: 192.168.10.15 y 192.168.10.16 en puerto 8080. "
            "Algoritmo deseado: Round Robin."
        ),
        "max_revisions": 3,
        "revision_number": 0,
        "is_valid": False,
        "validation_feedback": "",
        "json_rule_draft": "",
        "architecture_plan": "",
        "documentation": ""
    }

    print("🚀 Iniciando procesamiento multiagente para SVLB...\n")
    for step in graph.stream(initial_input, thread_config):
        for node_name, state_update in step.items():
            print(f"✔️ Nodo finalizado: [{node_name}]")
            if node_name == "documenter":
                print("\n================ REPORT TÉCNICO ENTREGADO ================\n")
                print(state_update.get("documentation"))