# Load Balancer Automation Builder (LB Automation Builder) ðŸš€

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Framework](https://img.shields.io/badge/Framework-LangGraph-orange.svg)
![Validation](https://img.shields.io/badge/Validation-Pydantic-green.svg)
![Infrastructure](https://img.shields.io/badge/Cloud-Oracle%20Cloud%20(OCI)-red.svg)

**LB Automation Builder** es un sistema orquestado por una **arquitectura multiagente distribuida** sobre **LangGraph** diseÃ±ada para automatizar el ciclo de vida de administraciÃ³n, configuraciÃ³n, validaciÃ³n y documentaciÃ³n de reglas para **SmartVista Load Balancer**.

El sistema procesa requerimientos operativos expresados en lenguaje natural o especificaciones parciales, los convierte en objetos JSON validados, genera documentaciÃ³n tÃ©cnica en formato Markdown y simula/ejecuta la subida de paquetes de configuraciÃ³n a contenedores de **Oracle Cloud Infrastructure (OCI)**.

---

## ðŸ“„ Tabla de Contenidos

- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Flujo de Trabajo (Workflow)](#-flujo-de-trabajo-workflow)
- [Estructura de Agentes](#-estructura-de-agentes)
- [Esquema de Datos y ValidaciÃ³n](#-esquema-de-datos-y-validaciÃ³n)
- [Requisitos Previos](#-requisitos-previos)
- [InstalaciÃ³n y ConfiguraciÃ³n](#-instalaciÃ³n-y-configuraciÃ³n)
- [EjecuciÃ³n](#-ejecuciÃ³n)
- [Estructura del Proyecto](#-estructura-del-proyecto)

---

## ðŸ— Arquitectura del Sistema

El proyecto sustituye los flujos secuenciales rÃ­gidos por un **grafo determinista con agentes especializados**. La comunicaciÃ³n entre nodos se realiza a travÃ©s de un estado global compartido (`LBAutomationState`), donde un **Supervising Router** evalÃºa continuamente la condiciÃ³n de la configuraciÃ³n para enrutar la ejecuciÃ³n hacia el agente mÃ¡s adecuado.


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
| (ValidaciÃ³n OK + Doc lista)
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
2. **Interpretaci¨®n:** El **Ingress Agent** traduce la solicitud a par¨¢metros t¨¦cnicos clave.
3. **Generaci¨®n:** El **Constructor Agent** arma el bloque de c¨®digo JSON de acuerdo al est¨¢ndar de SmartVista.
4. **Validaci¨®n y Autorreparaci¨®n:** El **Validator Agent** eval¨²a la sintaxis mediante esquemas Pydantic. Si se identifican errores, activa el sub-ciclo de reparaci¨®n.
5. **Documentaci¨®n & Cloud:** El **Documenter Agent** crea la ficha t¨¦cnica en Markdown y emite los enlaces de repositorio en OCI Object Storage.
6. **Consolidaci¨®n:** El **Supervisor** presenta el reporte final integrado.

---

## ?? Estructura de Agentes

| Agente / Nodo | Funci¨®n Principal | Salida Producida |
| :--- | :--- | :--- |
| **Router Node** | Eval¨²a el estado del grafo y toma la decisi¨®n determinista de enrutamiento mediante un esquema de Pydantic. | `next_node` ("ingress", "constructor", "validator", "documenter", "supervisor") |
| **Ingress Agent** | Extrae requerimientos t¨¦cnicos (puerto, protocolo, algoritmo, backends) a partir de lenguaje natural. | `raw_requirements` |
| **Constructor Agent** | Genera la definici¨®n estructural de la regla en JSON compatible con SmartVista. | `generated_json_config` |
| **Validator Agent (Repairer)** | Valida estricta y sint¨¢cticamente el JSON generado contra el esquema Pydantic `SmartVistaLBRule`. Repara el JSON en caso de error. | `validation_status` (Boolean), `validation_errors` |
| **Documenter Agent** | Redacta la ficha t¨¦cnica y coordina las llamadas a herramientas externas (OCI Object Storage API). | `final_documentation`, `oci_object_link` |
| **Supervisor Node** | Redacta la respuesta y despliega la consola/resumen final para el usuario. | `messages` (Markdown + JSON + Enlaces) |

---

## ?? Esquema de Datos y Validaci¨®n

Toda configuraci¨®n generada debe ser compatible con la estructura base de **SmartVista Load Balancer**.

```python
class SmartVistaLBRule(BaseModel):
    rule_name: str = Field(description="Nombre ¨²nico de la regla de balanceo.")
    listen_port: int = Field(description="Puerto de escucha (ej. 8088).")
    protocol: Literal["TCP", "HTTP", "HTTPS", "ISO8583"] = Field(description="Protocolo de red.")
    algorithm: Literal["ROUND_ROBIN", "LEAST_CONNECTIONS", "IP_HASH"] = Field(description="Algoritmo de distribuci¨®n.")
    backend_servers: List[str] = Field(description="Direcciones IP:Puerto de los servidores destino.")
    health_check_endpoint: Optional[str] = Field(default="/health", description="Ruta de comprobaci¨®n de estado.")
    timeout_ms: int = Field(default=5000, description="Tiempo l¨ªmite de respuesta en ms.")

```
---
