---

```markdown
# Load Balancer Automation Builder (LB Automation Builder) 🚀

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Framework](https://img.shields.io/badge/Framework-LangGraph-orange.svg)
![Validation](https://img.shields.io/badge/Validation-Pydantic-green.svg)
![Infrastructure](https://img.shields.io/badge/Cloud-Oracle%20Cloud%20(OCI)-red.svg)

**LB Automation Builder** es un sistema orquestado por una **arquitectura multiagente distribuida** sobre **LangGraph** diseñada para automatizar el ciclo de vida de administración, configuración, validación y documentación de reglas para **SmartVista Load Balancer**.

El sistema procesa requerimientos operativos expresados en lenguaje natural o especificaciones parciales, los convierte en objetos JSON validados, genera documentación técnica en formato Markdown y simula/ejecuta la subida de paquetes de configuración a contenedores de **Oracle Cloud Infrastructure (OCI)**.

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

---

## 🏗 Arquitectura del Sistema

El proyecto sustituye los flujos secuenciales rígidos por un **grafo determinista con agentes especializados**. La comunicación entre nodos se realiza a través de un estado global compartido (`LBAutomationState`), donde un **Supervising Router** evalúa continuamente la condición de la configuración para enrutar la ejecución hacia el agente más adecuado.


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
| (Validación OK + Doc lista)
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