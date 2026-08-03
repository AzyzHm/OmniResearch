<h1 align="center">OmniResearch </h1>
<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?logo=streamlit&logoColor=white">
  <img alt="Supabase" src="https://img.shields.io/badge/Supabase-PostgreSQL-3FCF8E?logo=supabase&logoColor=white">
  <img alt="ChromaDB" src="https://img.shields.io/badge/ChromaDB-Vector%20Store-FF6F00">
  <img alt="LangGraph" src="https://img.shields.io/badge/LangGraph-Agentic%20RAG-1C3C3C">
  <img alt="License" src="https://img.shields.io/badge/License-Apache%202.0-blue.svg">
</p>

> **Note:** This is the `legacy/streamlit-mvp` branch, a frozen snapshot of OmniResearch's original Streamlit-based frontend. The active development branch has since migrated the frontend to React + TypeScript + Vite. This branch is kept for archival and reference purposes.

OmniResearch is a centralized research, curation, and document analysis platform powered by Artificial Intelligence (Agentic RAG). Designed specifically to streamline research workflows, it eliminates the fragmentation of traditional tools by combining web exploration and knowledge extraction within a single, secure environment.

The application allows users to seamlessly transition from keyword-based information discovery to deep semantic dialogue with an AI agent, based entirely on a custom, verified, and controlled corpus of sources.

---

## 📚 Documentation

- [**Backend Documentation**](backend/docs/README.md): architecture, API reference, database schema, the agentic RAG graph, LLM fallback, and usage monitoring.
- [**Frontend Documentation**](frontend/docs/README.md): project structure, session state, the services (API client) layer, and the UI/UX patterns behind the workspace.

---

## 🌟 Key Features

* **🔐 Authentication & Isolation (Multi-Tenancy):** Secure access to dedicated workspaces. A strict metadata filtering mechanism guarantees total isolation of document sources between each user account and project.


* **👑 Role Hierarchy:** Three-tier access control (`user` / `admin` / `superadmin`). Admins manage regular users; only a superadmin can promote/demote roles or manage other admin accounts, and superadmin accounts themselves are protected from role changes or deletion.


* **🔎 Integrated Exploratory Engine:** Launch keyword-based searches directly from the interface, view web results, and use checkboxes to select relevant sites to populate your collections.


* **📦 Curation by Collections:** Organize your data by project into dedicated collections, local text files, PDF files, or lists of remote URLs.


* **🧠 Agentic RAG:** Chat in natural language with your corpus. The AI agent decides for itself whether a question needs retrieval at all, refines the query using conversation context, retrieves and validates the evidence it finds, and retries with more context before formulating a contextualized, sourced answer. Responses can be streamed token-by-token in real time.


* **🔀 Hybrid Retrieval & Reranking:** Choose between semantic (embedding), keyword (BM25), or hybrid retrieval, the latter fusing both rankings via Reciprocal Rank Fusion, followed by cross-encoder reranking of the pooled candidates for a final, precision-ordered context set.


* **🚦 Per-User Token Quotas:** Configurable daily LLM token limits per user, enforced automatically before each chat request and adjustable by admins.


* **📊 Administration Panel:** A dedicated supervision interface to approve pending user accounts, manage roles, track activity logs (connection timestamps), and monitor per-user LLM token consumption and search engine credit usage.



---

## 🏗️ Tech Stack

OmniResearch is built on a modern, decoupled, and high-performance architecture:

* **Frontend:** `Streamlit` (Reactive user interface utilizing native chat and dialog components).


* **Backend / API:** `FastAPI` (Asynchronous server handling business logic and orchestration).


* **Database:** `Supabase` (PostgreSQL for user authentication, project management, metadata, and administration logs).


* **Vector Database:** `ChromaDB` (Storage and semantic similarity search with metadata filtering).


* **AI Models:** `Gemini 2.5 Flash` (Primary text generation and synthesis via API, with automatic fallback to `Mistral` if the Gemini quota is exhausted) & `EmbeddingGemma` via `Ollama` (Local generation of semantic embeddings).


* **Retrieval & Reranking:** `ChromaDB`'s built-in BM25 sparse embedding function (keyword retrieval) fused with semantic search via Reciprocal Rank Fusion, followed by cross-encoder reranking (`BAAI/bge-reranker-base` via `sentence-transformers`) of the pooled candidates.


* **Scraping & Parsing:** `Jina Reader` (Conversion of webpage HTML into clean Markdown) & `PyPDF` (Text extraction from local files).


* **Search Engine:** `Tavily API` / `Exa API` (Web result retrieval for the exploratory search module).



---

## 🤝 Contributing

Contributions are welcome. If you'd like to fix a bug, add a feature, or improve the docs, feel free to open an issue or a pull request.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to open an issue (including the issue template) and how to submit a pull request.

---

## 🔒 Security

Found a vulnerability? Please report it privately rather than opening a public issue. See [`SECURITY.md`](SECURITY.md) for how to reach out.

---

## 📄 License

This project is licensed under the **Apache License, Version 2.0**. You're free to use, modify, and distribute this software, including for commercial purposes, provided you comply with the license's terms (attribution, a copy of the license, and a note of any changes made to the source). See the [`LICENSE`](LICENSE) file at the root of this repository for the full text.