from langchain_core.messages import AIMessage

def supervisor_node(state):
    summary = (
        f"### LB Automation Builder - Proceso Completado\n\n"
        f"**Estado de Validación:** {'Aprobado ✅' if state.validation_status else 'Revisión Requerida ⚠️'}\n"
        f"**Enlace de Descarga/Despliegue OCI:** [{state.oci_object_link}]({state.oci_object_link})\n\n"
        f"#### Ficha Técnica y Documentación:\n"
        f"{state.final_documentation}\n\n"
        f"#### Configuración JSON Final (SmartVista):\n"
        f"```json\n{state.generated_json_config}\n```"
    )
    return {"messages": [AIMessage(content=summary)]}