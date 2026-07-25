# Load Balancer Automation Builder (LB Automation Builder) 馃殌

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Framework](https://img.shields.io/badge/Framework-LangGraph-orange.svg)
![Validation](https://img.shields.io/badge/Validation-Pydantic-green.svg)
![Infrastructure](https://img.shields.io/badge/Cloud-Oracle%20Cloud%20(OCI)-red.svg)

**LB Automation Builder** es un sistema orquestado por una **arquitectura multiagente distribuida** sobre **LangGraph** dise帽ada para automatizar el ciclo de vida de administraci贸n, configuraci贸n, validaci贸n y documentaci贸n de reglas para **SmartVista Load Balancer**.

El sistema procesa requerimientos operativos expresados en lenguaje natural o especificaciones parciales, los convierte en objetos JSON validados, genera documentaci贸n t茅cnica en formato Markdown y simula/ejecuta la subida de paquetes de configuraci贸n a contenedores de **Oracle Cloud Infrastructure (OCI)**.

---

## 馃搫 Tabla de Contenidos

- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Flujo de Trabajo (Workflow)](#-flujo-de-trabajo-workflow)
- [Estructura de Agentes](#-estructura-de-agentes)
- [Esquema de Datos y Validaci贸n](#-esquema-de-datos-y-validaci贸n)
- [Requisitos Previos](#-requisitos-previos)
- [Instalaci贸n y Configuraci贸n](#-instalaci贸n-y-configuraci贸n)
- [Ejecuci贸n](#-ejecuci贸n)
- [Estructura del Proyecto](#-estructura-del-proyecto)

---

## 馃彈 Arquitectura del Sistema

El proyecto sustituye los flujos secuenciales r铆gidos por un **grafo determinista con agentes especializados**. La comunicaci贸n entre nodos se realiza a trav茅s de un estado global compartido (`LBAutomationState`), donde un **Supervising Router** eval煤a continuamente la condici贸n de la configuraci贸n para enrutar la ejecuci贸n hacia el agente m谩s adecuado.


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
| (Validaci贸n OK + Doc lista)
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
2. **Interpretación:** El **Ingress Agent** traduce la solicitud a parámetros técnicos clave.
3. **Generación:** El **Constructor Agent** arma el bloque de código JSON de acuerdo al estándar de SmartVista.
4. **Validación y Autorreparación:** El **Validator Agent** evalúa la sintaxis mediante esquemas Pydantic. Si se identifican errores, activa el sub-ciclo de reparación.
5. **Documentación & Cloud:** El **Documenter Agent** crea la ficha técnica en Markdown y emite los enlaces de repositorio en OCI Object Storage.
6. **Consolidación:** El **Supervisor** presenta el reporte final integrado.

---

## ?? Estructura de Agentes

| Agente / Nodo | Función Principal | Salida Producida |
| :--- | :--- | :--- |
| **Router Node** | Evalúa el estado del grafo y toma la decisión determinista de enrutamiento mediante un esquema de Pydantic. | `next_node` ("ingress", "constructor", "validator", "documenter", "supervisor") |
| **Ingress Agent** | Extrae requerimientos técnicos (puerto, protocolo, algoritmo, backends) a partir de lenguaje natural. | `raw_requirements` |
| **Constructor Agent** | Genera la definición estructural de la regla en JSON compatible con SmartVista. | `generated_json_config` |
| **Validator Agent (Repairer)** | Valida estricta y sintácticamente el JSON generado contra el esquema Pydantic `SmartVistaLBRule`. Repara el JSON en caso de error. | `validation_status` (Boolean), `validation_errors` |
| **Documenter Agent** | Redacta la ficha técnica y coordina las llamadas a herramientas externas (OCI Object Storage API). | `final_documentation`, `oci_object_link` |
| **Supervisor Node** | Redacta la respuesta y despliega la consola/resumen final para el usuario. | `messages` (Markdown + JSON + Enlaces) |

---

## ?? Esquema de Datos y Validación

Toda configuración generada debe ser compatible con la estructura base de **SmartVista Load Balancer**.

```python
class SmartVistaLBRule(BaseModel):
    rule_name: str = Field(description="Nombre único de la regla de balanceo.")
    listen_port: int = Field(description="Puerto de escucha (ej. 8088).")
    protocol: Literal["TCP", "HTTP", "HTTPS", "ISO8583"] = Field(description="Protocolo de red.")
    algorithm: Literal["ROUND_ROBIN", "LEAST_CONNECTIONS", "IP_HASH"] = Field(description="Algoritmo de distribución.")
    backend_servers: List[str] = Field(description="Direcciones IP:Puerto de los servidores destino.")
    health_check_endpoint: Optional[str] = Field(default="/health", description="Ruta de comprobación de estado.")
    timeout_ms: int = Field(default=5000, description="Tiempo límite de respuesta en ms.")

```