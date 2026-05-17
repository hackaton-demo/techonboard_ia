---
company_name: SwagLabs
app_name: Sauce Demo
app_url: https://www.saucedemo.com
app_description: >
  Tienda e-commerce demo de artículos tech (camisetas, mochilas, onesies).
  Tiene 5 pantallas clave: login, inventario de productos, detalle de ítem,
  carrito y flujo de checkout completo. Es la app principal que el equipo
  mantiene y sobre la cual se escriben todos los tests E2E.

team_stack: TypeScript, Playwright, React, Node.js, GitHub Actions

tools:
  testing: [Playwright, TypeScript]
  ci_cd: [GitHub Actions]
  project_management: [Jira]
  version_control: [GitHub]
  browsers: [Chromium, Firefox, WebKit]

repo_url: https://github.com/saucelabs/sauce-demo
jira_project: SWAG
default_branch: main

learning_sequence:
  - "Entender la app: flujos críticos de login, agregar al carrito y checkout completo"
  - "Clonar el repo, instalar dependencias con npm install, y correr npx playwright test"
  - "Entender la estructura de carpetas: tests/, fixtures/, pages/ (Page Object Model)"
  - "Correr un test en modo headed para ver qué hace: npx playwright test --headed"
  - "Leer el reporte HTML generado por Playwright y cómo se ve en GitHub Actions"
  - "Cómo crear un ticket en Jira cuando encontrás un bug: severity, steps to reproduce, evidencia"
  - "Proceso de PR: nombre de branch, descripción, qué revisa el equipo antes de mergear"

first_ticket:
  junior: >
    Escribir un test Playwright en TypeScript para el happy path del checkout completo:
    login → agregar ítem al carrito → ir al carrito → completar checkout con datos válidos
    → verificar pantalla de confirmación. Usar el Page Object Model ya existente en el repo.
    Tiempo estimado: 4-6 horas.
  mid: >
    Escribir tests para los edge cases del login: usuario bloqueado (locked_out_user),
    credenciales inválidas, y campo vacío. Incluir assertions de los mensajes de error.
    Agregar un custom fixture de Playwright para reutilizar la lógica de login.
    Tiempo estimado: 6-10 horas.
  senior: >
    Diseñar e implementar una estrategia de datos de prueba para los tests de checkout:
    parametrizar los tests con diferentes combinaciones de productos y métodos de envío.
    Proponer y documentar la convención para fixtures compartidos del equipo.
    Tiempo estimado: 1-2 días.

access_rules:
  junior:
    github_repo_saucedemo: auto
    jira_project_swag: auto
    github_actions_view: auto
    staging_env: auto
    github_actions_trigger: requires_approval
    production: blocked
  mid:
    github_repo_saucedemo: auto
    jira_project_swag: auto
    github_actions_view: auto
    github_actions_trigger: auto
    staging_env: auto
    branch_protection_bypass: requires_approval
    production: blocked
  senior:
    github_repo_saucedemo: auto
    jira_project_swag: auto
    github_actions: auto
    staging_env: auto
    branch_protection_bypass: auto
    production: requires_approval
    repo_settings: requires_approval
---

# SwagLabs — Configuración de Onboarding

## Sobre la app

Sauce Demo es una tienda e-commerce de artículos tech construida en React. Es la aplicación
principal que mantiene el equipo de QA/Frontend. Todos los nuevos devs hacen su primer
contribución escribiendo o mejorando tests Playwright para esta app.

## Stack del equipo

- **Tests E2E:** Playwright + TypeScript
- **Frontend:** React + Node.js
- **CI/CD:** GitHub Actions (se ejecuta en cada PR y merge a main)
- **Gestión de proyecto:** Jira (proyecto SWAG)
- **Control de versiones:** GitHub

## Flujos críticos que nunca deben romperse

1. **Login** — con `standard_user` / `secret_sauce`
2. **Agregar al carrito** — desde inventario y desde detalle de ítem
3. **Checkout completo** — carrito → información de envío → resumen → confirmación
4. **Logout** — desde el menú lateral

## Usuarios de prueba disponibles en la app

| Usuario | Contraseña | Comportamiento |
|---|---|---|
| standard_user | secret_sauce | Flujo normal |
| locked_out_user | secret_sauce | Login bloqueado |
| problem_user | secret_sauce | Imágenes rotas |
| performance_glitch_user | secret_sauce | Carga lenta |

## Convenciones del equipo

- Tests van en `tests/` organizados por feature
- Cada página tiene su Page Object en `pages/`
- Los datos de prueba van en `fixtures/`
- Nombre de branch: `feat/SWAG-123-descripcion` o `fix/SWAG-456-descripcion`
- El pipeline de GitHub Actions corre en Chromium, Firefox y WebKit
