from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from config.settings import MODEL_NAME
from schemas.router_schema import RouterDecision

llm = ChatOpenAI(model=MODEL_NAME, temperature=0)

def router_node(state):
    structured_llm = llm.with_structured_output(RouterDecision)
    prompt = SystemMessage(
        content=(
            "Eres el enrutador central del sistema 'LB Automation Builder' para SmartVista Load Balancer.\n"
            "Evalúa la situación según las siguientes reglas:\n"
            "1. Si no se han refinado los requerimientos, dirige a 'ingress_agent'.\n"
            "2. Si los requerimientos están listos pero no hay JSON generado, dirige a 'constructor_agent'.\n"
            "3. Si hay un JSON generado pero no ha sido validado (o hubo fallos), dirige a 'validator_agent'.\n"
            "4. Si el JSON fue validado exitosamente pero falta documentación u OCI link, dirige a 'documenter_agent'.\n"
            "5. Si la regla JSON está validada y documentada, dirige a 'supervisor' para finalizar."
        )
    )
    decision = structured_llm.invoke([prompt] + list(state.messages))
    return {"next_node": decision.next_agent}