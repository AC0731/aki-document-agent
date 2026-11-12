# Aki Document Agent

I built this FastAPI service to ask questions about a PDF and see the passages behind the answer. It uses BM25 search to find text, then sends the matching sections to OpenAI. A calculator tool handles basic arithmetic.

This is the first version. It is in GitHub, but I have not deployed or tested it with a set of real documents yet. It needs an OpenAI API key and a separate API key for access. OpenAI usage may have a cost.

## Run it on your computer

You need Python 3.11 or newer.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:AGENT_API_KEY = "make-a-long-secret"
$env:OPENAI_API_KEY = "your-openai-api-key"
uvicorn main:app --reload
```

Then open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to use the API. Do not put either key in frontend code or commit it to GitHub.

## Connect it to another app

First upload a PDF. The response gives you a `document_id`.

```bash
curl -X POST "$AGENT_URL/v1/documents" \
  -H "Authorization: Bearer $AGENT_API_KEY" \
  -F "file=@handbook.pdf"
```

Then send a question using that ID:

```bash
curl -X POST "$AGENT_URL/v1/ask" \
  -H "Authorization: Bearer $AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"document_id":"DOCUMENT_ID","question":"What does the handbook say about leave?"}'
```

The answer response includes the source passages and page numbers. The repository also has a [JavaScript example](#javascript-example).

### JavaScript example

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

Keep `AGENT_API_KEY` on a server you control. Do not expose it in a browser app.

## Available endpoints

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/healthz` | Check whether the service is running |
| POST | `/v1/documents` | Upload a PDF |
| GET | `/v1/documents` | List uploaded PDFs |
| POST | `/v1/ask` | Ask about a PDF |
| DELETE | `/v1/documents/{document_id}` | Delete a PDF |

All endpoints except `/healthz` need the bearer API key. PDFs must contain selectable text and be under 20 MB and 200 pages. Scanned PDFs are not supported yet.

## Deploy it

The repository includes a Dockerfile. Set `AGENT_API_KEY` and `OPENAI_API_KEY` on your hosting provider and attach persistent storage at `/data`. The service uses SQLite, so a host without a persistent volume will lose uploaded documents when it replaces the container. Use HTTPS.

## Check answers

The [example evaluation file](evals/example.json) is a template. Upload a PDF, add questions and terms you expect to see in the answers, and run:

```bash
pip install requests
python evals/run_eval.py evals/my_cases.json
```

This only checks for selected words and whether sources were returned. It does not prove an answer is correct, so read the answers and source passages yourself. I have not reported evaluation results.

## What still needs work

- There is one shared API key and no individual user accounts.
- Documents are stored in one SQLite database. The service is intended for one small deployment, not multiple servers.
- BM25 can miss a relevant passage when the document uses different wording.
- There is no OCR for scanned PDFs.
