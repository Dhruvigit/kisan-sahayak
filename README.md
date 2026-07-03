# Kisan Sahayak

> An AI-powered Retrieval-Augmented Generation (RAG) system that provides accurate, document-grounded information about Indian Government agricultural schemes through a multilingual Telegram bot.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![LangChain](https://img.shields.io/badge/LangChain-RAG-green)
![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-orange)
![Groq](https://img.shields.io/badge/LLM-Groq-red)
![Telegram](https://img.shields.io/badge/Frontend-Telegram-blue)

---

## Overview

Kisan Sahayak is an information retrieval system that answers questions about Indian Government agricultural schemes using **Retrieval-Augmented Generation (RAG)**.

Instead of relying solely on an LLM's knowledge, the system retrieves relevant information from **official government documents** and **curated scheme summaries**, then generates responses grounded in the retrieved context.

The current version supports **Information Mode**, allowing users to ask factual questions about government schemes through a multilingual Telegram bot.

---

## Features

- Document-grounded question answering
- Semantic search using ChromaDB
- Intelligent query refinement and routing
- Metadata-aware retrieval pipeline
- Multilingual support (English, Hindi, Gujarati)
- Voice input and voice responses
- Telegram Bot interface
- Hybrid knowledge base using official PDFs and curated summaries

---

## Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.10+ |
| LLM | Groq (Llama 3.1 8B Instant) |
| Framework | LangChain |
| Vector Database | ChromaDB |
| Embeddings | BAAI/bge-m3 |
| Document Processing | PyMuPDF4LLM, python-docx |
| Frontend | Telegram Bot |
| Translation | Google Translator |
| Speech | SpeechRecognition, gTTS |
| Package Manager | uv |

---

## Repository Structure

```text
kisan-sahayak/
│
├── backend/
│   ├── app/
│   │   ├── information/
│   │   └── rag/
│   │       ├── generation/
│   │       ├── ingestion/
│   │       ├── retrieval/
│   │       ├── router/
│   │       ├── vectorization/
│   │       └── scheme_metadata.py
│   │
│   └── scripts/
│       ├── get_unique_headers.py
│       ├── inspect_vectorstore.py
│       └── run_information_tests.py
│
├── data/
│   ├── pdfs/
│   └── summaries/
│
├── frontend/
│   └── telegram_bot/
│
├── docs/
│   ├── Architecture.docx
│   ├── Design-Decisions.docx
│
├── main.py
├── pyproject.toml
├── uv.lock
├── README.md
└── .gitignore
```

---

## Documentation

Detailed project documentation is available in the `docs/` directory.

- **Architecture** – Overall system architecture and module interactions
- **Design Decisions** – Engineering choices and implementation rationale

---

# Project Setup

## Prerequisites

Before getting started, ensure you have the following installed:

- Python **3.10 - 3.12**
- Git
- [uv](https://docs.astral.sh/uv/) (Python package manager)

---

## 1. Clone the Repository

```bash
git clone https://github.com/Dhruvigit/kisan-sahayak.git

cd kisan-sahayak
```

---

## 2. Create a Virtual Environment

Using **uv**:

```bash
uv venv
```

Activate the environment:

### Windows

```powershell
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

---

## 3. Install Dependencies

Install all required packages from the lock file:

```bash
uv sync
```

This creates a reproducible environment using the versions defined in `uv.lock`.

---

## 4. Configure Environment Variables

Create a `.env` file in the project root.

```text
kisan-sahayak/
│
├── .env
├── backend/
├── frontend/
└── ...
```

Example:

```env
GROQ_API_KEY=your_groq_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

> **Note:** Never commit your `.env` file to GitHub.

---

## 5. Prepare the Knowledge Base

Place the official Government scheme PDFs inside:

```text
data/pdfs/
```

Example:

```text
PMFBY.pdf
PMKISAN.pdf
PMKSY.pdf
PMKMY.pdf
KCC.pdf
RWBCIS.pdf
```

Place the curated scheme summaries inside:

```text
data/summaries/
```

Example:

```text
PMFBY_summary.docx
PMKISAN_summary.docx
PMKSY_summary.docx
PMKMY_summary.docx
KCC_summary.docx
RWBCIS_summary.docx
```

---

## 6. Build the Vector Database

Before running the application, generate embeddings and create the Chroma vector database.

```bash
python backend/app/rag/vectorization/build_vectorstore.py
```

This process:

- Extracts text from PDFs and DOCX summaries
- Chunks the documents
- Generates metadata
- Creates embeddings
- Stores them in ChromaDB

The generated database will be stored in:

```text
data/vectordb/
```

> **Note:** The `data/vectordb/` directory is excluded from version control and must be generated locally.

---

## 7. Run the Telegram Bot

Start the application using:

```bash
python frontend/telegram_bot/bot.py
```

If everything is configured correctly, the bot will start listening for incoming Telegram messages.

---

## 8. Rebuilding the Vector Database

Whenever you:

- Add new scheme documents
- Modify existing PDFs
- Update summary documents

Delete the existing vector database and rebuild it.

```bash
# Delete the existing database
rm -rf data/vectordb
```

Windows (PowerShell):

```powershell
Remove-Item -Recurse -Force data\vectordb
```

Then rebuild:

```bash
python backend/app/rag/vectorization/build_vectorstore.py
```

---

## Quick Start

```bash
git clone https://github.com/Dhruvigit/kisan-sahayak.git

cd kisan-sahayak

uv venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

uv sync

# Create .env
# Add GROQ_API_KEY and TELEGRAM_BOT_TOKEN

python backend/app/rag/vectorization/build_vectorstore.py

python frontend/telegram_bot/bot.py
```

# Utility Scripts

The `backend/scripts/` directory contains helper utilities for testing, debugging, and validating different parts of the RAG pipeline during development.

| Script | Purpose |
|---------|---------|
| `run_information_tests.py` | Runs predefined information retrieval queries to validate the complete pipeline. |
| `inspect_vectorstore.py` | Displays stored chunks and metadata from the Chroma vector database. |
| `get_unique_headers.py` | Extracts unique document headers to verify header detection during ingestion. |

### Run Information Tests

```bash
python backend/scripts/run_information_tests.py
```

Use this script to verify that the information pipeline returns expected responses for predefined test queries.

---

### Inspect the Vector Database

```bash
python backend/scripts/inspect_vectorstore.py
```

Useful for checking:

- Stored chunks
- Metadata
- Source documents
- Retrieved context

---

### Inspect Extracted Headers

```bash
python backend/scripts/get_unique_headers.py
```

Lists the unique section headers detected from the source documents. This helps validate the header extraction logic used during document ingestion.

---

# Data Directory

The project expects the following directory structure:

```text
data/
├── pdfs/          # Official Government scheme PDFs
├── summaries/     # Curated DOCX summaries
└── vectordb/      # Generated locally (ignored by Git)
```

> **Note:** The `vectordb/` directory is generated after running the vectorization pipeline and is intentionally excluded from version control.

---

# Documentation

Detailed project documentation is available in the `docs/` directory.

| Document | Description |
|----------|-------------|
| `Architecture.docx` | System architecture and module interactions |
| `Design-Decisions.docx` | Engineering decisions and implementation rationale |

---

# Current Limitations

The current version is focused on **Information Mode**.

Current limitations include:

- Advisory mode is not yet implemented.
- Knowledge base is limited to the supported government schemes.
- Responses are restricted to the information available in the indexed documents.

---

# Future Enhancements

Planned improvements include:

- Advisory mode for personalized scheme recommendations
- Support for additional government schemes
- Web interface alongside Telegram
- OCR support for scanned PDF documents
- REST API for third-party integration
- Enhanced multilingual support

---

# Contributing

Contributions are welcome.

If you would like to improve the project:

1. Fork the repository.
2. Create a new feature branch.
3. Commit your changes.
4. Push the branch.
5. Open a Pull Request.

For major changes, please open an issue first to discuss the proposed improvements.

---

## Research

This repository contains the implementation developed as part of the research project:

**Kisan Sahayak: An AI-Powered Framework for Subsidy Recommendation for Farmers in India**

The associated research paper is currently under review.

For detailed system design and implementation, refer to the documents in the `docs/` directory.
