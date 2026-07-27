# Load Balancer Automation Builder (LB Automation Builder) ??

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Framework](https://img.shields.io/badge/Framework-LangGraph-orange.svg)
![Backend](https://img.shields.io/badge/API-FastAPI-green.svg)
![Validation](https://img.shields.io/badge/Validation-Pydantic-green.svg)
![Infrastructure](https://img.shields.io/badge/Cloud-Oracle%20Cloud%20(OCI)-red.svg)

**LB Automation Builder** es un sistema orquestado por una **arquitectura multiagente distribuida** sobre **LangGraph** y expuesto mediante una **API REST (FastAPI) + Interfaz Web interactiva**. Dise?ado para automatizar el ciclo de vida de administraci¨®n, configuraci¨®n, validaci¨®n y documentaci¨®n de reglas para **SmartVista Load Balancer (SVLB)**.

El sistema procesa requerimientos operativos expresados en lenguaje natural o par¨¢metros t¨¦cnicos desde un formulario din¨¢mico web, los convierte en objetos JSON validados contra las especificaciones de SmartVista (ip, puertos, `mhdr`, etc.), genera documentaci¨®n t¨¦cnica en formato Markdown y simula/ejecuta la subida de paquetes de configuraci¨®n a contenedores de **Oracle Cloud Infrastructure (OCI)**.

---

## ?? Tabla de Contenidos

- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Flujo de Trabajo (Workflow)](#-flujo-de-trabajo-workflow)
- [Estructura de Agentes](#-estructura-de-agentes)
- [Esquema de Datos y Validaci¨®n](#-esquema-de-datos-y-validaci¨®n)
- [Requisitos Previos](#-requisitos-previos)
- [Instalaci¨®n y Configuraci¨®n](#-instalaci¨®n-y-configuraci¨®n)
- [Ejecuci¨®n](#-ejecuci¨®n)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Contribuciones](#-contribuciones)
- [Licencia](#-licencia)

---

## ?? Arquitectura del Sistema

El proyecto integra una **Capa Cliente (Frontend Web)** comunicada as¨ªncronamente v¨ªa HTTP/JSON con un **Servidor de Agentes (FastAPI + LangGraph)**. La orquestaci¨®n backend sustituye los flujos secuenciales r¨ªgidos por un **grafo determinista con agentes especializados**.

```text
[ Cliente Web / Frontend HTML5 + JS ]
                 ©¦
                 ©¦ (POST /api/generate-config)
                 ¨‹
©°©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©´
©¦              BACKEND API (FastAPI Orchestrator)          ©¦
©¦                                                          ©¦
©¦                 +---------------+                        ©¦
©¦                 | Router Node   |<-------------------+   ©¦
©¦                 +-------+-------+                    |   ©¦
©¦                         |                            |   ©¦
©¦    +--------------------+--------------------+       |   ©¦
©¦    |            |               |            |       |   ©¦
©¦    v            v               v            v       |   ©¦
©¦ +-----+      +-----+         +-----+      +-----+    |   ©¦
©¦ |Ingr.|      |Const|         |Valid|      |Docum|    |   ©¦
©¦ |Agent|      |Agent|         |Agent|      |Agent|    |   ©¦
©¦ +--+--+      +--+--+         +--+--+      +--+--+    |   ©¦
©¦    |            |               |            |       |   ©¦
©¦    +------------+---------------+------------+       |   ©¦
©¦                         | (Validaci¨®n OK + Doc)      |   ©¦
©¦                         v                            |   ©¦
©¦                 +---------------+                    |   ©¦
©¦                 |  Supervisor   |--------------------+   ©¦
©¦                 +-------+-------+                        ©¦
©¦                         |                                ©¦
©¸©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©à©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¼
                          ¨‹
           [ Respuesta JSON / Config SVLB ]

```

---

## ?? Flujo de Trabajo (Workflow)

1. **Ingreso (Frontend / API):** El usuario ingresa una solicitud v¨ªa interfaz web (formulario estructurado) o en lenguaje natural.
2. **Interpretaci¨®n:** El **Ingress Agent** valida los par¨¢metros iniciales o traduce la solicitud a especificaciones de red (`raddr`, `lport`, `mhdr`).
3. **Generaci¨®n:** El **Constructor Agent** arma el bloque de c¨®digo JSON respetando el est¨¢ndar del manual de SmartVista Load Balancer.
4. **Validaci¨®n y Autorreparaci¨®n:** El **Validator Agent** eval¨²a la sintaxis mediante esquemas Pydantic (`SmartVistaLBRule`). Si se identifican errores de rango, sintaxis de cabecera o puerto, activa el sub-ciclo de reparaci¨®n.
5. **Documentaci¨®n & Cloud:** El **Documenter Agent** crea la ficha t¨¦cnica en Markdown y emite los enlaces del repositorio en OCI Object Storage.
6. **Consolidaci¨®n:** El **Supervisor** presenta la configuraci¨®n t¨¦cnica validada (`node_config`, `rule_src_config`) y la retorna a la interfaz web para su visualizaci¨®n/descarga.

---

## ?? Estructura de Agentes

| Agente / Nodo | Funci¨®n Principal | Salida Producida |
| --- | --- | --- |
| **Router Node** | Eval¨²a el estado del grafo y toma la decisi¨®n determinista de enrutamiento mediante un esquema Pydantic. | `next_node` ("ingress", "constructor", "validator", "documenter", "supervisor") |
| **Ingress Agent** | Extrae requerimientos t¨¦cnicos (IP, puerto, rango, protocolo, `mhdr`) a partir del payload API o lenguaje natural. | `raw_requirements` |
| **Constructor Agent** | Genera la definici¨®n estructural de la regla en JSON compatible con SmartVista (`node_config`, `rule_src_config`). | `generated_json_config` |
| **Validator Agent (Repairer)** | Valida sint¨¢cticamente el JSON contra el esquema Pydantic `SmartVistaLBRule` y reglas del protocolo (`CDb4`, `BHb2`, `visa`, `amex`, etc.). Repara el JSON si hay fallas. | `validation_status` (Boolean), `validation_errors` |
| **Documenter Agent** | Redacta la ficha t¨¦cnica y coordina las llamadas a herramientas externas (OCI Object Storage API). | `final_documentation`, `oci_object_link` |
| **Supervisor Node** | Redacta la respuesta final y devuelve la estructura JSON/Markdown consolidada al endpoint de la API. | `generated_config` + `messages` |

---

## ?? Esquema de Datos y Validaci¨®n

Toda configuraci¨®n generada cumple con los tipos de datos requeridos por la estructura base de **SmartVista Load Balancer**.

```python
class SmartVistaLBRule(BaseModel):
    ip: str = Field(description="Direcci¨®n IP destino o 0.0.0.0 para cualquier origen.")
    port: str = Field(description="Puerto individual (ej. 10000) o rango de puertos (ej. 20001-20005).")
    range_count: Optional[str] = Field(default=None, description="Cantidad de conexiones consecutivas en rango (ej. 10/BHb2).")
    mhdr_preset: str = Field(description="Tipo o formato de enmarcado de cabecera (CDb4, BHb2, visa, amex, custom).")
    custom_mhdr: Optional[str] = Field(default=None, description="Sintaxis de cabecera gen¨¦rica personalizada (ej. x800BHb2).")

```

---

## ?? Requisitos Previos

* **Python:** 3.10 o superior.
* **OpenAI API Key:** Acceso a modelos GPT-4o o equivalentes.
* **Librer¨ªas Clave:**
* `fastapi`
* `uvicorn`
* `langgraph`
* `langchain-core`
* `langchain-openai`
* `pydantic`



---

## ?? Instalaci¨®n y Configuraci¨®n

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
Crea un archivo `.env` en la ra¨ªz del proyecto:

```env
OPENAI_API_KEY="tu-api-key-aqui"
OCI_COMPARTMENT_ID="ocid1.compartment.oc1.."  # Opcional para despliegue OCI real

```

---

## ?? Ejecuci¨®n

El proyecto consta de dos partes: el servicio backend API de agentes y la interfaz gr¨¢fica de usuario.

### 1. Iniciar el Backend (FastAPI + LangGraph)

Ejecuta el servidor backend Uvicorn:

```bash
uvicorn app:app --reload --port 8000

```

*El backend quedar¨¢ escuchando en `http://127.0.0.1:8000` y desplegar¨¢ la documentaci¨®n interactiva en `http://127.0.0.1:8000/docs`.*

### 2. Iniciar la Interfaz Web (Frontend)

* Abre el archivo `index.html` directamente en tu navegador o mediante la extensi¨®n **Live Server** en Visual Studio Code.
* Configura los par¨¢metros de IP, Puerto y Cabecera (`mhdr`) y haz clic en **Procesar con Agentes Backend**.

---

## ?? Estructura del Proyecto

```text
lb-automation-builder/
©À©¤©¤ config/
©¦   ©¸©¤©¤ settings.py             # Configuraci¨®n general de variables y claves API
©À©¤©¤ schemas/
©¦   ©À©¤©¤ lb_schema.py            # Esquema Pydantic SmartVistaLBRule
©¦   ©¸©¤©¤ router_schema.py        # Esquema de decisi¨®n para RouterDecision
©À©¤©¤ nodes/
©¦   ©À©¤©¤ router.py               # L¨®gica del nodo enrutador
©¦   ©À©¤©¤ agents.py               # Nodos de agentes (Ingress, Constructor, Validator, Documenter)
©¦   ©¸©¤©¤ supervisor.py           # Nodo final de consolidaci¨®n
©À©¤©¤ tools/
©¦   ©¸©¤©¤ oci_tools.py            # Herramientas de integraci¨®n con Oracle Cloud Infrastructure
©À©¤©¤ app.py                      # Servidor backend API (FastAPI) y orquestaci¨®n de endpoints
©À©¤©¤ graph.py                    # Ensamble de nodos y bordes condicionales en LangGraph
©À©¤©¤ main.py                     # Punto de entrada para ejecuci¨®n por CLI
©À©¤©¤ index.html                  # Interfaz web cliente (HTML5/CSS3/JavaScript)
©À©¤©¤ requirements.txt            # Dependencias del proyecto
©¸©¤©¤ README.md                   # Documentaci¨®n del proyecto

```

---

## ?? Contribuciones

Las contribuciones son bienvenidas. Para cambios mayores, abre un *issue* primero para discutir lo que te gustar¨ªa modificar o mejorar.

---

## ?? Licencia

Este proyecto est¨¢ distribuido bajo la licencia MIT. Consulta el archivo `LICENSE` para m¨¢s detalles.

```

```