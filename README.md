# RAG System by PanScience

This project implements a Retrieval-Augmented Generation (RAG) system allowing users to upload documents, index them using embeddings, and ask questions grounded in those documents.

# Deploy Link
https://rag-system-fixed.onrender.com

## Features
- Upload up to 20 documents (PDF, TXT, DOCX).
- Chunking, embedding (OpenAI), and storage in a FAISS vector index.
- REST API (Flask) endpoints: `/upload`, `/query`, `/metadata`.
- SQLite for metadata storage.
- Docker and docker-compose for easy deployment.

## Quickstart (local)
1. Copy your OpenAI API key to an environment variable:
```bash
export OPENAI_API_KEY="sk-..."
```
2. Build and run with Docker Compose:
```bash
docker-compose up --build
```
3. Open `http://localhost:8080`

## Running tests
```bash
pytest -q
```

## Notes
- Configure other LLM providers by updating `services/vector_store.py` where embeddings/calls are made.
