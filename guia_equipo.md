# 🚀 Guía de trabajo en equipo – Proyecto Market

Este documento explica cómo vamos a trabajar en el repositorio utilizando **ramas organizadas** y **Pull Requests**, para mantener un flujo limpio.

---

## 🧭 Estructura de ramas

| Rama                | Responsable           | Descripción                                                                                                                                                   |
| ------------------- | --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **main**      | (líder del proyecto) | Rama**estable**, contiene el código listo para producción. Nadie más debe hacer commits directos aquí.                                               |
| **develop**   | Todo el equipo        | Rama de**desarrollo** principal. Es la base desde donde se crean las demás ramas y donde se integran las nuevas funciones antes de pasarlas a `main`. |
| **feature/*** | Cada desarrollador    | Ramas temporales para **nuevas funcionalidades**, **correcciones** o **mejoras específicas**.                                              |

---

## 🧩 Flujo de trabajo (paso a paso)

### 1. Antes de empezar una nueva tarea

Actualizá tu entorno local con la versión más reciente del código:

```bash
git checkout develop
git pull origin develop
```

### 2. Crear tu rama de trabajo

Cada tarea (issue, ticket de Jira, o mejora) debe hacerse en una rama nueva, creada desde `develop`.

"feature/nombre-descriptivo"

```bash
git checkout -b feature/login-usuarios
git checkout -b feature/pagina-productos
```

### 3. Trabajar y hacer commits

```bash
git add .
git commit -m "Agrega login de usuarios con autenticación básica"
```

### 4. Subir tu rama al repositorio remoto

```bash
git push origin feature/login-usuarios
```

### 5. Crear un Pull Request (PR)

Desde GitHub:

1. Entrá al repositorio.
2. Hacé clic en  **“Compare & pull request”** .
3. Asegurate que la base sea `develop` y tu comparación (`compare`) sea tu rama `feature/...`.
4. Escribí una descripción del cambio y mencioná qué parte del proyecto afecta.
   ⚠️ No merges directamente. Esperá que el líder revise y apruebe el PR.

### 6. Correciones y aprobacion

```bash
git checkout feature/login-usuarios
# aplicá los cambios pedidos
git add .
git commit -m "Corrige validación del formulario de login"
git push origin feature/login-usuarios
```
