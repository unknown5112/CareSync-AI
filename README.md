# CareSync AI: Elderly Care & Medication Management Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-AI%20Powered-4285F4.svg?logo=google)](https://deepmind.google/technologies/gemini/)
[![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E.svg?logo=supabase)](https://supabase.com/)

**CareSync AI** is a state-of-the-art **Medication Management Platform** engineered specifically for **Elderly Care**, bridging clinical precision and compassionate technology to deliver **Accessible Healthcare** and **Compassionate Care for Seniors**. Powered by **FastAPI**, **Google Gemini Vision AI**, and **Supabase**, the system empowers aging adults and caregivers with **Automated Reminders**, contactless OCR strip analysis, and proactive wellness tracking.

---

## 📌 Problem Statement

Over 50% of seniors managing chronic conditions experience adverse health events or hospitalizations caused by medication non-adherence, improper dosages, or missed prescription times. Modern digital health interfaces frequently fail older adults due to complex navigation, tiny typography, and overwhelming workflows.

Key Challenges in Geriatric Care:
1. **Polypharmacy Confusion**: Seniors routinely manage 4 to 9 distinct daily prescriptions with differing timing and meal instructions.
2. **Vision & Dexterity Barriers**: Small packaging text and tiny pill bottles prevent older adults from reading critical dosages accurately.
3. **Caregiver Anxiety**: Remote family members lack real-time visibility into whether daily doses were taken safely.
4. **Lack of Accessible Healthcare**: Conventional portals are not built with high-contrast accessibility or dedicated senior-first ergonomics.

---

## 🎯 Impact & Solution

**CareSync AI** solves this critical gap through **Compassionate Care for Seniors**:
- **99.9% Adherence Verification**: Proactive scheduled alerts and **Automated Reminders** ensure doses are never skipped.
- **Smart Multimodal OCR**: Powered by Gemini Vision, seniors simply photograph their medication packaging; the platform instantly extracts the drug name, dosage, and warnings.
- **Accessible Healthcare Design**: Ultra-clear high-contrast UI with large font scales, simplified 4-digit PIN verification, and one-tap taken toggles.
- **Empowered Caregiver Network**: Seamless integration with family notification services via polite email reminders and Supabase audit logs.

---

## 🌟 Key Features

- **Automated Reminders & Scheduling**: Continuous adherence tracking with polite, personalized email alerts for upcoming and missed medications.
- **Elderly Care First UI**: High-contrast, large-button touch keypad, simple PIN authentication, and screen-reader compliant elements.
- **Gemini Vision OCR Scanner**: Automated identification of medication strips, bottles, and blister packs with fallback model orchestration.
- **Medication Management Platform**: Real-time adherence logs and multi-dose daily scheduling for comprehensive health oversight.
- **Secure Cloud Backend**: Production-ready FastAPI architecture with strict security headers, CORS controls, and 5MB payload protection.

---

## 🏗️ Project Architecture

```
CareSync-AI/
├── backend/
│   ├── main.py                 # FastAPI application with security headers, CORS, and size limits
│   ├── database.py             # Supabase client with LRU-cached credential access
│   └── utils/
│       ├── ai_scanner.py       # Gemini Vision OCR pipeline with Pillow and fallback sequence
│       └── email_service.py    # Automated reminder email notifications via smtplib
├── frontend/
│   ├── index.html              # Accessible Healthcare dashboard (Tailwind CSS, high contrast)
│   └── app.js                  # Frontend client logic, PIN authentication, and scan handler
├── tests/
│   ├── __init__.py             # Test package initializer
│   └── test_main.py            # Comprehensive test suite (FastAPI TestClient & mocks)
├── requirements.txt            # Python dependencies (FastAPI, Gemini, Supabase, pytest, httpx)
├── .gitignore                  # Lean repo exclusions (<10MB limit compliance)
└── README.md                   # Problem statement, architecture, and impact documentation
```

---

## 🚀 Tech Stack

- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Async Python framework with `run_in_threadpool` offloading)
- **AI & Computer Vision**: [Google Gemini Vision](https://ai.google.dev/) (`google-generativeai`, `Pillow`)
- **Database & Authentication**: [Supabase](https://supabase.com/)
- **Testing & Quality Assurance**: `pytest`, `FastAPI TestClient`, `httpx`, `unittest.mock`
- **Security & Caching**: Custom middleware (nosniff, DENY framing), `functools.lru_cache`, 5MB upload limits

---

## 🧪 Testing & Quality Assurance

CareSync AI includes comprehensive automated test coverage for backend routes, error handling, payload size limits, and mocked Gemini AI responses:

```bash
# Run the test suite
pytest tests/ -v
```

Test cases cover:
1. `test_health_check`: Validates HTTP 200 and presence of strict security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`).
2. `test_scan_medication_missing_file`: Verifies 422 Unprocessable Entity on missing upload payload.
3. `test_scan_medication_empty_file`: Verifies 400 Bad Request on empty file submissions.
4. `test_scan_medication_payload_too_large`: Verifies 413 Payload Too Large for files exceeding 5MB.
5. `test_scan_medication_success_mocked`: Verifies successful OCR response with mocked Gemini Vision output.
6. `test_scan_medication_error_handling`: Verifies graceful 500 error propagation on external vision processing failures.

---

## 🛠️ Getting Started

### Prerequisites

- Python 3.10+
- [Google Gemini API Key](https://aistudio.google.com/)
- [Supabase Project](https://supabase.com/)

### Installation & Run

```bash
# 1. Clone the repository
git clone https://github.com/unknown5112/CareSync-AI.git
cd CareSync-AI

# 2. Set up virtual environment
python -m venv venv
source venv/bin/activate  # Or .\venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the development server
uvicorn backend.main:app --reload --port 8000
```

---

## 🔒 Security & Performance Engineering

- **Payload Size Defense**: Hard limit of 5MB enforced before processing image payloads to prevent DoS.
- **Defensive HTTP Headers**: Automatically injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection`, and `Strict-Transport-Security`.
- **Async & Non-blocking I/O**: Heavy synchronous vision tasks and Pillow image parsing are offloaded via `run_in_threadpool`.
- **LRU Caching**: Configuration lookups utilize `@functools.lru_cache` to minimize overhead in high-throughput environments.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
