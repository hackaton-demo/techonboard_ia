#!/usr/bin/env python3
"""
Seed script for TechOnboard demo data.
Usage:
    docker compose exec backend python scripts/seed_demo_data.py
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

try:
    import asyncpg
except ImportError:
    print("ERROR: asyncpg not installed.")
    sys.exit(1)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://techonboard:password@localhost:5432/techonboard",
)
ASYNCPG_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

now = datetime.now(timezone.utc)

# UUIDs fijos para reproducibilidad
AGENT_QA    = UUID("4db122c7-4e94-4828-a998-e0b4078388c8")
AGENT_BE    = UUID("b53c2e63-87f3-415a-8292-fa2487a5ea7a")
AGENT_FE    = UUID("5947ec25-5d83-48cd-b933-6b20be931a83")
AGENT_DO    = UUID("875d9fde-4fb9-47b2-9967-4509ac17fba9")
AGENT_DE    = UUID("30fb9bd7-afa3-4fcc-9f17-e8f095f99dce")
AGENT_AI    = UUID("1ef4a953-b66a-42b7-a29e-e3b3d48cec17")

SESSION_1   = UUID("22222222-0001-0001-0001-000000000001")
SESSION_2   = UUID("22222222-0002-0002-0002-000000000002")
SESSION_3   = UUID("22222222-0003-0003-0003-000000000003")

AUDIT_1     = UUID("33333333-0001-0001-0001-000000000001")
AUDIT_2     = UUID("33333333-0002-0002-0002-000000000002")
AUDIT_3     = UUID("33333333-0003-0003-0003-000000000003")
AUDIT_4     = UUID("33333333-0004-0004-0004-000000000004")
AUDIT_5     = UUID("33333333-0005-0005-0005-000000000005")

AGENTS = [
    {
        "id": AGENT_QA,
        "name": "QA Engineer",
        "category": "qa",
        "slug": "qa-engineer",
        "icon": "🧪",
        "seniority_levels": json.dumps(["junior", "mid", "senior"]),
        "stack_keywords": json.dumps(["playwright", "cypress", "selenium", "pytest"]),
        "tools": json.dumps({"testing_e2e": ["Playwright", "Cypress"], "api_testing": ["Postman"]}),
        "access_rules": json.dumps({"junior": {"github_repos": "auto", "production": "blocked"}}),
        "learning_sequence": json.dumps(["Estrategia de testing", "Suite E2E local", "Flujos criticos"]),
        "ticket_criteria": json.dumps({"junior": "Flujo E2E simple de happy path. Tiempo: 4-6h."}),
        "interview_questions": json.dumps({"stack_detection": "Con que framework E2E tienes experiencia?"}),
        "lobster_trap_policy_file": "qa_engineer.yaml",
        "system_prompt_template": "Eres el agente de onboarding para QA Engineer.",
        "is_custom": False,
    },
    {
        "id": AGENT_BE,
        "name": "Backend Developer",
        "category": "dev",
        "slug": "backend-developer",
        "icon": "⚙️",
        "seniority_levels": json.dumps(["junior", "mid", "senior", "lead"]),
        "stack_keywords": json.dumps(["python", "fastapi", "nodejs", "postgresql", "redis"]),
        "tools": json.dumps({"languages": ["Python", "Node.js", "Go"], "frameworks": ["FastAPI", "Express"]}),
        "access_rules": json.dumps({"junior": {"github_repos": "auto", "production": "blocked"}}),
        "learning_sequence": json.dumps(["Arquitectura general", "Setup local", "Postman collection"]),
        "ticket_criteria": json.dumps({"junior": "Agregar validacion a endpoint existente. Tiempo: 4-6h."}),
        "interview_questions": json.dumps({"stack_detection": "Con que lenguaje backend tienes experiencia?"}),
        "lobster_trap_policy_file": "backend_dev.yaml",
        "system_prompt_template": "Eres el agente de onboarding para Backend Developer.",
        "is_custom": False,
    },
    {
        "id": AGENT_FE,
        "name": "Frontend Developer",
        "category": "dev",
        "slug": "frontend-developer",
        "icon": "🎨",
        "seniority_levels": json.dumps(["junior", "mid", "senior"]),
        "stack_keywords": json.dumps(["react", "typescript", "tailwind", "nextjs"]),
        "tools": json.dumps({"frameworks": ["React", "Vue", "Next.js"], "styling": ["Tailwind CSS"]}),
        "access_rules": json.dumps({"junior": {"github_repos_frontend": "auto", "prod_api_keys": "blocked"}}),
        "learning_sequence": json.dumps(["Design system", "Setup local", "Routing y estado"]),
        "ticket_criteria": json.dumps({"junior": "Actualizar componente UI con nueva variante. Tiempo: 3-5h."}),
        "interview_questions": json.dumps({"stack_detection": "Con que framework frontend tienes experiencia?"}),
        "lobster_trap_policy_file": "frontend_dev.yaml",
        "system_prompt_template": "Eres el agente de onboarding para Frontend Developer.",
        "is_custom": False,
    },
    {
        "id": AGENT_DO,
        "name": "DevOps / SRE",
        "category": "ops",
        "slug": "devops-sre",
        "icon": "🚀",
        "seniority_levels": json.dumps(["mid", "senior", "staff"]),
        "stack_keywords": json.dumps(["terraform", "kubernetes", "docker", "datadog"]),
        "tools": json.dumps({"iac": ["Terraform", "Pulumi"], "containers": ["Docker", "Kubernetes"]}),
        "access_rules": json.dumps({"mid": {"github_repos_infra": "auto", "aws_prod": "blocked"}}),
        "learning_sequence": json.dumps(["Arquitectura cloud", "Pipeline CI/CD", "Runbooks"]),
        "ticket_criteria": json.dumps({"mid": "Agregar alerta de Datadog en staging. Tiempo: 4-8h."}),
        "interview_questions": json.dumps({"stack_detection": "Con que cloud provider tienes experiencia?"}),
        "lobster_trap_policy_file": "devops_sre.yaml",
        "system_prompt_template": "Eres el agente de onboarding para DevOps/SRE.",
        "is_custom": False,
    },
    {
        "id": AGENT_DE,
        "name": "Data Engineer",
        "category": "data",
        "slug": "data-engineer",
        "icon": "📊",
        "seniority_levels": json.dumps(["junior", "mid", "senior"]),
        "stack_keywords": json.dumps(["python", "dbt", "airflow", "spark", "bigquery"]),
        "tools": json.dumps({"transformation": ["dbt", "Spark", "pandas"], "orchestration": ["Airflow"]}),
        "access_rules": json.dumps({"junior": {"warehouse_staging_read": "auto", "customer_data_raw": "blocked"}}),
        "learning_sequence": json.dumps(["Arquitectura warehouse", "Catalogo tablas", "dbt local"]),
        "ticket_criteria": json.dumps({"junior": "Agregar test de calidad dbt. Tiempo: 4-6h."}),
        "interview_questions": json.dumps({"stack_detection": "Con que herramienta de transformacion tienes experiencia?"}),
        "lobster_trap_policy_file": "data_engineer.yaml",
        "system_prompt_template": "Eres el agente de onboarding para Data Engineer.",
        "is_custom": False,
    },
    {
        "id": AGENT_AI,
        "name": "AI / ML Engineer",
        "category": "ai",
        "slug": "ai-ml-engineer",
        "icon": "🤖",
        "seniority_levels": json.dumps(["junior", "mid", "senior"]),
        "stack_keywords": json.dumps(["python", "pytorch", "langchain", "mlflow", "gemini"]),
        "tools": json.dumps({"llm_tools": ["LangChain", "LangGraph", "Gemini API"], "mlops": ["MLflow"]}),
        "access_rules": json.dumps({"junior": {"jupyter_staging": "auto", "raw_user_data": "blocked"}}),
        "learning_sequence": json.dumps(["Arquitectura IA", "Pipeline datos", "MLflow experimentos"]),
        "ticket_criteria": json.dumps({"junior": "Replicar experimento con dataset diferente. Tiempo: 1-2 dias."}),
        "interview_questions": json.dumps({"stack_detection": "Has trabajado mas con fine-tuning, RAG o deployment?"}),
        "lobster_trap_policy_file": "ai_engineer.yaml",
        "system_prompt_template": "Eres el agente de onboarding para AI/ML Engineer.",
        "is_custom": False,
    },
]

SESSIONS = [
    {
        "id": SESSION_1,
        "agent_profile_id": AGENT_QA,
        "seniority": "mid",
        "dev_email": "ma***@demo.com",
        "dev_github_username": "maria-garcia-dev",
        "project_repo_url": "https://github.com/demo-org/demo-app",
        "status": "active",
        "payment_tx_hash": "demo_tx_maria_001",
        "interview_profile": json.dumps({"stack_actual": ["Playwright", "Python"], "nivel_real_detectado": "mid"}),
        "access_status": json.dumps({"github_repos": "granted", "jira_board": "granted", "production": "blocked"}),
        "onboarding_plan": json.dumps({"days": [{"day": 1, "title": "Setup del entorno de QA"}]}),
        "assigned_ticket_id": "DEMO-101",
        "checkin_day3_at": (now - timedelta(days=2)).isoformat(),
        "checkin_day7_at": None,
        "checkin_day14_at": None,
    },
    {
        "id": SESSION_2,
        "agent_profile_id": AGENT_BE,
        "seniority": "senior",
        "dev_email": "ca***@demo.com",
        "dev_github_username": "carlos-mendez-be",
        "project_repo_url": "https://github.com/demo-org/backend-services",
        "status": "interviewing",
        "payment_tx_hash": "demo_tx_carlos_002",
        "interview_profile": None,
        "access_status": json.dumps({}),
        "onboarding_plan": None,
        "assigned_ticket_id": None,
        "checkin_day3_at": None,
        "checkin_day7_at": None,
        "checkin_day14_at": None,
    },
    {
        "id": SESSION_3,
        "agent_profile_id": AGENT_DO,
        "seniority": "staff",
        "dev_email": "an***@demo.com",
        "dev_github_username": "ana-torres-sre",
        "project_repo_url": "https://github.com/demo-org/infra",
        "status": "completed",
        "payment_tx_hash": "demo_tx_ana_003",
        "interview_profile": json.dumps({"stack_actual": ["Terraform", "Kubernetes", "AWS"], "nivel_real_detectado": "staff"}),
        "access_status": json.dumps({"github_repos_infra": "granted", "aws_staging": "granted", "aws_prod": "blocked"}),
        "onboarding_plan": json.dumps({"days": [{"day": 1, "title": "Arquitectura cloud overview"}]}),
        "assigned_ticket_id": "DEMO-203",
        "checkin_day3_at": (now - timedelta(days=28)).isoformat(),
        "checkin_day7_at": (now - timedelta(days=24)).isoformat(),
        "checkin_day14_at": (now - timedelta(days=17)).isoformat(),
    },
]

AUDIT_EVENTS = [
    {
        "id": AUDIT_1,
        "session_id": SESSION_1,
        "event_type": "LOG",
        "severity": "LOW",
        "rule_triggered": "log_all_access_requests",
        "original_intent": "access_request",
        "action_taken": "Acceso a github_repos registrado",
        "resource_requested": "github_repos",
        "timestamp": (now - timedelta(days=5)).isoformat(),
    },
    {
        "id": AUDIT_2,
        "session_id": SESSION_1,
        "event_type": "REDACT",
        "severity": "MEDIUM",
        "rule_triggered": "redact_pii_in_prompts",
        "original_intent": "pii_detected",
        "action_taken": "Email redactado en el prompt antes de enviar a Gemini",
        "resource_requested": None,
        "timestamp": (now - timedelta(days=4)).isoformat(),
    },
    {
        "id": AUDIT_3,
        "session_id": SESSION_1,
        "event_type": "DENY",
        "severity": "HIGH",
        "rule_triggered": "block_prod_for_junior",
        "original_intent": "production_access",
        "action_taken": "Acceso a produccion bloqueado para nivel mid",
        "resource_requested": "production",
        "timestamp": (now - timedelta(days=3)).isoformat(),
    },
    {
        "id": AUDIT_4,
        "session_id": SESSION_3,
        "event_type": "HUMAN_REVIEW",
        "severity": "HIGH",
        "rule_triggered": "human_review_infra_write",
        "original_intent": "infrastructure_write",
        "action_taken": "Enviado a revision manual por senior-devops",
        "resource_requested": "aws_prod_write",
        "timestamp": (now - timedelta(days=20)).isoformat(),
    },
    {
        "id": AUDIT_5,
        "session_id": SESSION_3,
        "event_type": "LOG",
        "severity": "MEDIUM",
        "rule_triggered": "log_all_access_requests",
        "original_intent": "access_request",
        "action_taken": "Acceso a kubernetes_staging registrado",
        "resource_requested": "kubernetes_staging",
        "timestamp": (now - timedelta(days=25)).isoformat(),
    },
]


async def ensure_agents(conn):
    print("\n[1/3] Insertando agentes...")
    created = 0
    for a in AGENTS:
        existing = await conn.fetchval("SELECT id FROM agent_profiles WHERE id = $1", a["id"])
        if existing:
            print(f"  - {a['name']} ya existe")
            continue
        await conn.execute(
            """
            INSERT INTO agent_profiles (
                id, name, category, slug, icon, seniority_levels, stack_keywords,
                tools, access_rules, learning_sequence, ticket_criteria,
                interview_questions, lobster_trap_policy_file,
                system_prompt_template, is_custom
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
            ON CONFLICT DO NOTHING
            """,
            a["id"], a["name"], a["category"], a["slug"], a["icon"],
            a["seniority_levels"], a["stack_keywords"], a["tools"],
            a["access_rules"], a["learning_sequence"], a["ticket_criteria"],
            a["interview_questions"], a["lobster_trap_policy_file"],
            a["system_prompt_template"], a["is_custom"],
        )
        print(f"  + {a['name']}")
        created += 1
    print(f"  Agentes creados: {created}")


async def ensure_sessions(conn):
    print("\n[2/3] Insertando sesiones de demo...")
    created = 0
    for s in SESSIONS:
        existing = await conn.fetchval("SELECT id FROM onboarding_sessions WHERE id = $1", s["id"])
        if existing:
            print(f"  - Sesion {s['id']} ya existe")
            continue
        await conn.execute(
            """
            INSERT INTO onboarding_sessions (
                id, agent_profile_id, seniority, dev_email, dev_github_username,
                project_repo_url, status, payment_tx_hash, interview_profile,
                access_status, onboarding_plan, assigned_ticket_id,
                checkin_day3_at, checkin_day7_at, checkin_day14_at
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
            ON CONFLICT DO NOTHING
            """,
            s["id"], s["agent_profile_id"], s["seniority"], s["dev_email"],
            s["dev_github_username"], s["project_repo_url"], s["status"],
            s["payment_tx_hash"], s["interview_profile"], s["access_status"],
            s["onboarding_plan"], s["assigned_ticket_id"],
            datetime.fromisoformat(s["checkin_day3_at"]) if s["checkin_day3_at"] else None,
            datetime.fromisoformat(s["checkin_day7_at"]) if s["checkin_day7_at"] else None,
            datetime.fromisoformat(s["checkin_day14_at"]) if s["checkin_day14_at"] else None,
        )
        print(f"  + {s['dev_github_username']} ({s['status']})")
        created += 1
    print(f"  Sesiones creadas: {created}")


async def ensure_audit_events(conn):
    print("\n[3/3] Insertando eventos de auditoria...")
    created = 0
    for e in AUDIT_EVENTS:
        existing = await conn.fetchval("SELECT id FROM audit_events WHERE id = $1", e["id"])
        if existing:
            print(f"  - Evento {e['id']} ya existe")
            continue
        await conn.execute(
            """
            INSERT INTO audit_events (
                id, session_id, event_type, severity, rule_triggered,
                original_intent, action_taken, resource_requested, timestamp
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            ON CONFLICT DO NOTHING
            """,
            e["id"], e["session_id"], e["event_type"], e["severity"],
            e["rule_triggered"], e["original_intent"], e["action_taken"],
            e["resource_requested"],
            datetime.fromisoformat(e["timestamp"]),
        )
        print(f"  + [{e['severity']}] {e['event_type']} - {e['rule_triggered']}")
        created += 1
    print(f"  Eventos creados: {created}")


async def main():
    print("=" * 60)
    print("TechOnboard - Seed de datos de demo")
    print("=" * 60)
    print(f"Conectando a: {ASYNCPG_URL[:45]}...")

    try:
        conn = await asyncpg.connect(ASYNCPG_URL)
    except Exception as exc:
        print(f"\nERROR: No se pudo conectar.\n{exc}")
        sys.exit(1)

    try:
        await ensure_agents(conn)
        await ensure_sessions(conn)
        await ensure_audit_events(conn)
    finally:
        await conn.close()

    print("\n" + "=" * 60)
    print("Seed completado.")
    print("  6 agentes, 3 sesiones, 5 eventos de auditoria")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
