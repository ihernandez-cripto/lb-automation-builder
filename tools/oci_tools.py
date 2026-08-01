from langchain_core.tools import tool
from config.settings import OCI_STORAGE_BUCKET_URL

@tool
def generate_oci_storage_link(config_json_str: str) -> str:
    """Simula la subida de la configuración formateada al Storage de OCI y retorna el enlace de descarga."""
    try:
        file_hash = abs(hash(config_json_str)) % 1000000
        return f"{OCI_STORAGE_BUCKET_URL}smartvista_rule_{file_hash}.json"
    except Exception as e:
        return f"Error al interactuar con OCI: {str(e)}"