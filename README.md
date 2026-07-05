# OmniResearch

OmniResearch is a centralized research, curation, and document analysis platform powered by Artificial Intelligence (Agentic RAG). Designed specifically to streamline research workflows, it eliminates the fragmentation of traditional tools by combining web exploration and knowledge extraction within a single, secure environment.

The application allows users to seamlessly transition from keyword-based information discovery to deep semantic dialogue with an AI agent, based entirely on a custom, verified, and controlled corpus of sources.

---

## 📚 Documentation

- [**Backend Documentation**](backend/docs/README.md) — architecture, API reference, database schema, the agentic RAG graph, LLM fallback, and usage monitoring.
- [**Frontend Documentation**](frontend/docs/README.md) — project structure, session state, the services (API client) layer, and the UI/UX patterns behind the workspace.

---

## 🌟 Key Features

* **🔐 Authentication & Isolation (Multi-Tenancy):** Secure access to dedicated workspaces. A strict metadata filtering mechanism guarantees total isolation of document sources between each user account and project.


* **🔎 Integrated Exploratory Engine:** Launch keyword-based searches directly from the interface, view web results, and use checkboxes to select relevant sites to populate your collections.


* **📦 Curation by Collections:** Organize your data by project into dedicated collections — local text files, PDF files, or lists of remote URLs.


* **🧠 Agentic RAG:** Chat in natural language with your corpus. The AI agent decides for itself whether a question needs retrieval at all, refines the query using conversation context, retrieves and validates the evidence it finds, and retries once with more context before formulating a contextualized, sourced answer.


* **📊 Administration Panel:** A dedicated supervision interface to approve pending user accounts, manage roles, track activity logs (connection timestamps), and monitor per-user LLM token consumption and search engine credit usage.



---

## 🏗️ Tech Stack

OmniResearch is built on a modern, decoupled, and high-performance architecture:

* **Frontend:** `Streamlit` (Reactive user interface utilizing native chat and dialog components).


* **Backend / API:** `FastAPI` (Asynchronous server handling business logic and orchestration).


* **Database:** `Supabase` (PostgreSQL for user authentication, project management, metadata, and administration logs).


* **Vector Database:** `ChromaDB` (Storage and semantic similarity search with metadata filtering).


* **AI Models:** `Gemini 2.5 Flash` (Primary text generation and synthesis via API, with automatic fallback to `Mistral` if the Gemini quota is exhausted) & `EmbeddingGemma` via `Ollama` (Local generation of semantic embeddings).


* **Scraping & Parsing:** `Jina Reader` (Conversion of webpage HTML into clean Markdown) & `PyPDF` (Text extraction from local files).


* **Search Engine:** `Tavily API` / `Exa API` (Web result retrieval for the exploratory search module).



---

## 🤝 Contributing

OmniResearch is currently a closed personal project. The license below does not permit forking, redistribution, or reuse of this code, so the standard fork → branch → pull request workflow does not apply here.

If you're interested in collaborating or have a specific proposal, please reach out directly to discuss terms rather than opening a pull request.

---

## 📄 License

This project is **not** open source. All rights are reserved by the copyright holder, the Software may be viewed for personal or educational purposes only. No copying, modification, merging, publishing, distribution, sublicensing, or sale of the Software (in whole or in part) is permitted without prior written consent. See the [`LICENSE`](LICENSE) file at the root of this repository for the full terms.