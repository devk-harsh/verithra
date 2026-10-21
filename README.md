# Verithra

A technical support assistant that searches local manuals and resolved cases, then returns a
likely cause, suggested steps and the passages used to support them. Built with Python,
Streamlit, OpenAI and FAISS.

## Run locally

Python 3.12 or newer is required. In PowerShell:

```powershell
git clone https://github.com/devk-harsh/verithra.git
cd verithra
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps .
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501. On macOS or Linux, use `.venv/bin/python` instead.

The app starts in offline mode. This uses keyword-based vectors and copies matching passages;
it does not call an LLM.

## Use OpenAI

Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY`. Restart the app if it is already
running. Select **OpenAI**, then click **Build / refresh index** before submitting an issue.
Both indexing and answers use the API and incur usage charges.

You can also build the index from the command line:

```powershell
.\.venv\Scripts\python.exe -m verithra.cli build-index
```

Model names and retrieval settings are configured in `.env`. Rebuild the index after changing
the embedding model or knowledge files. Live similarity thresholds may need adjustment for
your own documents.

## Knowledge base

`data/raw/` holds 12 Markdown manuals. `data/support_cases/cases.jsonl` holds 24 example cases.
They describe RelayDesk, a fictional service; the manuals are locally authored CC0-1.0 material
and the cases are synthetic.

Citations show the original passage and section. When the supplied evidence is insufficient,
the app returns no resolution. A citation alone does not establish that a suggested fix is correct.

To add manuals, place them in `data/raw/` and update `manifest.json`. Case `source_refs` must
match a manual's `source_id`. Rebuild the index afterward. Generated indexes and embedding
caches stay local and are excluded from Git.

## Docker

```powershell
docker build -t verithra .
docker run --rm -p 127.0.0.1:8501:8501 -v verithra-index:/app/data/index verithra
```

For OpenAI mode, add `--env-file .env` to the run command. The volume keeps the index between runs.
