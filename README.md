# Load Balancer Automation Builder (LB Automation Builder) ??

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Framework](https://img.shields.io/badge/Framework-LangGraph-orange.svg)
![Backend](https://img.shields.io/badge/API-FastAPI-green.svg)
![Validation](https://img.shields.io/badge/Validation-Pydantic-green.svg)
![Infrastructure](https://img.shields.io/badge/Cloud-Oracle%20Cloud%20(OCI)-red.svg)

**LB Automation Builder** es un sistema orquestado por una **arquitectura multiagente distribuida** sobre **LangGraph** y expuesto mediante una **API REST (FastAPI) + Interfaz Web interactiva**. Dise?ado para automatizar el ciclo de vida de administraci車n, configuraci車n, validaci車n y documentaci車n de reglas para **SmartVista Load Balancer (SVLB)**.

El sistema procesa requerimientos operativos expresados en lenguaje natural o par芍metros t谷cnicos desde un formulario din芍mico web, los convierte en objetos JSON validados contra las especificaciones de SmartVista (ip, puertos, `mhdr`, etc.), genera documentaci車n t谷cnica en formato Markdown y simula/ejecuta la subida de paquetes de configuraci車n a contenedores de **Oracle Cloud Infrastructure (OCI)**.

---

## ?? Tabla de Contenidos

- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Flujo de Trabajo (Workflow)](#-flujo-de-trabajo-workflow)
- [Estructura de Agentes](#-estructura-de-agentes)
- [Esquema de Datos y Validaci車n](#-esquema-de-datos-y-validaci車n)
- [Requisitos Previos](#-requisitos-previos)
- [Instalaci車n y Configuraci車n](#-instalaci車n-y-configuraci車n)
- [Ejecuci車n](#-ejecuci車n)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Contribuciones](#-contribuciones)
- [Licencia](#-licencia)

---

## ?? Arquitectura del Sistema

El proyecto integra una **Capa Cliente (Frontend Web)** comunicada as赤ncronamente v赤a HTTP/JSON con un **Servidor de Agentes (FastAPI + LangGraph)**. La orquestaci車n backend sustituye los flujos secuenciales r赤gidos por un **grafo determinista con agentes especializados**.

```text
[ Cliente Web / Frontend HTML5 + JS ]
                 岫
                 岫 (POST /api/generate-config)
                 �
庚岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸庖
岫              BACKEND API (FastAPI Orchestrator)          岫
岫                                                          岫
岫                 +---------------+                        岫
岫                 | Router Node   |<-------------------+   岫
岫                 +-------+-------+                    |   岫
岫                         |                            |   岫
岫    +--------------------+--------------------+       |   岫
岫    |            |               |            |       |   岫
岫    v            v               v            v       |   岫
岫 +-----+      +-----+         +-----+      +-----+    |   岫
岫 |Ingr.|      |Const|         |Valid|      |Docum|    |   岫
岫 |Agent|      |Agent|         |Agent|      |Agent|    |   岫
岫 +--+--+      +--+--+         +--+--+      +--+--+    |   岫
岫    |            |               |            |       |   岫
岫    +------------+---------------+------------+       |   岫
岫                         | (Validaci車n OK + Doc)      |   岫
岫                         v                            |   岫
岫                 +---------------+                    |   岫
岫                 |  Supervisor   |--------------------+   岫
岫                 +-------+-------+                        岫
岫                         |                                岫
弩岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸拈岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸岸彼
                          �
           [ Respuesta JSON / Config SVLB ]

```

---

## ?? Flujo de Trabajo (Workflow)

1. **Ingreso (Frontend / API):** El usuario ingresa una solicitud v赤a interfaz web (formulario estructurado) o en lenguaje natural.
2. **Interpretaci車n:** El **Ingress Agent** valida los par芍metros iniciales o traduce la solicitud a especificaciones de red (`raddr`, `lport`, `mhdr`).
3. **Generaci車n:** El **Constructor Agent** arma el bloque de c車digo JSON respetando el est芍ndar del manual de SmartVista Load Balancer.
4. **Validaci車n y Autorreparaci車n:** El **Validator Agent** eval迆a la sintaxis mediante esquemas Pydantic (`SmartVistaLBRule`). Si se identifican errores de rango, sintaxis de cabecera o puerto, activa el sub-ciclo de reparaci車n.
5. **Documentaci車n & Cloud:** El **Documenter Agent** crea la ficha t谷cnica en Markdown y emite los enlaces del repositorio en OCI Object Storage.
6. **Consolidaci車n:** El **Supervisor** presenta la configuraci車n t谷cnica validada (`node_config`, `rule_src_config`) y la retorna a la interfaz web para su visualizaci車n/descarga.

---

## ?? Estructura de Agentes

| Agente / Nodo | Funci車n Principal | Salida Producida |
| --- | --- | --- |
| **Router Node** | Eval迆a el estado del grafo y toma la decisi車n determinista de enrutamiento mediante un esquema Pydantic. | `next_node` ("ingress", "constructor", "validator", "documenter", "supervisor") |
| **Ingress Agent** | Extrae requerimientos t谷cnicos (IP, puerto, rango, protocolo, `mhdr`) a partir del payload API o lenguaje natural. | `raw_requirements` |
| **Constructor Agent** | Genera la definici車n estructural de la regla en JSON compatible con SmartVista (`node_config`, `rule_src_config`). | `generated_json_config` |
| **Validator Agent (Repairer)** | Valida sint芍cticamente el JSON contra el esquema Pydantic `SmartVistaLBRule` y reglas del protocolo (`CDb4`, `BHb2`, `visa`, `amex`, etc.). Repara el JSON si hay fallas. | `validation_status` (Boolean), `validation_errors` |
| **Documenter Agent** | Redacta la ficha t谷cnica y coordina las llamadas a herramientas externas (OCI Object Storage API). | `final_documentation`, `oci_object_link` |
| **Supervisor Node** | Redacta la respuesta final y devuelve la estructura JSON/Markdown consolidada al endpoint de la API. | `generated_config` + `messages` |

---

## ?? Esquema de Datos y Validaci車n

Toda configuraci車n generada cumple con los tipos de datos requeridos por la estructura base de **SmartVista Load Balancer**.

```python
class SmartVistaLBRule(BaseModel):
    ip: str = Field(description="Direcci車n IP destino o 0.0.0.0 para cualquier origen.")
    port: str = Field(description="Puerto individual (ej. 10000) o rango de puertos (ej. 20001-20005).")
    range_count: Optional[str] = Field(default=None, description="Cantidad de conexiones consecutivas en rango (ej. 10/BHb2).")
    mhdr_preset: str = Field(description="Tipo o formato de enmarcado de cabecera (CDb4, BHb2, visa, amex, custom).")
    custom_mhdr: Optional[str] = Field(default=None, description="Sintaxis de cabecera gen谷rica personalizada (ej. x800BHb2).")

```

---

## ?? Requisitos Previos

* **Python:** 3.10 o superior.
* **OpenAI API Key:** Acceso a modelos GPT-4o o equivalentes.
* **Librer赤as Clave:**
* `fastapi`
* `uvicorn`
* `langgraph`
* `langchain-core`
* `langchain-openai`
* `pydantic`



---

## ?? Instalaci車n y Configuraci車n

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
Crea un archivo `.env` en la ra赤z del proyecto:

```env
OPENAI_API_KEY="tu-api-key-aqui"
OCI_COMPARTMENT_ID="ocid1.compartment.oc1.."  # Opcional para despliegue OCI real

```

---

## ?? Ejecuci車n

El proyecto consta de dos partes: el servicio backend API de agentes y la interfaz gr芍fica de usuario.

### 1. Iniciar el Backend (FastAPI + LangGraph)

Ejecuta el servidor backend Uvicorn:

```bash
uvicorn app:app --reload --port 8000

```

*El backend quedar芍 escuchando en `http://127.0.0.1:8000` y desplegar芍 la documentaci車n interactiva en `http://127.0.0.1:8000/docs`.*

### 2. Iniciar la Interfaz Web (Frontend)

* Abre el archivo `index.html` directamente en tu navegador o mediante la extensi車n **Live Server** en Visual Studio Code.
* Configura los par芍metros de IP, Puerto y Cabecera (`mhdr`) y haz clic en **Procesar con Agentes Backend**.

---

## ?? Estructura del Proyecto

```text
lb-automation-builder/
念岸岸 config/
岫   弩岸岸 settings.py             # Configuraci車n general de variables y claves API
念岸岸 schemas/
岫   念岸岸 lb_schema.py            # Esquema Pydantic SmartVistaLBRule
岫   弩岸岸 router_schema.py        # Esquema de decisi車n para RouterDecision
念岸岸 nodes/
岫   念岸岸 router.py               # L車gica del nodo enrutador
岫   念岸岸 agents.py               # Nodos de agentes (Ingress, Constructor, Validator, Documenter)
岫   弩岸岸 supervisor.py           # Nodo final de consolidaci車n
念岸岸 tools/
岫   弩岸岸 oci_tools.py            # Herramientas de integraci車n con Oracle Cloud Infrastructure
念岸岸 app.py                      # Servidor backend API (FastAPI) y orquestaci車n de endpoints
念岸岸 graph.py                    # Ensamble de nodos y bordes condicionales en LangGraph
念岸岸 main.py                     # Punto de entrada para ejecuci車n por CLI
念岸岸 index.html                  # Interfaz web cliente (HTML5/CSS3/JavaScript)
念岸岸 requirements.txt            # Dependencias del proyecto
弩岸岸 README.md                   # Documentaci車n del proyecto

```

---

## ?? Contribuciones

Las contribuciones son bienvenidas. Para cambios mayores, abre un *issue* primero para discutir lo que te gustar赤a modificar o mejorar.

---

## ?? Licencia

Este proyecto est芍 distribuido bajo la licencia MIT. Consulta el archivo `LICENSE` para m芍s detalles.

```

```
