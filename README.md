# 🐛 AI Auto Bug Tester

An intelligent, end-to-end bug reproduction assistant that reads bug reports and automatically executes UI test steps using Playwright—enhanced with AI-driven fallback selectors and DOM understanding.

---

## 🚀 Features

- ✅ Natural language bug report parsing via **Phi-3 mini instruct (LLM)**
- ✅ Converts bug descriptions into structured JSON test steps
- ✅ Executes steps with **Playwright**
- ✅ Uses AI fallback for dynamic DOM-based selector recovery
- ✅ Streamlit UI for easy interaction
- ✅ Generates detailed markdown reports with screenshots
- ✅ Browser runs in headed mode for live inspection

---

## 🧠 Powered by AI

- Uses **Phi-3 Mini (Locally running via LM Studio)** for:
  - Parsing bug descriptions
  - Suggesting fallback selectors dynamically by analyzing live DOM
  - Recovering from broken test steps

---

## 🔧 Tech Stack

| Layer            | Technology                     |
|------------------|---------------------------------|
| UI               | Streamlit                      |
| Backend          | FastAPI                        |
| Test Execution   | Playwright (Python)            |
| AI Integration   | Phi-3 via LM Studio (GGUF LLM) |
| Markdown + Screenshot | Python Imaging, Base64     |

---

## 🗂️ Project Structure

```
ai-auto-bug-tester/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── executor.py          # Core test executor with Playwright
│   ├── gpt_parser.py        # LLM integration & bug parsing
│   └── outputs/             # Screenshots + Reports
├── frontend/
│   └── app.py               # Streamlit interface
```

---

## ⚙️ Setup Instructions

1. Clone the repository  
   `git clone https://github.com/guptasoumya26/ai-auto-bug-tester.git`

2. Install dependencies  
   `pip install -r requirements.txt`

3. Install Playwright browsers  
   `playwright install`

4. Run LM Studio locally (phi-3-mini with instruct GGUF)

5. Launch backend  
   `cd backend && uvicorn main:app --reload --port 8000`

6. Launch frontend  
   `cd frontend && streamlit run app.py`

---

## 📤 Output

After running, the following is generated:
- Markdown bug reproduction report
- Step-wise screenshots
- Stored inside `backend/outputs/`

---

## 📌 Example Use Case

> Feed this:
>
> “Steps to Reproduce: Open login page, type wrong password, click login. Expect error message 'Invalid credentials'. No message shown.”
>
> 🧠 AI will:
> - Convert into JSON steps
> - Execute UI actions
> - Capture errors + screenshots
> - Generate a detailed report

---

## 🤝 Contribute

Want to add GitHub issue parsing? LLM selector scoring? Multi-browser support?

Open a PR or connect on LinkedIn!
