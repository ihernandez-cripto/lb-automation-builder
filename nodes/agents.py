json_import = __import__("json")
from json import JSONDecodeError
from pydantic import ValidationError
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from config.settings import MODEL_NAME
from schemas.lb_schema import SmartVistaLBRule
from tools.oci_tools import generate_oci_storage_link

llm = ChatOpenAI(model=MODEL_NAME, temperature=0)

def ingress_agent_node(state):
    prompt = SystemMessage(
        content=(
            "Eres un Ingeniero Experto en SmartVista Load Balancer. Extrae y estructura las "
            "necesidades técnicas de balanceo (puerto, protocolo, algoritmo, backends, health checks) "
            "partiendo de la consulta del usuario."
        )
    )
    response = llm.invoke([prompt] + list(state.messages))
    return {
        "messages": [response],
        "raw_requirements": response.content
    }

def constructor_agent_node(state):
    prompt = SystemMessage(
        content=(
            "Eres el Constructor de Configuraciones de LB. Tu única tarea es generar un objeto JSON estricto "
            "que cumpla con la estructura de SmartVistaLBRule basada en los requerimientos procesados.\n"
            "Responde ÚNICAMENTE con el bloque de código JSON sin texto adicional."
        )
    )
    reqs = state.raw_requirements or state.messages[-1].content
    response = llm.invoke([prompt, HumanMessage(content=f"Requerimientos: {reqs}")])
    raw_json = response.content.strip().replace("```json", "").replace("```", "")
    return {
        "messages": [response],
        "generated_json_config": raw_json
    }

def validator_agent_node(state):
    raw_json = state.generated_json_config
    try:
        parsed_data = json_import.loads(raw_json)
        validated_rule = SmartVistaLBRule(**parsed_data)
        return {
            "validation_status": True,
            "validation_errors": None,
            "messages": [AIMessage(content=f"Validación exitosa para la regla: {validated_rule.rule_name}")]
        }
    except (JSONDecodeError, ValidationError) as err:
        repair_prompt = SystemMessage(
            content=(
                f"La configuración JSON generada falló en la validación de SmartVistaLBRule.\n"
                f"Errores detectados: {str(err)}\n"
                f"Por favor, corrige el JSON y devuélvelo corregido sin markdown ni explicaciones adicionales."
            )
        )
        corrected_response = llm.invoke([repair_prompt, HumanMessage(content=f"JSON Erróneo: {raw_json}")])
        corrected_json = corrected_response.content.strip().replace("```json", "").replace("```", "")
        return {
            "generated_json_config": corrected_json,
            "validation_status": False,
            "validation_errors": str(err),
            "messages": [AIMessage(content="Se detectaron errores de estructura. JSON corregido generado.")]
        }

def documenter_agent_node(state):
    oci_link = generate_oci_storage_link.invoke({"config_json_str": state.generated_json_config})
    prompt = SystemMessage(
        content=(
            "Eres el Documentador del LB Automation Builder. Genera una ficha técnica en Markdown "
            "que resuma la configuración del SmartVista Load Balancer, los parámetros principales, "
            "las políticas de monitoreo y las instrucciones de despliegue."
        )
    )
    doc_response = llm.invoke([
        prompt, 
        HumanMessage(content=f"Configuración JSON Validada:\n{state.generated_json_config}\nOCI Link: {oci_link}")
    ])
    return {
        "oci_object_link": oci_link,
        "final_documentation": doc_response.content,
        "messages": [doc_response]
    }