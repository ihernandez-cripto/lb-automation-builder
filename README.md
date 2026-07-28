# Load Balancer Automation Builder (LB Automation Builder) 🚀

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Framework](https://img.shields.io/badge/Framework-LangGraph-orange.svg)
![Backend](https://img.shields.io/badge/API-FastAPI-green.svg)
![Validation](https://img.shields.io/badge/Validation-Pydantic-green.svg)
![Infrastructure](https://img.shields.io/badge/Cloud-Oracle%20Cloud%20(OCI)-red.svg)

**LB Automation Builder** es un sistema orquestado por una **arquitectura multiagente distribuida** sobre **LangGraph** y expuesto mediante una **API REST (FastAPI) + Interfaz Web interactiva**. Diseñado para automatizar el ciclo de vida de administración, configuración, validación y documentación de reglas para **SmartVista Load Balancer (SVLB)**.

El sistema procesa requerimientos operativos expresados en lenguaje natural o parámetros técnicos desde un formulario dinámico web, los convierte en objetos JSON validados contra las especificaciones de SmartVista (ip, puertos, `mhdr`, etc.), genera documentación técnica en formato Markdown y simula/ejecuta la subida de paquetes de configuración a contenedores de **Oracle Cloud Infrastructure (OCI)**.

---

## 📄 Tabla de Contenidos

- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Flujo de Trabajo (Workflow)](#-flujo-de-trabajo-workflow)
- [Estructura de Agentes](#-estructura-de-agentes)
- [Esquema de Datos y Validación](#-esquema-de-datos-y-validación)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Ejecución](#-ejecución)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Interfaz Web](#-interfaz-web)
- [Despliegue en Oracle Cloud Infrastructure (OCI)](#-despliegue-oci)
- [Contribuciones](#-contribuciones)
- [Licencia](#-licencia)

---

## 🏗 Arquitectura del Sistema

El proyecto integra una **Capa Cliente (Frontend Web)** comunicada asíncronamente vía HTTP/JSON con un **Servidor de Agentes (FastAPI + LangGraph)**. La orquestación backend sustituye los flujos secuenciales rígidos por un **grafo determinista con agentes especializados**.

```text
[ Cliente Web / Frontend HTML5 + JS ]
                 │
                 │ (POST /api/generate-config)
                 ▼
┌──────────────────────────────────────────────────────────┐
│              BACKEND API (FastAPI Orchestrator)          │
│                                                          │
│                 +---------------+                        │
│                 | Router Node   |<-------------------+   │
│                 +-------+-------+                    |   │
│                         |                            |   │
│    +--------------------+--------------------+       |   │
│    |            |               |            |       |   │
│    v            v               v            v       |   │
│ +-----+      +-----+         +-----+      +-----+    |   │
│ |Ingr.|      |Const|         |Valid|      |Docum|    |   │
│ |Agent|      |Agent|         |Agent|      |Agent|    |   │
│ +--+--+      +--+--+         +--+--+      +--+--+    |   │
│    |            |               |            |       |   │
│    +------------+---------------+------------+       |   │
│                         | (Validación OK + Doc)      |   │
│                         v                            |   │
│                 +---------------+                    |   │
│                 |  Supervisor   |--------------------+   │
│                 +-------+-------+                        │
│                         |                                │
└─────────────────────────┼────────────────────────────────┘
                          ▼
           [ Respuesta JSON / Config SVLB ]

```

---

## 🔄 Flujo de Trabajo (Workflow)

1. **Ingreso (Frontend / API):** El usuario ingresa una solicitud vía interfaz web (formulario estructurado) o en lenguaje natural.
2. **Interpretación:** El **Ingress Agent** valida los parámetros iniciales o traduce la solicitud a especificaciones de red (`raddr`, `lport`, `mhdr`).
3. **Generación:** El **Constructor Agent** arma el bloque de código JSON respetando el estándar del manual de SmartVista Load Balancer.
4. **Validación y Autorreparación:** El **Validator Agent** evalúa la sintaxis mediante esquemas Pydantic (`SmartVistaLBRule`). Si se identifican errores de rango, sintaxis de cabecera o puerto, activa el sub-ciclo de reparación.
5. **Documentación & Cloud:** El **Documenter Agent** crea la ficha técnica en Markdown y emite los enlaces del repositorio en OCI Object Storage.
6. **Consolidación:** El **Supervisor** presenta la configuración técnica validada (`node_config`, `rule_src_config`) y la retorna a la interfaz web para su visualización/descarga.

---

## 🤖 Estructura de Agentes

| Agente / Nodo | Función Principal | Salida Producida |
| --- | --- | --- |
| **Router Node** | Evalúa el estado del grafo y toma la decisión determinista de enrutamiento mediante un esquema Pydantic. | `next_node` ("ingress", "constructor", "validator", "documenter", "supervisor") |
| **Ingress Agent** | Extrae requerimientos técnicos (IP, puerto, rango, protocolo, `mhdr`) a partir del payload API o lenguaje natural. | `raw_requirements` |
| **Constructor Agent** | Genera la definición estructural de la regla en JSON compatible con SmartVista (`node_config`, `rule_src_config`). | `generated_json_config` |
| **Validator Agent (Repairer)** | Valida sintácticamente el JSON contra el esquema Pydantic `SmartVistaLBRule` y reglas del protocolo (`CDb4`, `BHb2`, `visa`, `amex`, etc.). Repara el JSON si hay fallas. | `validation_status` (Boolean), `validation_errors` |
| **Documenter Agent** | Redacta la ficha técnica y coordina las llamadas a herramientas externas (OCI Object Storage API). | `final_documentation`, `oci_object_link` |
| **Supervisor Node** | Redacta la respuesta final y devuelve la estructura JSON/Markdown consolidada al endpoint de la API. | `generated_config` + `messages` |

---

## 🛡 Esquema de Datos y Validación

Toda configuración generada cumple con los tipos de datos requeridos por la estructura base de **SmartVista Load Balancer**.

```python
class SmartVistaLBRule(BaseModel):
    ip: str = Field(description="Dirección IP destino o 0.0.0.0 para cualquier origen.")
    port: str = Field(description="Puerto individual (ej. 10000) o rango de puertos (ej. 20001-20005).")
    range_count: Optional[str] = Field(default=None, description="Cantidad de conexiones consecutivas en rango (ej. 10/BHb2).")
    mhdr_preset: str = Field(description="Tipo o formato de enmarcado de cabecera (CDb4, BHb2, visa, amex, custom).")
    custom_mhdr: Optional[str] = Field(default=None, description="Sintaxis de cabecera genérica personalizada (ej. x800BHb2).")

```

---

## 🛠 Requisitos Previos

* **Python:** 3.10 o superior.
* **OpenAI API Key:** Acceso a modelos GPT-4o o equivalentes.
* **Librerías Clave:**
* `fastapi`
* `uvicorn`
* `langgraph`
* `langchain-core`
* `langchain-openai`
* `pydantic`



---

## 📦 Instalación y Configuración

1. **Clonar el repositorio:**

```bash
git clone [https://github.com/ihernandez-cripto/lb-automation-builder.git](https://github.com/ihernandez-cripto/lb-automation-builder.git)
cd lb-automation-builder

```

2. **Crear y activar un entorno virtual:**

```bash
python -m venv venv
source venv/bin/activate  # En Linux/macOS
# venv\Scripts\activate   # En Windows

```

3. **Instalar dependencias:**

```bash
pip install -r requirements.txt

```

4. **Configurar variables de entorno:**
Crea un archivo `.env` en la raíz del proyecto:

```env
OPENAI_API_KEY="tu-api-key-aqui"
OCI_COMPARTMENT_ID="ocid1.compartment.oc1.."  # Opcional para despliegue OCI real

```

---

## 🚀 Ejecución

El proyecto consta de dos partes: el servicio backend API de agentes y la interfaz gráfica de usuario.

### 1. Iniciar el Backend (FastAPI + LangGraph)

Ejecuta el servidor backend Uvicorn:

```bash
uvicorn app:app --reload --port 8000

```

*El backend quedará escuchando en `http://127.0.0.1:8000` y desplegará la documentación interactiva en `http://127.0.0.1:8000/docs`.*

### 2. Iniciar la Interfaz Web (Frontend)

* Abre el archivo `index.html` directamente en tu navegador o mediante la extensión **Live Server** en Visual Studio Code.
* Configura los parámetros de IP, Puerto y Cabecera (`mhdr`) y haz clic en **Procesar con Agentes Backend**.

---

## 📂 Estructura del Proyecto

```text
lb-automation-builder/
├── config/
│   └── settings.py             # Configuración general de variables y claves API
├── schemas/
│   ├── lb_schema.py            # Esquema Pydantic SmartVistaLBRule
│   └── router_schema.py        # Esquema de decisión para RouterDecision
├── nodes/
│   ├── router.py               # Lógica del nodo enrutador
│   ├── agents.py               # Nodos de agentes (Ingress, Constructor, Validator, Documenter)
│   └── supervisor.py           # Nodo final de consolidación
├── tools/
│   └── oci_tools.py            # Herramientas de integración con Oracle Cloud Infrastructure
├── app.py                      # Servidor backend API (FastAPI) y orquestación de endpoints
├── graph.py                    # Ensamble de nodos y bordes condicionales en LangGraph
├── main.py                     # Punto de entrada para ejecución por CLI
├── index.html                  # Interfaz web cliente (HTML5/CSS3/JavaScript)
├── requirements.txt            # Dependencias del proyecto
└── README.md                   # Documentación del proyecto

```
---
## Interfaz Web

La interfaz web permite ingresar parámetros de configuración de SmartVista Load Balancer y enviar la petición al backend de agentes.

- El usuario completa los campos de IP, puerto, rango y `mhdr`.
- El frontend envía la solicitud a `POST /api/generate-config`.
- El backend devuelve la configuración validada, la documentación técnica en Markdown y el enlace simulado a OCI.

Ejemplo de uso:

1. Abrir `index.html` en el navegador o usar Live Server en Visual Studio Code.
2. Completar los campos de la forma con los datos de la regla.
3. Presionar el botón **Procesar con Agentes Backend**.
4. Revisar la salida generada y descargar los archivos si es necesario.

![Interfaz Web](lb_web/imagen/app_ONE.png)

---
---
## ☁️ Despliegue en Oracle Cloud Infrastructure (OCI)

El proyecto está diseñado para ser desplegado en instancias **OCI Compute** (Oracle Linux 8/9 / RHEL) integrándose con servicios de red y almacenamiento de OCI.

### 🏛 Arquitectura de Despliegue

```text
[ Cliente Web / Navegador ]
           │
           │ (HTTP / Puerto 80 o 8000)
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORACLE CLOUD INFRASTRUCTURE                  │
│                                                                 │
│  ┌────────────────────────┐         ┌────────────────────────┐  │
│  │ OCI Security List      │         │ OCI Compute (VM)       │  │
│  │  - Ingress TCP: 80     │         │  - Firewall / firewalld│  │
│  │  - Ingress TCP: 8000   │────────►│  - Nginx (Frontend)    │  │
│  └────────────────────────┘         │  - Uvicorn (FastAPI)   │  │
│                                     │  - LangGraph Flow      │  │
│  ┌────────────────────────┐         └───────────┬────────────┘  │
│  │ OCI Object Storage     │                     │               │
│  │  - Documentación SVLB  │◄────────────────────┘               │
│  └────────────────────────┘                                     │
└─────────────────────────────────────────────────────────────────┘

```

---

### 📋 Prerrequisitos de Infraestructura OCI

1. **Instancia Compute**: Shape `VM.Standard.A1.Flex` u equivalente con sistema operativo Oracle Linux o Ubuntu.
2. **Virtual Cloud Network (VCN)**: Reglas de Entrada (*Ingress Rules*) habilitadas en la **Security List**:
* **CIDR de origen:** `0.0.0.0/0`
* **IP Protocol:** `TCP`
* **Puertos de destino:** `80` (HTTP) y `8000` (FastAPI / Uvicorn API).



---

### 🚀 Pasos de Instalación y Despliegue en la VM

#### 1. Conexión SSH a la Instancia

Asegúrate de conectarte utilizando el usuario predeterminado de Oracle Linux (`opc`) y tu clave privada SSH:

```bash
ssh -i /ruta/a/tu/clave_privada.key opc@<IP_PUBLICA_OCI>

```

#### 2. Configurar Espacio SWAP (Memoria Virtual de Protección)

Para prevenir bloqueos del kernel por falta de memoria RAM (*Out of Memory / OOM Killer*) durante la instalación de paquetes con `pip`, habilita 2 GB de memoria SWAP:

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

```

#### 3. Clonar Repositorio e Instalar Dependencias

```bash
git clone [https://github.com/ihernandez-cripto/lb-automation-builder.git](https://github.com/ihernandez-cripto/lb-automation-builder.git)
cd lb-automation-builder

# Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias optimizando el uso de memoria RAM
pip install --no-cache-dir -r requirements.txt

```

#### 4. Configuración de Variables de Entorno

Crea el archivo `.env` en la raíz del proyecto:

```bash
cat << 'EOF' > .env
OPENAI_API_KEY="tu-api-key-de-openai"
OCI_COMPARTMENT_ID="ocid1.compartment.oc1.." # Opcional si se integran herramientas de OCI SDK
EOF

```

#### 5. Configuración del Firewall Interno (firewalld)

Abre el puerto de la API en el firewall del SO en Oracle Linux:

```bash
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

```

---

### ⚙️ Automatización del Servicio Backend (Systemd)

Para garantizar la ejecución continua del backend FastAPI en OCI, configura un servicio de `systemd`:

1. Crear el archivo de servicio:

```bash
sudo nano /etc/systemd/system/svlb-backend.service

```

2. Agregar la siguiente configuración:

```ini
[Unit]
Description=SVLB Multi-Agent FastAPI Backend
After=network.target

[Service]
User=opc
WorkingDirectory=/home/opc/lb-automation-builder
ExecStart=/home/opc/lb-automation-builder/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target

```

3. Activar e iniciar el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now svlb-backend

```

---

### 🌐 Configurar la IP del Servidor en el Frontend

Antes de desplegar la interfaz web, asegúrate de actualizar la URL del endpoint en el archivo `index.html` para que apunte a la IP pública de tu instancia de OCI:

```javascript
// index.html
const response = await fetch('http://<IP_PUBLICA_OCI>:8000/api/generate-config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
});

```
## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para cambios mayores, abre un *issue* primero para discutir lo que te gustaría modificar o mejorar.

---

## 📝 Licencia

Este proyecto está distribuido bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.

```

```
