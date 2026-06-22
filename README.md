# OmniResearch

OmniResearch is a centralized research, curation, and document analysis platform powered by Artificial Intelligence (Agentic RAG). Designed specifically to streamline research workflows, it eliminates the fragmentation of traditional tools by combining web exploration and knowledge extraction within a single, secure environment.

The application allows users to seamlessly transition from keyword-based information discovery to deep semantic dialogue with an AI agent, based entirely on a custom, verified, and controlled corpus of sources.

---

## 🌟 Key Features

* **🔐 Authentication & Isolation (Multi-Tenancy):** Secure access to dedicated workspaces. A strict metadata filtering mechanism guarantees total isolation of document sources between each user account and project.


* **🔎 Integrated Exploratory Engine:** Launch keyword-based searches directly from the interface, view web results, and use checkboxes to select relevant sites to populate your collections.


* **📦 Curation by Collections:** Organize your data by project into dedicated collections (local PDF files or lists of remote URLs).


* **🧠 Agentic RAG:** Chat in natural language with your corpus. The AI agent analyzes, synthesizes, and formulates contextualized and sourced answers based on your active collections.


* **📊 Administration Panel:** A dedicated supervision interface to create new user accounts, track activity logs (connection timestamps), and graphically monitor API token consumption.



---

## 🏗️ Tech Stack

OmniResearch is built on a modern, decoupled, and high-performance architecture:

* **Frontend:** `Streamlit` (Reactive user interface utilizing native chat and dialog components).


* **Backend / API:** `FastAPI` (Asynchronous server handling business logic and orchestration).


* **Database:** `Supabase` (PostgreSQL for user authentication, project management, metadata, and administration logs).


* **Vector Database:** `ChromaDB` (Storage and semantic similarity search with metadata filtering).


* **AI Models:** `Gemini 2.5 Flash` (Text generation and synthesis via API) & `EmbeddingGemma` via `Ollama` (Local generation of semantic embeddings).


* **Scraping & Parsing:** `Jina Reader` (Conversion of webpage HTML into clean Markdown) & `PyPDF` (Text extraction from local files).


* **Search Engine:** `Tavily API` / `DuckDuckGo` (Web result retrieval for the exploratory search module).



---

## 🤝 Contributing

Community contributions are essential to moving OmniResearch forward! Whether you want to fix a bug, optimize the data extraction pipeline, improve the user interface, or enrich the agent's conversational memory, your help is welcome.

1. **Fork** the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`).
4. **Push** to the branch (`git push origin feature/AmazingFeature`).
5. Open a detailed **Pull Request**.

---

## 📄 License

This project is distributed under the **MIT** License. Full legal details regarding code protection and sharing can be found in the `LICENSE` file at the root of this repository.