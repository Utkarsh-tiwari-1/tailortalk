# 🧵 TailorTalk: AI Booking Assistant

![TailorTalk Logo](https://cdn-icons-png.flaticon.com/512/4712/4712035.png)

## 🚀 Overview
TailorTalk is a conversational AI agent that helps you book and manage appointments on your Google Calendar—just by chatting! Powered by FastAPI, LangChain, and a beautiful Streamlit frontend, TailorTalk understands your intent, checks your calendar, suggests time slots, and confirms bookings—all seamlessly through chat.

---

## ✨ Features
- **Conversational Booking:** Natural language chat to book, view, and manage meetings.
- **Google Calendar Integration:** Real-time availability, booking, and upcoming events.
- **Modern Chat UI:** Responsive, glassmorphic design with avatars, dark/light mode, and PWA support.
- **Multi-Model LLM:** Uses OpenRouter (GPT-4o, Gemini, Claude, etc.) for robust language understanding.
- **Error Handling & Fallbacks:** Smart model fallback and typo-tolerant intent detection.
- **Installable PWA:** Add to your desktop or mobile for an app-like experience.

---

## 🛠️ Tech Stack
- **Backend:** FastAPI (Python)
- **Agent Framework:** LangChain
- **Frontend:** Streamlit (with custom CSS)
- **LLM:** OpenRouter API (GPT-4o, Gemini, Claude, etc.)
- **Calendar:** Google Calendar API (Service Account)

---

## ⚡ Quick Start

### 1. Clone the Repo
```bash
git clone https://github.com/yourusername/tailortalk.git
cd tailortalk
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Create a `.env` file in the backend directory:
```
OPENROUTER_API_KEY=sk-or-...
GOOGLE_APPLICATION_CREDENTIALS=backend/service_account.json
```

### 4. Google Calendar Setup
- Create a Google Cloud project and service account.
- Enable Google Calendar API and download the JSON key as `service_account.json`.
- Share your Google Calendar with the service account email.

### 5. Run the Backend
```bash
uvicorn backend.main:app --reload
```

### 6. Run the Frontend
```bash
streamlit run frontend.py
```

- Visit [http://localhost:8501](http://localhost:8501) to chat with TailorTalk!

---

## 🌐 Deployment
- Deploy backend and frontend to [Railway](https://railway.app), [Render](https://render.com), or [Streamlit Cloud](https://streamlit.io/cloud).
- Set environment variables and upload your `manifest.json` for PWA support.
- Update backend URL in frontend if deploying separately.

---

## 📸 Screenshots
| Chat UI (Dark Mode) | Sidebar & PWA |
|--------------------|--------------|
| ![Chat UI](https://i.imgur.com/2Qw7QwB.png) | ![Sidebar](https://i.imgur.com/8Qw7QwB.png) |

---

## 🤝 Credits
- **Built by:** [Utkarsh Tiwari](https://github.com/utkarsh)
- **Inspired by:** OpenAI, Google, Streamlit, LangChain

---

## 📝 License
MIT License. See [LICENSE](LICENSE) for details.

---

**TailorTalk — Your AI-powered calendar assistant!**
