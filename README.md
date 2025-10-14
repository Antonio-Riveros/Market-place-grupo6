# Market-place-grupo6

![Django](https://img.shields.io/badge/Django-5.2.7-green)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![Database](https://img.shields.io/badge/Database-SQLite3-orange)

## 📌 Descripción

**Market-place-grupo6** es un proyecto grupal desarrollado en el marco académico, que consiste en un marketplace donde los usuarios pueden registrarse, iniciar sesión, gestionar productos y realizar compras. El proyecto incorpora funcionalidades avanzadas como un sistema de chat interno y recomendaciones mediante inteligencia artificial.

---

## 👥 Integrantes

- [Antonio Riveros](https://github.com/Antonio-Riveros) (Líder de proyecto, configuración de MySQL para desarrollo)
- [Tania Magalí Zarza](https://github.com/MaguiZarza) (Desarrolladora Front-End)
- [Agustín Silva](https://github.com/agussilva88) (Desarrollador Back-End)

---

## ⚙️ Tecnologías utilizadas

- **Backend:** Django 5.2.7, Python 3.10
- **Base de datos:** SQLite3 (grupo) / MySQL (desarrollo avanzado)
- **Autenticación:** Django Allauth (registro e inicio de sesión, social login Google/GitHub)
- **Frontend:** HTML, CSS
- **Funcionalidades adicionales:** Chat interno (`simple_chat`), recomendaciones de productos mediante AI (`market_ai`)
- **Gestión de proyecto:** Jira, Discord

---

## 💡 Funcionalidades principales

- Registro e inicio de sesión de usuarios (Django Allauth)
- Login social con Google y GitHub
- Gestión de productos: crear, listar, editar y eliminar
- Carrito de compras con seguimiento de productos
- Chat interno entre usuarios (`simple_chat`)
- Sistema de recomendaciones con IA (`market_ai`)

---

## 🛠️ Instalación y configuración

1. Clonar el repositorio:

```bash
git clone https://github.com/Antonio-Riveros/Market-place-grupo6.git
cd Market-place-grupo6
```


2. Crear un entorno virtual e instalar dependencias

```bash
python -m venv venv
source venv/bin/activate  # Linux / Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt

```

3. Configurar variables sensibles en un archivo `.env` en la raíz del proyecto:

```bash
SECRET_KEY=tu_clave_secreta
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_NAME=db_name
DATABASE_USER=db_user
DATABASE_PASSWORD=db_password
DATABASE_HOST=localhost
DATABASE_PORT=3306
GOOGLE_CLIENT_ID=tu_google_client_id
GOOGLE_CLIENT_SECRET=tu_google_client_secret
GITHUB_CLIENT_ID=tu_github_client_id
GITHUB_CLIENT_SECRET=tu_github_client_secret
MERCADOPAGO_ACCESS_TOKEN=tu_token

```

4. Ejecutar migraciones:

```bash
python manage.py makemigrations
python manage.py migrate
```

5. Crear un superusuario:

```bash
python manage.py createsuperuser
```

6. Correr el servidor:

```bash
python manage.py runserver
```

7. Acceder al proyecto desde el navegador:

```bash
http://127.0.0.1:8000/
```
