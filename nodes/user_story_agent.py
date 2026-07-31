import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# Define las variables de entorno
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

import json
from langchain_google_genai import ChatGoogleGenerativeAI

def process_user_story(user_story: str, docx_content: str, excel_content: str) -> dict:
    
    docx_text = docx_content if docx_content and docx_content.strip() else "Sin información adicional."
    excel_text = excel_content if excel_content and excel_content.strip() else "Sin información adicional."
    
    # Cambiar 'gemini-1.5-flash' por 'gemini-2.0-flash'
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0
    )
    
    prompt = f"""
    Eres un experto en administración de SmartVista Load Balancer (SVLB).
    Basándote en la siguiente información de contexto tomada de los documentos oficiales:

    DOCUMENTO CREDIBANCO:
    {docx_text[:2000]}

    CONFIGURADOR DE AMBIENTES (EXCEL):
    {excel_text[:2000]}

    Instrucción:
    Procesa la siguiente historia de usuario y genera la regla de configuración JSON exacta para el ambiente indicado:
    HISTORIA DE USUARIO: "{user_story}"

    Responde ÚNICAMENTE con un objeto JSON válido con la siguiente estructura:
    {{
        "environment": "QA",
        "client": "Banco Caja Social",
        "load_balancer": {{
            "virtual_ip": "172.29.12.67",
            "nodes": [
                {{"node_id": 1, "ip": "172.29.12.69"}},
                {{"node_id": 2, "ip": "172.29.12.68"}}
            ]
        }},
        "rules": [
            {{
                "direction": "SVFE_SERVER",
                "source_ip": "10.2.32.194",
                "source_ports": ["330-333", "430-433"],
                "role": "server"
            }},
            {{
                "direction": "SVFE_CLIENT",
                "destination_ip": "172.19.207.40",
                "destination_ports": [4180, 5180],
                "role": "client"
            }}
        ]
    }}
    """
    
    response = llm.invoke(prompt)
    clean_text = response.content.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_text)