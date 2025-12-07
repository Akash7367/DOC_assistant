🚀 Intelligent Document Assistant

A smart, AI-powered enterprise document assistant built with Gemini API, LangChain, and Flask, designed to analyze contracts, policies, legal documents, and internal reports with ease.

This assistant can:

🔍 Extract clauses

⚠️ Identify risky terms

📑 Summarize documents

🤖 Answer questions using RAG

📤 Upload & ingest PDFs, DOCX, TXT

🧠 Maintain searchable history

🕸️ Provide LangSmith export

📈 Offer auto-escalation for high-risk clauses

✨ Features
🔹 1. Intelligent Q&A

Ask any question from uploaded files — the system retrieves the most relevant chunks and generates human-like answers using Google Gemini.

🔹 2. Document Upload & Ingestion

Supports:

PDF (with fallback to OCR for scanned files)

DOCX

TXT

Automatic chunking + embedding using SentenceTransformers.

🔹 3. Risk Analysis

Identifies:

Liability clauses

Indemnities

Termination conditions

Non-compete and confidentiality risks

High-risk results are auto-escalated.

🔹 4. Conversation History

Every query is preserved with:

Question

Answer

Context used

Sources

Risk score

History is searchable & replayable.

🔹 5. LangSmith Export

Export your entire dataset as JSON for evaluation, monitoring, or training.

🔹 6. Clean UI

Single-page interface with:

Ask panel

Upload & ingest integrated inside Ask

Scrollable results

Right-side History panel

🏗️ Tech Stack
Component	Technology
Backend	Python, Flask
LLM	Google Gemini (2.5 Flash / 1.5 Flash fallback)
Embeddings	SentenceTransformers MiniLM
Retrieval	Custom retriever + vector store
Frontend	HTML5, JavaScript, Marked.js (Markdown rendering)
Storage	SQLite (history), filesystem (uploads)
Dev Tools	LangChain, LangGraph, LangSmith
📂 Project Structure
DOC_assistant/
│── app.py
│── requirements.txt
│── README.md
│── .gitignore
│── templates/
│    └── index.html
│── static/
│    └── style.css
│── services/
│    ├── ingest.py
│    ├── llm_client.py
│    ├── retrieval.py
│    ├── risk.py
│    └── db.py
│── data/
│    ├── uploads/
│    └── history.db  (auto-created)
└── tests/

⚙️ Installation
1. Clone repo
git clone https://github.com/Akash7367/DOC_assistant.git
cd DOC_assistant

2. Create virtual env
python -m venv myenv
myenv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

4. Create .env file

(Do NOT commit this.)

GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash
SECRET_KEY=your_flask_secret_here


Optional OCR support for scanned PDFs:

pip install pillow pytesseract pdf2image
# plus install poppler & tesseract system binaries

▶️ Run the App
python app.py


Open in browser:

http://127.0.0.1:5000

🧠 How It Works (RAG Pipeline)

1️⃣ Upload Document
→ Extract text → Chunk → Embed → Store

2️⃣ Ask Question
→ Retriever selects best chunks → Sent to Gemini

3️⃣ LLM Generates
→ Answer
→ Markdown formatting
→ Risk report
→ Sources

4️⃣ History Saved
→ SQLite entry created
→ Can be replayed anytime

📊 Architecture Diagram (Add your PNG here later)
[User] → [Frontend] → [Flask Backend] → [Retriever] → [Embeddings DB]
                                          ↓
                                      [Gemini LLM]
                                          ↓
                                      [Final Answer]

📸 Screenshots (You can upload images in GitHub)

Add like:

![UI Screenshot](images/screenshot1.png)

🧪 Testing
pytest

📤 Export to LangSmith

Go to:

/export/langsmith


Downloads langsmith_export.json.

🛡️ .env Protection

Your repo already includes a strong .gitignore:

✔ .env excluded
✔ myenv/ excluded
✔ Sensitive files protected

🤝 Contributing

Pull requests are welcome!
For major changes, open an issue first.

📜 License

MIT License (or specify)

🎉 Done!

Your README is now professional, clean, and GitHub-ready.

If you want:

A logo for your project

Architecture diagram PNG

GIF demo

More badges (build passing, stars, issues, license)
Just tell me — I can generate all of them.