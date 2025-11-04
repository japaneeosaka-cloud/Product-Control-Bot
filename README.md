## 📄 Portfolio Bot Project Overview

This is an **asynchronous Telegram Portfolio Management Bot** built using the modern Python stack. It is designed to efficiently showcase projects, categorize them, and manage content submission from users, with clear administrative oversight. The core functionality is divided into secure **Admin** features for moderation and robust **Public** access for viewing and submitting projects.

---

### Core Technology Stack

The project uses enterprise-grade asynchronous tools for high performance and scalability:

* **Runtime:** Python 3.11+
* **Bot Framework:** **Aiogram 3.x** (Asynchronous)
* **Database:** **PostgreSQL** (Production-ready)
* **ORM:** **SQLAlchemy 2.0** (Asynchronous Core & ORM)
* **State Management:** **Redis** (Used for Aiogram FSM storage)
* **Configuration:** **Pydantic-Settings** (Strictly validates environment variables from `.env`)

### Architecture and Structure

The logic is structurally clean, utilizing **Aiogram Routers** to strictly separate public user interactions from administrative commands. Key elements of the architecture include **CallbackData** for efficient inline buttons and dedicated **Middleware** for essential functions like access restriction and admin checks.

### Content Management and FSM

A central feature is the structured content collection system. It uses the built-in **Aiogram FSM (Finite State Machine)**, backed by **Redis**, for reliable, step-by-step guidance when adding a project. This ensures all required data—Category, Title, Description, Link, Photo, and Document—is collected correctly before submission or moderation.

### Administrative Control

The administrator panel provides essential control tools: viewing core usage statistics, **moderating new project submissions** (Approve/Reject), and directly adding projects to the portfolio, bypassing the standard moderation queue.

---

### 🐳 Deployment (Dockerized)

The project is configured for easy, one-command deployment using **Docker Compose**. This ensures that the application environment, database, and cache are all launched together and isolated from the host machine.

#### **Setup Steps:**

1.  Place your environment variables (BOT\_TOKEN, DB\_URL, etc.) in a file named **`.env`** in the root directory.
2.  Run the following command in the project root to build the images and launch all three services (Bot, PostgreSQL, Redis):

```bash
docker-compose up --build -d

3. Monitor the bot's logs:
docker-compose logs -f bot