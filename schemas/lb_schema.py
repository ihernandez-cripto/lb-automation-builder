from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class SmartVistaLBRule(BaseModel):
    rule_name: str = Field(description="Nombre descriptivo de la regla de balanceo.")
    listen_port: int = Field(description="Puerto de escucha del Load Balancer.")
    protocol: Literal["TCP", "HTTP", "HTTPS", "ISO8583"] = Field(description="Protocolo de red/transacción.")
    algorithm: Literal["ROUND_ROBIN", "LEAST_CONNECTIONS", "IP_HASH"] = Field(description="Algoritmo de balanceo.")
    backend_servers: List[str] = Field(description="Lista de IPs/Hostnames de los servidores backend con puerto (ej. 192.168.1.10:8080).")
    health_check_endpoint: Optional[str] = Field(default="/health", description="Ruta de verificación de estado (Health Check).")
    timeout_ms: int = Field(default=5000, description="Timeout en milisegundos.")