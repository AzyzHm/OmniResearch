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


* **👑 Role Hierarchy:** Three-tier access control (`user` / `admin` / `superadmin`). Admins manage regular users; only a superadmin can promote/demote roles or manage other admin accounts, and superadmin accounts themselves are protected from role changes or deletion.


* **🔎 Integrated Exploratory Engine:** Launch keyword-based searches directly from the interface, view web results, and use checkboxes to select relevant sites to populate your collections.


* **📦 Curation by Collections:** Organize your data by project into dedicated collections — local text files, PDF files, or lists of remote URLs.


* **🧠 Agentic RAG:** Chat in natural language with your corpus. The AI agent decides for itself whether a question needs retrieval at all, refines the query using conversation context, retrieves and validates the evidence it finds, and retries with more context before formulating a contextualized, sourced answer. Responses can be streamed token-by-token in real time.


* **🔀 Hybrid Retrieval & Reranking:** Choose between semantic (embedding), keyword (BM25), or hybrid retrieval — the latter fusing both rankings via Reciprocal Rank Fusion — followed by cross-encoder reranking of the pooled candidates for a final, precision-ordered context set.


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

OmniResearch is closed-source and all-rights-reserved, but contributions are welcome. If you'd like to fix a bug, add a feature, or improve the docs, feel free to open a pull request — by submitting one, you agree that the contribution is licensed to the project owner under the terms in [`LICENSE`](LICENSE) (see the "Contributions" clause). Submitting a contribution does not grant you, or anyone else, rights to use, deploy, or redistribute the Software itself.

For anything beyond a contribution (e.g. wanting to use, host, or build on OmniResearch), please reach out directly to discuss terms.

---

## 📄 License

This project is **not** open source. All rights, including ownership of the codebase and any future derivative works, are reserved by the copyright holder. The Software may be viewed for evaluation and reference purposes only — no use, execution, hosting, copying, modification, distribution, or resale is permitted without prior written consent. External contributions are welcome under the terms described above. See the [`LICENSE`](LICENSE) file at the root of this repository for the full terms.