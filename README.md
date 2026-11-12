# Aki Document Agent

A reusable document question-answering API. Upload a text-based PDF, ask questions about it, and receive an answer grounded in retrieved passages with page references. The model can call a restricted calculator tool for arithmetic.

This is an initial implementation. It is not deployed yet and has not been independently tested. It requires an OpenAI API key, which is billed by OpenAI according to the selected model and account.

## What it does

- Extracts text from PDFs and stores document chunks in SQLite.
- Retrieves relevant passages with a local BM25 search.
- Answers through the OpenAI Chat Completions API and returns source excerpts and page numbers.
- Provides a calculator tool with an arithmetic-only expression evaluator.
- Protects document endpoints with a bearer API key.
- Includes a small evaluation runner for checking expected answer terms and source presence.
- Exposes OpenAPI docs at `/docs`.

Scanned PDFs need OCR, which is not included. SQLite is suitable for a small single-instance deployment; use a persistent volume at `/data`. For multiple users, add user-level authorization and isolate each user's documents before exposing the service publicly.

## Run locally

Use Python 3.11 or newer.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set the required values in your shell before starting the server:

```powershell
$env:AGENT_API_KEY = "your-long-random-secret"
$env:OPENAI_API_KEY = "your-openai-api-key"
uvicorn main:app --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). The API key and document content should stay private. Do not commit real keys or sensitive documents.

## Use it from another app

Set `AGENT_URL` to the deployed base URL and `AGENT_API_KEY` to the same secret configured on the service.

Upload a PDF:

```bash
curl -X POST "$AGENT_URL/v1/documents" \
  -H "Authorization: Bearer $AGENT_API_KEY" \
  -F "file=@handbook.pdf"
```

The response includes a `document_id`. Ask a question:

```bash
curl -X POST "$AGENT_URL/v1/ask" \
  -H "Authorization: Bearer $AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"document_id":"DOCUMENT_ID","question":"What is the leave request process?"}'
```

A JavaScript integration can use the same HTTP API:

```js
const response = await fetch(`${AGENT_URL}/v1/ask`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${AGENT_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ document_id, question }),
});
const result = await response.json();
console.log(result.answer, result.sources);
```

Keep the bearer key on your server. Do not put it in frontend code. For browser clients, call this API through your own authenticated backend.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/healthz` | Health check |
| POST | `/v1/documents` | Upload and index a PDF |
| GET | `/v1/documents` | List indexed PDFs |
| POST | `/v1/ask` | Ask a question about one PDF |
| DELETE | `/v1/documents/{document_id}` | Delete a PDF and its chunks |

Protected endpoints require `Authorization: Bearer <AGENT_API_KEY>`. Uploads are limited to 20 MB and 200 pages. PDFs must contain selectable text.

## Deploy with Docker

Build and run locally:

```bash
docker build -t aki-document-agent .
docker run --rm -p 8000:8000 \
  -e AGENT_API_KEY="$AGENT_API_KEY" \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -v agent-data:/data \
  aki-document-agent
```

On a hosting provider, set `AGENT_API_KEY`, `OPENAI_API_KEY`, and optionally `OPENAI_MODEL`, `CORS_ORIGINS`, and `DATA_DIR`. Attach persistent storage at `/data`; otherwise documents disappear when the container is replaced. Use HTTPS and a secret manager for production credentials.

## Check answer quality

Copy `evals/example.json`, upload a representative PDF, replace the placeholder ID and question, and add distinctive expected terms. Install the runner dependency with `pip install requests`, then run:

```bash
python evals/run_eval.py evals/my_cases.json
```

The runner checks whether expected terms appear and whether the API returned sources. It is a simple regression signal, not a semantic correctness score. Review every answer and source manually. Keep evaluation PDFs and any sensitive data private.

## Current limits

- One shared API key; there is no user accounts or per-user document isolation.
- SQLite and one service instance; no distributed vector store.
- BM25 lexical retrieval can miss passages that use different wording.
- No OCR for scanned documents.
- Retrieved text is treated as untrusted reference material, but this is not a substitute for reviewing outputs.
- No live deployment, usage monitoring, or evaluation results are claimed yet.
