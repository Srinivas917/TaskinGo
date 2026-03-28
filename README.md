<div align="center">

<h1>🎯 TaskinGo</h1>

<p><strong>AI-powered goal tracking. set your goals, build your path, and let intelligent agents guide you to success.</strong></p>

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-FF6B6B?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com)
[![MSSQL](https://img.shields.io/badge/MSSQL-CC2927?style=for-the-badge&logo=microsoftsqlserver&logoColor=white)](https://www.microsoft.com/en-us/sql-server)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)

</div>

---

## 🌟 What is TaskinGo?

**TaskinGo** is a smart, AI-driven goal management platform that helps you define what you want to achieve, break it down into actionable tasks, track your progress, and gain deep insights into how effectively you're working toward your goals.

Whether you're building a new habit, completing a personal project, or working toward a long-term objective - TaskinGo gives you the structure, intelligence, and clarity to get there.

---

## ✨ Key Features

### 🎯 Goal Creation with Email Confirmation
Create a goal in seconds. Once submitted, you'll receive a **confirmation email** instantly - a simple but meaningful signal that your commitment is locked in.

### 🤖 AI-Suggested Tasks
Not sure where to start? Let the AI suggest a list of tasks tailored to your goal. Review the suggestions and **add the ones that resonate** directly to your task list - no copy-pasting needed.

### ✅ Task Management & Progress Tracking
- Add your own custom tasks or use AI suggestions
- Mark tasks as **complete** or **incomplete** with a single click
- A **live progress bar** updates in real time, giving you a visual sense of how close you are to achieving your goal

### 🧠 AI Insights *(Powered by LangGraph)*
The crown jewel of TaskinGo. A **multi-agent AI pipeline** built with LangGraph analyzes your goal and task activity to deliver:

| Insight | Description |
|---|---|
| 🚫 Irrelevant Task Detection | Identifies tasks you're doing that don't actually contribute to your goal |
| 📊 Goal Progress Analytics | Tells you how close you are to achieving your goal, with honest analysis |
| 💡 Smart Task Suggestions | Recommends additional tasks that could help you reach your goal faster |

Each agent in the pipeline has a dedicated role - together, they provide a holistic, intelligent review of your goal journey.

### 📝 Goal-Specific Notes
Capture thoughts, ideas, and reminders **within the context of each goal**. Notes are scoped per goal, so your thinking stays organized and you never lose a key insight.

---

## 🔄 How It Works

```
1. Create a Goal
        │
        ▼
2. Receive Email Confirmation
        │
        ▼
3. Add Tasks (manually or via AI suggestions)
        │
        ▼
4. Track Progress (mark complete/incomplete → progress bar updates)
        │
        ▼
5. Request AI Insights (LangGraph agents analyze your goal)
        │
        ├── Detects irrelevant tasks
        ├── Analyzes goal completion percentage
        └── Suggests missing tasks to reach your goal faster
```

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | FastAPI (Python) |
| **AI Orchestration** | LangGraph (multi-agent pipeline) |
| **Relational Database** | Microsoft SQL Server (MSSQL) |
| **Document Store** | MongoDB |
| **Frontend** | Streamlit |
| **Email Service** | SMTP / Mail integration |
| **AI/LLM** | LangChain-compatible LLMs |

---

## 🖥️ Frontend — Streamlit UI

TaskinGo ships with a **user-friendly Streamlit interface** so you don't need to interact with raw API endpoints. Everything is accessible through a clean, interactive web app right in your browser.

Through the Streamlit UI you can:

- 🎯 Create and manage your goals from a simple form
- ✅ Add, complete, and uncheck tasks with one click
- 📊 Watch your **progress bar** update live as you work through tasks
- 🤖 Request AI task suggestions and add them instantly to your list
- 🧠 Trigger **AI Insights** and read the agent-generated analysis in a readable format
- 📝 Write and review your **goal-specific notes** without leaving the page

### Running the Frontend

Make sure the FastAPI backend is already running, then launch the Streamlit app:

```bash
streamlit run app.py
```

The UI will open automatically at `http://localhost:8501`

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Microsoft SQL Server
- MongoDB
- An GROQ API key

### Installation

```bash
# Clone the repository
git clone https://github.com/Srinivas917/TaskinGo.git
cd TaskinGo
git checkout dev

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the root directory:

```env
# Database
MSSQL_CONNECTION_STRING=your_mssql_connection_string
MONGODB_URI=your_mongodb_uri

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASSWORD=your_password

# AI
GROQ_API_KEY=your_groq_api_key
```

### Run the Application

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:9000`  
Interactive API docs at `http://localhost:9000/docs`

---

## 📖 Use Cases

- 🏋️ **Fitness Goals** — Create a "Run a 5K" goal, get AI-suggested training tasks, track workouts, and get insights on whether your current routine is aligned with your target
- 📚 **Learning Goals** — Set a "Learn Python in 30 days" goal, get a structured learning path, and find out if any tasks are off-track
- 💼 **Work Projects** — Break down complex deliverables into tasks, monitor completion, and use notes to capture meeting points or blockers
- 🧘 **Personal Development** — Build habits, reflect through notes, and let AI tell you what's working and what isn't

---

<div align="center">

Built by [Srinivas917](https://github.com/Srinivas917)

*Stop wishing. Start tracking. Let AI do the thinking.*

</div>

