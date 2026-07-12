ROUTER_PROMPT = """You are the routing step of a research assistant. Decide whether answering the user's latest message requires retrieving information from the user's own document/URL sources, or whether it can be answered directly.

Choose RETRIEVE when:
- The question needs specific facts, details, or content that would come from the user's uploaded documents or saved URLs.
- The user explicitly asks to search, look up, or check their sources/collections.

Choose DIRECT when:
- The message is a greeting, small talk, or general conversation.
- The question can already be fully answered using only the conversation history below.
- The user is asking about the assistant itself, or asking for a clarification of something already said in this conversation.

Conversation history:
{history_text}

User's latest message:
{query}

Respond with exactly one word — RETRIEVE or DIRECT — and nothing else."""


REFINE_QUERY_PROMPT = """Rewrite the user's latest message into a single, standalone search query, using the conversation history only to resolve references (pronouns, "it", "that", implied subjects, etc.). The rewritten query must be understandable on its own, with no memory of the conversation, and must preserve the user's original intent without adding new assumptions.

Conversation history:
{history_text}

User's latest message:
{query}

Respond with only the rewritten standalone query, and nothing else."""


VALIDATION_PROMPT = """Judge whether the context below is sufficient to fully and accurately answer the user's question. Base your judgment only on the context provided — do not use outside knowledge.

User's question:
{query}

Retrieved context:
{context_text}

Respond in exactly one of these two forms, and nothing else:
- The single word SUFFICIENT, if the context fully answers the question.
- INSUFFICIENT: <query>, if it does not — where <query> is a short, specific, self-contained search query describing exactly what information is still missing. It must not reference "the context" or use pronouns; phrase it as something that could be searched for on its own."""


GENERATION_PROMPT = """Answer the user's question using the retrieved context below when it is relevant, along with the ongoing conversation. If the context does not fully cover the question, answer as best you can with what is available and be upfront about what is missing — do not say you "don't have access" without first using whatever relevant context is provided.

Retrieved context:
{context_text}

User's question:
{query}"""