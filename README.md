# CareSync AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-AI%20Powered-4285F4.svg?logo=google)](https://deepmind.google/technologies/gemini/)
[![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E.svg?logo=supabase)](https://supabase.com/)

**CareSync AI** is an intelligent, compassionate healthcare management platform designed specifically for **Elderly Care & Medication Management**. Powered by **FastAPI**, **Google Gemini AI**, and **Supabase**, CareSync AI assists seniors and their caregivers in seamlessly managing prescription schedules, monitoring vital health signals, and providing personalized, AI-driven wellness companionship.

---

## 🌟 Key Features

- **Automated Medication Reminders & Tracking**: Proactive alerts and scheduled reminders to ensure timely adherence to prescribed medications.
- **Gemini-Powered Care Companion**: Natural-language conversational guidance for seniors to ask questions about symptoms, wellness tips, and daily routines.
- **Caregiver & Family Portal**: Real-time notifications and activity logs for caregivers and family members, providing peace of mind.
- **Adherence & Health Analytics**: Trend analysis tracking adherence rates, missed doses, and routine wellness check-ins.
- **Secure & Compliant Cloud Storage**: Powered by Supabase with Row Level Security (RLS) to ensure patient health data remains private and protected.

---

## 🏗️ Project Architecture

```
CareSync-AI/
├── backend/            # FastAPI REST backend and AI orchestration
├── frontend/           # Modern web/mobile caregiver and patient UI
├── .gitignore          # Repository hygiene and exclusion rules (<10MB target)
├── requirements.txt    # Core Python backend dependencies
└── README.md           # Project documentation
```

---

## 🚀 Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Async Python framework), [Uvicorn](https://www.uvicorn.org/) (ASGI server)
- **AI & Reasoning Engine**: [Google Gemini Pro / Gemini SDK](https://ai.google.dev/) (`google-generativeai`)
- **Database & Auth**: [Supabase](https://supabase.com/) (PostgreSQL & Auth)
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/)

---

## 🛠️ Getting Started

### Prerequisites

- Python 3.10+
- A [Google Gemini API Key](https://aistudio.google.com/)
- A [Supabase Project](https://supabase.com/) account and credentials

### 1. Clone & Setup Environment

```bash
git clone https://github.com/your-username/CareSync-AI.git
cd CareSync-AI

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory (do not commit this file):

```env
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Supabase Credentials
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_or_service_key
```

---

## 🔒 Security & Repository Hygiene

To keep the repository clean, lightweight, and strictly compliant with repository size limits (<10MB):
- Virtual environments (`venv/`, `env/`), bytecode caches (`__pycache__/`, `*.pyc`), and local environment variables (`.env`) are excluded via [.gitignore](file:///c:/Users/anonymous/.gemini/antigravity/scratch/CareSync-AI/.gitignore).
- Never commit large binaries, model weights, or dataset dumps to Git.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
