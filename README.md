SGO: Sistema de Gestión de Operaciones
This is the README.md file for the SGO project.

<br>

Project Overview
This project is a full-stack web application designed to digitize and automate the operational management of a 32-person cleaning and hygiene team at a hospital. The system replaces a manual, paper-based workflow with a modern, cloud-native solution, allowing supervisors to manage daily staff scheduling, log incidents, and plan overtime from any device.

The core of the project is a robust backend API that communicates with a cloud database and a user-friendly frontend interface built for daily operational use. The final output of the system is the automated generation of official administrative forms, significantly reducing manual data entry and planning time.

<br>

Key Features
📋 Daily Incident Logging: Supervisors can log daily attendance for each worker across three shifts (Matutino, Vespertino, Nocturno) using a "roll call" style interface.

🔄 Substitution Planning: A dedicated dashboard allows for the planning and logging of worker-to-worker substitutions.

➕ Overtime Management: A comprehensive planning dashboard shows upcoming coverage needs and allows for the assignment and tracking of overtime. Includes a feature to delete assignments.

📍 Daily Service Assignment: An interface for assigning specific service areas to each worker on a daily, per-shift basis.

📄 Automated Reporting: A feature to generate and download clean, structured Excel reports for all major data types (incidents, substitutions, assignments, etc.) directly from the application.

🔐 Secure User Authentication: A simple but effective sign-in system restricts access to authorized supervisors.

🧠 Smart Scheduling Logic: The application contains complex, rule-based logic to accurately filter and display employee lists based on their unique schedules, including day shifts, "work-one, rest-one" night shifts, and special accumulated weekend shifts.

<br>

Tech Stack
Backend: Python with FastAPI

Frontend: Python with Streamlit

Database: PostgreSQL on Google Cloud SQL

Deployment: Docker, Google Cloud Run, Google Artifact Registry

Core Python Libraries: pandas, SQLAlchemy, requests, openpyxl, python-dotenv


<br>

What I Learned
This project served as a practical application of junior data science and cloud engineering skills, covering the entire lifecycle of a full-stack application. Key skills developed include:

Cloud Infrastructure: Provisioning and managing cloud resources (Cloud SQL, Cloud Run) using the gcloud CLI.

Backend Development: Building a robust, data-driven REST API with FastAPI and SQLAlchemy.

Database Design: Modeling a relational database schema to fit complex business requirements.

Containerization: Using Docker to create reproducible environments for both the backend and frontend, and managing images with Artifact Registry.

Frontend Development: Creating a functional and interactive user interface for data entry and visualization with Streamlit.

Automation: Writing Python scripts with pandas and openpyxl to automate the generation of official administrative reports.

Debugging: Systematically diagnosing and fixing a wide range of issues, from local environment problems to complex cloud deployment errors and business logic flaws.
