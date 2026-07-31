from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import re
from fastapi.responses import JSONResponse, FileResponse
import json
import os
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# Define las variables de entorno
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

app = FastAPI(title="SVLB Multi-Agent Orchestrator")

# Permitir solicitudes desde el frontend local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de datos de entrada
class SVLBRequest(BaseModel):
    ip: str
    port: str
    range_count: Optional[str] = None
    mhdr_preset: str
    custom_mhdr: Optional[str] = None

class UserStoryRequest(BaseModel):
    user_story: str

# --- LÓGICA DE LOS AGENTES ---

def agent_network_validator(ip: str, port: str) -> Dict[str, Any]:
    """Agente 1: Valida la coherencia de red y sintaxis de puertos."""
    ip_pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    if not re.match(ip_pattern, ip):
        raise ValueError(f"Dirección IP no válida: {ip}")
    
    # Validar formato de puerto (ej. 10000, 20001-20005, o IP:Puerto)
    port_pattern = r"^(\d+|\d+-\d+|((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):\d+)$"
    if not re.match(port_pattern, port):
        raise ValueError(f"Formato de puerto/rango no válido: {port}")
        
    return {"status": "OK", "ip": ip, "port": port}

def agent_protocol_validator(preset: str, custom: Optional[str]) -> str:
    """Agente 2: Aplica las reglas del manual SVLB para el enmarcado mhdr."""
    if preset == "custom":
        if not custom:
            raise ValueError("Debe especificar un valor para la cabecera personalizada.")
        # Validación de sintaxis mhdr genérica: [xN][i][C|B][D|H][b|l][1-9]
        mhdr_pattern = r"^(x\d+)?(i)?(C|B)(D|H)(b|l)[1-9]$"
        if not re.match(mhdr_pattern, custom) and custom not in ["visa", "amex"]:
            raise ValueError(f"La sintaxis del mhdr '{custom}' no cumple con la especificación de SmartVista.")
        return custom
    return preset

def agent_compiler(net_data: Dict[str, Any], mhdr: str, range_count: Optional[str]) -> Dict[str, Any]:
    """Agente 3: Ensambla la estructura final de configuración."""
    ip = net_data["ip"]
    port = net_data["port"]
    
    formatted_mhdr_val = mhdr
    if range_count and range_count.strip():
        formatted_mhdr_val = f"{range_count.strip()}/{mhdr}"

    return {
        "status": "success",
        "generated_config": {
            "node_config": {
                "ip": ip,
                "ports": {
                    port: formatted_mhdr_val
                }
            },
            "rule_src_config": {
                "raddr": f"{ip}:0",
                "lport": f"{port} {mhdr}",
                "mhdr": mhdr
            }
        },
        "metadata": {
            "applied_rules": ["SVLB_1.14_Standard", "Network_Schema_V1"]
        }
    }

# --- ENDPOINT PRINCIPAL ---

@app.post("/api/generate-config")
async def process_svlb_config(payload: SVLBRequest):
    try:
        # Paso 1: Ejecución Agente Red
        net_info = agent_network_validator(payload.ip, payload.port)
        
        # Paso 2: Ejecución Agente Protocolo
        mhdr_val = agent_protocol_validator(payload.mhdr_preset, payload.custom_mhdr)
        
        # Paso 3: Agente Compilador
        result = agent_compiler(net_info, mhdr_val, payload.range_count)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno al procesar la configuración.")

@app.post("/api/process-user-story")
async def handle_user_story(req: UserStoryRequest):
    # Cargar contexto de los documentos guardados en la VM
    from document_reader import read_docx, read_excel_config
    from nodes.user_story_agent import process_user_story

    docx_path = "SmartVista Load Balancer-Credibanco.docx"
    excel_path = "Configurador Load Balancer.xlsx"

    docx_text = read_docx(docx_path) if os.path.exists(docx_path) else ""
    excel_text = read_excel_config(excel_path) if os.path.exists(excel_path) else ""

    rule_json = process_user_story(req.user_story, docx_text, excel_text)

    # Guardar temporalmente para descarga
    file_path = "rule_output.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(rule_json, f, indent=4, ensure_ascii=False)

    return JSONResponse(content={"status": "success", "data": rule_json, "download_url": "/api/download-json"})

@app.get("/api/download-json")
async def download_json():
    return FileResponse("rule_output.json", filename="smartvista_rule_config.json", media_type="application/json")    