# Load Balancer Automation Builder (LB Automation Builder) ??

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Framework](https://img.shields.io/badge/Framework-LangGraph-orange.svg)
![Validation](https://img.shields.io/badge/Validation-Pydantic-green.svg)
![Infrastructure](https://img.shields.io/badge/Cloud-Oracle%20Cloud%20(OCI)-red.svg)

**LB Automation Builder** es un sistema orquestado por una **arquitectura multiagente distribuida** sobre **LangGraph** dise?ada para automatizar el ciclo de vida de administraci車n, configuraci車n, validaci車n y documentaci車n de reglas para **SmartVista Load Balancer**.

El sistema procesa requerimientos operativos expresados en lenguaje natural o especificaciones parciales, los convierte en objetos JSON validados, genera documentaci車n t谷cnica en formato Markdown y simula/ejecuta la subida de paquetes de configuraci車n a contenedores de **Oracle Cloud Infrastructure (OCI)**.

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

---

## ?? Arquitectura del Sistema

El proyecto sustituye los flujos secuenciales r赤gidos por un **grafo determinista con agentes especializados**. La comunicaci車n entre nodos se realiza a trav谷s de un estado global compartido (`LBAutomationState`), donde un **Supervising Router** eval迆a continuamente la condici車n de la configuraci車n para enrutar la ejecuci車n hacia el agente m芍s adecuado.


```

```
              +-----------------------+
              |      START / USER     |
              +-----------+-----------+
                          |
                          v
                  +---------------+
                  | Router Node   |<-----------------------+
                  +-------+-------+                        |
                          |                                |
    +---------------------+---------------------+            |
    |             |               |             |            |
    v             v               v             v            |

```

+-----------+ +-----------+   +-----------+ +-----------+      |
|  Ingress  | |Constructor|   | Validator | | Documenter|      |
|   Agent   | |   Agent   |   | & Repairer| |   Agent   |      |
+-----+-----+ +-----+-----+   +-----+-----+ +-----+-----+      |
|             |               |             |            |
+-------------+---------------+-------------+------------+
| (Validaci車n OK + Doc lista)
v
+---------------+
|  Supervisor   |
+-------+-------+
|
v
+-----+
| END |
+-----+

```

---

## ?? Flujo de Trabajo (Workflow)

1. **Ingreso (Ingress):** El usuario ingresa una solicitud de balanceo en lenguaje natural.
2. **Interpretaci車n:** El **Ingress Agent** traduce la solicitud a par芍metros t谷cnicos clave.
3. **Generaci車n:** El **Constructor Agent** arma el bloque de c車digo JSON de acuerdo al est芍ndar de SmartVista.
4. **Validaci車n y Autorreparaci車n:** El **Validator Agent** eval迆a la sintaxis mediante esquemas Pydantic. Si se identifican errores, activa el sub-ciclo de reparaci車n.
5. **Documentaci車n & Cloud:** El **Documenter Agent** crea la ficha t谷cnica en Markdown y emite los enlaces de repositorio en OCI Object Storage.
6. **Consolidaci車n:** El **Supervisor** presenta el reporte final integrado.

---

## ?? Estructura de Agentes

| Agente / Nodo | Funci車n Principal | Salida Producida |
| :--- | :--- | :--- |
| **Router Node** | Eval迆a el estado del grafo y toma la decisi車n determinista de enrutamiento mediante un esquema de Pydantic. | `next_node` ("ingress", "constructor", "validator", "documenter", "supervisor") |
| **Ingress Agent** | Extrae requerimientos t谷cnicos (puerto, protocolo, algoritmo, backends) a partir de lenguaje natural. | `raw_requirements` |
| **Constructor Agent** | Genera la definici車n estructural de la regla en JSON compatible con SmartVista. | `generated_json_config` |
| **Validator Agent (Repairer)** | Valida estricta y sint芍cticamente el JSON generado contra el esquema Pydantic `SmartVistaLBRule`. Repara el JSON en caso de error. | `validation_status` (Boolean), `validation_errors` |
| **Documenter Agent** | Redacta la ficha t谷cnica y coordina las llamadas a herramientas externas (OCI Object Storage API). | `final_documentation`, `oci_object_link` |
| **Supervisor Node** | Redacta la respuesta y despliega la consola/resumen final para el usuario. | `messages` (Markdown + JSON + Enlaces) |

---

## ?? Esquema de Datos y Validaci車n

Toda configuraci車n generada debe ser compatible con la estructura base de **SmartVista Load Balancer**.

```python
class SmartVistaLBRule(BaseModel):
    rule_name: str = Field(description="Nombre 迆nico de la regla de balanceo.")
    listen_port: int = Field(description="Puerto de escucha (ej. 8088).")
    protocol: Literal["TCP", "HTTP", "HTTPS", "ISO8583"] = Field(description="Protocolo de red.")
    algorithm: Literal["ROUND_ROBIN", "LEAST_CONNECTIONS", "IP_HASH"] = Field(description="Algoritmo de distribuci車n.")
    backend_servers: List[str] = Field(description="Direcciones IP:Puerto de los servidores destino.")
    health_check_endpoint: Optional[str] = Field(default="/health", description="Ruta de comprobaci車n de estado.")
    timeout_ms: int = Field(default=5000, description="Tiempo l赤mite de respuesta en ms.")

```

---

## ?? Requisitos Previos

* **Python:** 3.10 o superior.
* **OpenAI API Key:** Acceso a modelos GPT-4o o equivalentes.
* **Librer赤as Clave:**
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

Puedes ejecutar el motor de la aplicaci車n ejecutando el script principal:

```bash
python main.py

```

### Ejemplo de Prompt de Entrada:

> "Necesito balancear el tr芍fico transaccional ISO8583 en el puerto 8088. Usa el algoritmo LEAST_CONNECTIONS y los backends 10.0.1.15:8088 y 10.0.1.16:8088. El endpoint de healthcheck es /check."

---