Okay, here is a consolidated English text describing your portfolio bot for a customer, integrating the technical details from your current README and the functional description we developed previously.

---

## 📄 Portfolio Bot Project Overview

This is an **asynchronous Telegram Portfolio Management Bot** built using the modern Python stack. It is designed to efficiently showcase projects, categorize them, and manage content submission from users, with clear administrative oversight. The core functionality is divided into secure **Admin** features for moderation and robust **Public** access for viewing and submitting projects.

### Core Functionality and Architecture

The bot leverages **Python 3.11+** and the **Aiogram 3.x** asynchronous framework, ensuring high performance and responsiveness. Database persistence is handled by **SQLAlchemy 2.0** (using its asynchronous Core and ORM features), with **SQLite** utilized for development (and scalable to **PostgreSQL** for production).

The logic is structurally clean, using **Aiogram Routers** to strictly separate public user interactions from administrative commands. Key elements of the architecture include **CallbackData** for "smart" inline buttons and dedicated **Middleware** for essential functions like restricting access to admin features.

### Content Management and FSM

A central feature is the structured content collection system. It uses the built-in **Aiogram FSM (Finite State Machine)** for reliable, step-by-step guidance when adding a project, whether by a public user or an administrator. This ensures all required data—Category, Title, Description, Link, Photo, and Document—is collected correctly before submission.

### Administrative Control

The administrator panel provides essential control tools: viewing core usage statistics, **moderating new project submissions** (Approve/Reject), and directly adding projects to the portfolio, bypassing the standard moderation queue.

### Deployment Summary

Configuration relies on `python-dotenv` for simple management of environment variables (`BOT_TOKEN`, `ADMIN_ID`). To deploy and start the bot: first activate the virtual environment (`.venv/Scripts/Activate.ps1` or `activate`), and then run `python main.py`.

---

Would you like to focus on polishing a specific section of this text, such as the technical stack or the admin features?