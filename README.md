# 🩺 AI Health Assistant

A conversational medical intake and analysis application built with **Streamlit** and powered by **GPT-4o** via the TCS GenAI Lab endpoint. Instead of filling out a static form, users interact with the app like a real doctor's assistant — answering health questions one at a time in a natural chat interface.

---

## 📌 Purpose

The app helps users get a preliminary AI-generated health assessment based on their personal details, symptoms, and optionally uploaded medical images. It does **not replace a doctor** but provides structured observations, possible conditions, risk levels, and actionable suggestions before a clinical consultation.

---

## ✨ Key Features

- 💬 **Conversational intake** — step-by-step chat flow (name → age → weight → blood group → gender → medical history → symptoms → images → doctor preference)
- ✅ **Field validation** — name, age, weight, and symptoms are mandatory with format checks
- 🖼️ **Medical image upload** with AI-powered relevance detection (rejects selfies, food, random photos)
- 🔬 **Vision-based image analysis** for X-rays, skin conditions, lab reports, prescriptions
- 🚫 **Irrelevant text detection** for symptoms and medical history fields
- 🧠 **Full health analysis** with possible conditions, risk level, observations, and suggestions
- ⭐ **Feedback collection** at the end of every session
- 🔄 **Session reset** for a fresh consultation

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend & UI | Streamlit |
| LLM (text) | GPT-4o via LangChain + TCS GenAI Lab |
| LLM (vision) | GPT-4o via OpenAI SDK + TCS GenAI Lab |
| HTTP Client | httpx (with SSL bypass for internal network) |
| Language | Python 3.9+ |

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
pip install streamlit langchain-openai openai httpx
```

### 2. Run the App

```bash
streamlit run health_assistant.py
```

### 3. Open in Browser

Streamlit will open the app automatically at:
```
http://localhost:8501
```

---

## 📁 Project Structure

```
ai-health-assistant/
│
├── health_assistant.py     # Main application file
└── README.md               # Project documentation
```

---

## ⚙️ How It Works

```
User opens app
      │
      ▼
Greeted by AI assistant
      │
      ▼
Step-by-step questions (name, age, weight, blood group, gender...)
      │
      ▼
Symptoms entered → validated for health relevance
      │
      ▼
Optional: Medical images uploaded → checked for relevance → analyzed by vision model
      │
      ▼
Full health analysis generated (conditions, risk level, suggestions)
      │
      ▼
User submits feedback → session can be reset
```

---

## 🔒 Security Notes

> ⚠️ Before sharing or deploying this app, make the following changes:

- **Move the API key** to `st.secrets` or a `.env` file:
  ```python
  # In health_assistant.py, replace hardcoded key with:
  api_key=st.secrets["api_key"]
  ```
- **Re-enable SSL verification** if deploying outside the TCS internal network:
  ```python
  http_client = httpx.Client(verify=True)
  ```

---

## 🖼️ Supported Image Types

| Accepted ✅ | Rejected ❌ |
|---|---|
| X-ray, MRI, CT scan | Selfies, portraits |
| Skin condition / rash / wound | Food, drinks |
| Lab reports, prescriptions | Animals, nature |
| Medical documents | Memes, screenshots |

Recommended: **up to 5 images per session** (GPT-4o supports max ~10, but 5 is optimal for token limits).

---

## ⚠️ Limitations & Disclaimers

- This app does **not** provide clinical diagnoses
- Image analysis is preliminary and **not** a substitute for a radiologist or specialist
- Designed for **internal / demo use** only
- Always consult a certified doctor for medical decisions

---

## 💡 Ideal Use Cases

- Internal healthcare demos and proof-of-concepts (POCs)
- Pre-consultation screening tools
- Health awareness and triage assistants
- Medical chatbot prototypes

---

## 👨‍💻 Built With

- [Streamlit](https://streamlit.io/)
- [LangChain](https://www.langchain.com/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [TCS GenAI Lab — GPT-4o endpoint](https://genailab.tcs.in)

---

*This project is intended for demo and internal use. Not for clinical or production medical use.*
