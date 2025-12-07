# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from services.ingest import ingest_file
from services.retrieval import Retriever
from services.llm_client import GeminiClient
from services.risk import evaluate_risk
from services import db as dbsvc
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'data', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize DB
dbsvc.init_db()

# Initialize components
retriever = Retriever()  # builds/loads FAISS/Chroma index
llm = GeminiClient(api_key=os.environ.get('GEMINI_API_KEY'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file:
        return jsonify({'ok': False, 'message': 'No file provided'}), 400

    save_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    try:
        file.save(save_path)
    except Exception as e:
        return jsonify({'ok': False, 'message': f'Failed to save file: {e}'}), 500

    try:
        ingest_file(save_path, retriever)
    except Exception as e:
        return jsonify({'ok': False, 'message': f'Ingest failed: {e}'}), 500

    return jsonify({'ok': True, 'message': f'Uploaded and ingested {file.filename}'}), 200

@app.route('/query', methods=['POST'])
def query():
    data = request.json or {}
    q = data.get('query') or ''
    if not q:
        return jsonify({'error': 'missing query'}), 400

    hits = retriever.similarity_search(q, k=4)
    context_text = "\n\n".join([h.page_content for h in hits])

    # Build prompt (markdown request as you had)
    prompt = (
        "You are a concise document assistant. Use the CONTEXT to answer the question. "
        "Produce the final answer in MARKDOWN format only (no commentary). "
        "Use headings, short paragraphs, and bullet points. "
        "Include source references like `(source: filename.pdf)` where relevant.\n\n"
        "CONTEXT:\n"
        f"{context_text}\n\n"
        f"QUESTION: {q}\n\n"
        "Output only Markdown."
    )

    response_text = llm.complete(prompt)
    risk_report = evaluate_risk(context_text)
    escalated = risk_report.get('overall_score', 0) >= 0.7

    # Save to history DB
    try:
        model_name = getattr(llm, "_chosen_generate_model", None) or os.environ.get("GEMINI_MODEL") or ""
        item_id = dbsvc.save_interaction(
            question=q,
            answer=response_text,
            context=context_text,
            risk=risk_report,
            escalated=escalated,
            source_count=len(hits),
            model_used=model_name
        )
    except Exception as e:
        # don't fail the request if DB save fails; just log (return in JSON)
        item_id = None

    return jsonify({
        'answer': response_text,
        'risk': risk_report,
        'escalated': escalated,
        'source_count': len(hits),
        'history_id': item_id
    })

# History endpoints
@app.route('/history', methods=['GET'])
def history_list():
    limit = int(request.args.get('limit', 200))
    rows = dbsvc.list_history(limit=limit)
    return jsonify(rows)

@app.route('/history/<int:item_id>', methods=['GET'])
def history_get(item_id):
    row = dbsvc.get_history_item(item_id)
    if not row:
        return jsonify({'error': 'not found'}), 404
    return jsonify(row)

@app.route('/export/langsmith', methods=['GET'])
def export_langsmith():
    rows = dbsvc.export_all_for_langsmith()
    # return as JSON array
    return jsonify(rows)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
