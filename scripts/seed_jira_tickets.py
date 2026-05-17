#!/usr/bin/env python3
"""
Seed script — creates 20 Jira demo tickets distributed across the 6 roles.
If JIRA_API_TOKEN is not configured, runs in dry-run mode and prints what
would be created.

Usage:
    docker-compose exec backend python scripts/seed_jira_tickets.py
    # or locally:
    python scripts/seed_jira_tickets.py
"""

import os
import sys
import json
from typing import Optional

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config from environment
# ---------------------------------------------------------------------------

JIRA_URL = os.environ.get("JIRA_URL", "").rstrip("/")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
JIRA_PROJECT_KEY = os.environ.get("JIRA_PROJECT_KEY", "DEMO")

DRY_RUN = not bool(JIRA_API_TOKEN and JIRA_URL and JIRA_EMAIL)

# ---------------------------------------------------------------------------
# Ticket definitions — 20 tickets across 6 roles
# ---------------------------------------------------------------------------

TICKETS = [
    # ----- QA Engineer (3 tickets) -----
    {
        "role": "qa_engineer",
        "summary": "[QA Onboarding] Configurar entorno local de pruebas automatizadas",
        "description": (
            "El nuevo QA Engineer debe configurar su entorno de testing local:\n\n"
            "1. Clonar el repositorio de pruebas\n"
            "2. Instalar dependencias de pytest y playwright\n"
            "3. Ejecutar la suite de smoke tests y verificar que pasan\n"
            "4. Leer la guia de convencion de nombres para tests\n\n"
            "Criterio de aceptacion: La suite de smoke tests pasa al 100% en el entorno local."
        ),
        "issue_type": "Task",
        "priority": "High",
    },
    {
        "role": "qa_engineer",
        "summary": "[QA Onboarding] Revisar y documentar un bug existente en el backlog",
        "description": (
            "Seleccionar un bug de severidad Media del backlog de QA y:\n\n"
            "1. Reproducir el bug en el entorno de staging\n"
            "2. Documentar los pasos de reproduccion con capturas\n"
            "3. Identificar el componente afectado\n"
            "4. Proponer un caso de test para prevenir regresion\n\n"
            "Este ejercicio familiariza al nuevo QA con el flujo de trabajo del equipo."
        ),
        "issue_type": "Task",
        "priority": "Medium",
    },
    {
        "role": "qa_engineer",
        "summary": "[QA Onboarding] Participar en sesion de planning de QA como observador",
        "description": (
            "Asistir a la proxima sesion de sprint planning del equipo de QA.\n\n"
            "Objetivos:\n"
            "- Entender como se priorizan los casos de test en el sprint\n"
            "- Conocer las herramientas de gestion (TestRail / Xray)\n"
            "- Preguntar sobre el proceso de regression testing\n\n"
            "Entregar: Resumen de 1 pagina con aprendizajes clave."
        ),
        "issue_type": "Task",
        "priority": "Low",
    },

    # ----- Backend Developer (4 tickets) -----
    {
        "role": "backend_developer",
        "summary": "[Backend Onboarding] Setup entorno local con Docker y ejecutar migraciones",
        "description": (
            "Configurar el entorno de desarrollo backend:\n\n"
            "1. Clonar el repositorio principal\n"
            "2. Copiar .env.example a .env y configurar variables locales\n"
            "3. Ejecutar `docker-compose up` y verificar que todos los servicios arrancan\n"
            "4. Ejecutar `alembic upgrade head` y verificar el schema en la DB\n"
            "5. Ejecutar los tests unitarios con `pytest`\n\n"
            "Criterio de aceptacion: Todos los tests pasan, API responde en http://localhost:8000/health"
        ),
        "issue_type": "Task",
        "priority": "High",
    },
    {
        "role": "backend_developer",
        "summary": "[Backend Onboarding] Implementar endpoint de health check extendido",
        "description": (
            "Como primera tarea de codigo real, implementar un endpoint `/health/detailed`\n"
            "que retorne el estado de todos los servicios dependientes:\n\n"
            "- Estado de la conexion a PostgreSQL\n"
            "- Estado de la conexion a Redis\n"
            "- Version de la aplicacion\n"
            "- Tiempo de uptime\n\n"
            "Seguir los patrones de la API existentes. Incluir test unitario."
        ),
        "issue_type": "Story",
        "priority": "Medium",
    },
    {
        "role": "backend_developer",
        "summary": "[Backend Onboarding] Code review — entender los patrones de la API",
        "description": (
            "Revisar el codigo de los endpoints existentes para entender:\n\n"
            "1. Estructura de routers con FastAPI\n"
            "2. Uso de schemas Pydantic para validacion\n"
            "3. Patron de acceso a base de datos con SQLAlchemy async\n"
            "4. Manejo de errores y excepciones customizadas\n\n"
            "Preparar preguntas para la sesion 1:1 con el tech lead."
        ),
        "issue_type": "Task",
        "priority": "High",
    },
    {
        "role": "backend_developer",
        "summary": "[Backend Onboarding] Agregar migracion Alembic para nueva columna",
        "description": (
            "Ejercicio practico de migraciones:\n\n"
            "1. Agregar el campo `timezone: str` al modelo User\n"
            "2. Crear la migracion con `alembic revision --autogenerate`\n"
            "3. Aplicar la migracion y verificar el schema\n"
            "4. Hacer rollback con `alembic downgrade -1` y verificar\n\n"
            "Objetivo: Familiarizarse con el flujo de migraciones del equipo."
        ),
        "issue_type": "Task",
        "priority": "Medium",
    },

    # ----- Frontend Developer (3 tickets) -----
    {
        "role": "frontend_developer",
        "summary": "[Frontend Onboarding] Setup entorno Next.js y ejecutar Storybook",
        "description": (
            "Configurar el entorno frontend:\n\n"
            "1. `npm install` en el directorio frontend\n"
            "2. Ejecutar `npm run dev` y verificar que la app corre en localhost:3000\n"
            "3. Ejecutar `npm run storybook` y explorar el catalogo de componentes\n"
            "4. Leer el archivo DESIGN_SYSTEM.md\n\n"
            "Criterio de aceptacion: Storybook corre sin errores y el dev server responde."
        ),
        "issue_type": "Task",
        "priority": "High",
    },
    {
        "role": "frontend_developer",
        "summary": "[Frontend Onboarding] Implementar componente Badge de estado de onboarding",
        "description": (
            "Crear un componente React `<OnboardingStatusBadge status={status} />` que:\n\n"
            "- Acepte los valores: 'active', 'interviewing', 'completed', 'paused'\n"
            "- Use los tokens de color del design system\n"
            "- Incluya historia en Storybook con todos los estados\n"
            "- Incluya test con React Testing Library\n\n"
            "Seguir las convenciones del directorio `components/ui/`."
        ),
        "issue_type": "Story",
        "priority": "Medium",
    },
    {
        "role": "frontend_developer",
        "summary": "[Frontend Onboarding] Revisar arquitectura de estado global con Zustand",
        "description": (
            "Entender como se maneja el estado global en la aplicacion:\n\n"
            "1. Leer la documentacion del store principal en `store/`\n"
            "2. Trazar el flujo de datos desde la API hasta un componente de lista\n"
            "3. Identificar donde se manejan los estados de loading/error\n\n"
            "Entregar: Diagrama simple del flujo de datos para la feature de onboarding."
        ),
        "issue_type": "Task",
        "priority": "Low",
    },

    # ----- DevOps / SRE (4 tickets) -----
    {
        "role": "devops_sre",
        "summary": "[DevOps Onboarding] Acceso y orientacion en el cluster de Kubernetes",
        "description": (
            "Obtener acceso al cluster y familiarizarse con la infraestructura:\n\n"
            "1. Configurar kubeconfig con las credenciales provistas\n"
            "2. Ejecutar `kubectl get pods --all-namespaces` y verificar el estado\n"
            "3. Identificar los namespaces de produccion, staging y desarrollo\n"
            "4. Leer el runbook de on-call en la wiki del equipo\n\n"
            "Criterio de aceptacion: Acceso verificado y runbook leido."
        ),
        "issue_type": "Task",
        "priority": "High",
    },
    {
        "role": "devops_sre",
        "summary": "[DevOps Onboarding] Revisar y mejorar el pipeline de CI/CD",
        "description": (
            "Analizar el pipeline actual de GitHub Actions:\n\n"
            "1. Identificar los workflows existentes\n"
            "2. Medir el tiempo promedio de build en los ultimos 10 runs\n"
            "3. Proponer al menos 2 mejoras de performance (caching, paralelizacion)\n"
            "4. Implementar una de las mejoras con aprobacion del tech lead\n\n"
            "Objetivo: Reducir el tiempo de build en al menos 20%."
        ),
        "issue_type": "Story",
        "priority": "Medium",
    },
    {
        "role": "devops_sre",
        "summary": "[DevOps Onboarding] Configurar alertas de SLO en Grafana",
        "description": (
            "Revisar y actualizar las alertas de SLO:\n\n"
            "1. Acceder al dashboard de Grafana de SLOs\n"
            "2. Verificar que las alertas de disponibilidad (99.9%) esten activas\n"
            "3. Simular una caida y verificar que la alerta llega a PagerDuty\n"
            "4. Documentar cualquier alerta desconfigurada como bug\n\n"
            "Este ejercicio asegura que el nuevo SRE entiende el sistema de alertas."
        ),
        "issue_type": "Task",
        "priority": "High",
    },
    {
        "role": "devops_sre",
        "summary": "[DevOps Onboarding] Documentar proceso de disaster recovery",
        "description": (
            "Como primer proyecto de Staff, actualizar la documentacion de DR:\n\n"
            "1. Revisar el runbook de DR existente\n"
            "2. Ejecutar el proceso de restore desde backup en staging\n"
            "3. Medir el RTO y RPO reales vs los objetivos\n"
            "4. Actualizar el runbook con hallazgos y mejoras\n\n"
            "Entregable: Runbook actualizado revisado por el equipo de SRE."
        ),
        "issue_type": "Story",
        "priority": "High",
    },

    # ----- Data Engineer (3 tickets) -----
    {
        "role": "data_engineer",
        "summary": "[Data Onboarding] Explorar el data warehouse y modelo de datos",
        "description": (
            "Familiarizarse con la arquitectura de datos:\n\n"
            "1. Conectarse al warehouse con las credenciales del equipo\n"
            "2. Explorar los schemas de raw, staging y marts\n"
            "3. Correr una query que una 3 tablas del mart principal\n"
            "4. Leer la documentacion de DBT en el repositorio\n\n"
            "Criterio de aceptacion: Query ejecutada, resultados verificados con el data lead."
        ),
        "issue_type": "Task",
        "priority": "High",
    },
    {
        "role": "data_engineer",
        "summary": "[Data Onboarding] Agregar test de calidad de datos en DBT",
        "description": (
            "Primera contribucion al repositorio DBT:\n\n"
            "1. Identificar una tabla del staging sin tests de calidad\n"
            "2. Agregar tests de not_null y unique a las columnas clave\n"
            "3. Ejecutar `dbt test` y verificar que los tests pasan\n"
            "4. Abrir PR con los cambios\n\n"
            "Seguir las convenciones del archivo CONTRIBUTING.md del repositorio."
        ),
        "issue_type": "Story",
        "priority": "Medium",
    },
    {
        "role": "data_engineer",
        "summary": "[Data Onboarding] Revisar y ejecutar pipeline de ingestion en Airflow",
        "description": (
            "Entender el sistema de orquestacion:\n\n"
            "1. Acceder a la UI de Airflow\n"
            "2. Identificar los DAGs de ingestion principales\n"
            "3. Hacer trigger manual de un DAG de staging\n"
            "4. Investigar y documentar la ultima falla de un DAG\n\n"
            "Objetivo: Entender el flujo de datos de origen a warehouse."
        ),
        "issue_type": "Task",
        "priority": "Medium",
    },

    # ----- Product Manager (3 tickets) -----
    {
        "role": "product_manager",
        "summary": "[PM Onboarding] Revisar el roadmap del producto y OKRs del trimestre",
        "description": (
            "Inmersion en la estrategia de producto:\n\n"
            "1. Leer el documento de strategy y vision del producto\n"
            "2. Revisar los OKRs del trimestre actual en Notion\n"
            "3. Identificar las 3 iniciativas mas criticas del roadmap\n"
            "4. Preparar preguntas para la sesion con el Head of Product\n\n"
            "Entregable: Documento de 1 pagina con comprension de prioridades actuales."
        ),
        "issue_type": "Task",
        "priority": "High",
    },
    {
        "role": "product_manager",
        "summary": "[PM Onboarding] Conducir 3 sesiones de discovery con usuarios",
        "description": (
            "Proceso de discovery para entender al usuario:\n\n"
            "1. Revisar las guias de entrevistas de usuario del equipo\n"
            "2. Coordinar 3 entrevistas con usuarios actuales del producto\n"
            "3. Documentar insights y pain points identificados\n"
            "4. Presentar hallazgos al equipo de producto\n\n"
            "Objetivo: Desarrollar empatia con el usuario desde el primer mes."
        ),
        "issue_type": "Story",
        "priority": "Medium",
    },
    {
        "role": "product_manager",
        "summary": "[PM Onboarding] Escribir PRD para una feature del backlog",
        "description": (
            "Primera contribucion real como PM:\n\n"
            "1. Seleccionar una feature de impacto medio del backlog\n"
            "2. Escribir el PRD usando la plantilla del equipo\n"
            "3. Incluir: contexto, objetivo, user stories, metricas de exito, non-goals\n"
            "4. Presentar el PRD en la proxima sesion de refinamiento\n\n"
            "Criterio de aceptacion: PRD aprobado por el Head of Product."
        ),
        "issue_type": "Story",
        "priority": "Medium",
    },
]

# ---------------------------------------------------------------------------
# Jira API helpers
# ---------------------------------------------------------------------------

def create_jira_ticket(ticket: dict) -> Optional[str]:
    """Create a Jira ticket and return the issue key, or None on error."""
    url = f"{JIRA_URL}/rest/api/3/issue"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    auth = (JIRA_EMAIL, JIRA_API_TOKEN)

    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": ticket["summary"],
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": ticket["description"]}],
                    }
                ],
            },
            "issuetype": {"name": ticket["issue_type"]},
            "priority": {"name": ticket["priority"]},
            "labels": [f"onboarding-{ticket['role'].replace('_', '-')}"],
        }
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, auth=auth, timeout=10)
        resp.raise_for_status()
        key = resp.json().get("key", "UNKNOWN")
        return key
    except requests.RequestException as exc:
        print(f"  ERROR creando ticket: {exc}")
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("TechOnboard — Seed de tickets Jira")
    print("=" * 60)

    if DRY_RUN:
        print("\nMODO DRY-RUN — JIRA_API_TOKEN no configurado.")
        print(f"Se crearian {len(TICKETS)} tickets en el proyecto {JIRA_PROJECT_KEY}:\n")

        by_role: dict = {}
        for ticket in TICKETS:
            role = ticket["role"]
            by_role.setdefault(role, []).append(ticket)

        for role, role_tickets in by_role.items():
            print(f"\n  [{role.upper()} — {len(role_tickets)} tickets]")
            for i, t in enumerate(role_tickets, 1):
                print(f"    {i}. [{t['issue_type']}] [{t['priority']}] {t['summary']}")

        print(f"\nTotal: {len(TICKETS)} tickets")
        print("\nPara crear los tickets reales, configura las variables:")
        print("  JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY")
        return

    # Real Jira creation
    print(f"\nConectando a Jira: {JIRA_URL}")
    print(f"Proyecto: {JIRA_PROJECT_KEY}")
    print(f"Creando {len(TICKETS)} tickets...\n")

    created = []
    failed = 0

    for ticket in TICKETS:
        print(f"  Creando: {ticket['summary'][:60]}...", end=" ")
        key = create_jira_ticket(ticket)
        if key:
            print(f"-> {key}")
            created.append(key)
        else:
            print("-> FALLO")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Tickets creados: {len(created)}")
    if created:
        print(f"  Rango: {created[0]} — {created[-1]}")
    if failed:
        print(f"Tickets fallidos: {failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()
