-- ============================================================================
-- OmniResearch — consolidated schema
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.users (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username           TEXT NOT NULL UNIQUE,
    password           TEXT NOT NULL,
    role               TEXT NOT NULL DEFAULT 'user'
                           CHECK (role IN ('user', 'admin', 'superadmin')),
    is_approved        BOOLEAN NOT NULL DEFAULT FALSE,
    daily_token_limit  INTEGER NOT NULL DEFAULT 80000,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.login_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    username    TEXT NOT NULL,
    login_time  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address  TEXT
);

CREATE TABLE IF NOT EXISTS public.projects (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.chats (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    name        TEXT NOT NULL DEFAULT 'New Chat',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.collections (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL CHECK (type IN ('documents', 'urls', 'text')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.collection_items (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID NOT NULL REFERENCES public.collections(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    source_type   TEXT NOT NULL CHECK (source_type IN ('txt', 'pdf', 'url')),
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    status        TEXT NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'ready', 'error')),
    chunk_count   INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.messages (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id    UUID NOT NULL REFERENCES public.chats(id) ON DELETE CASCADE,
    role       TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.llm_usage (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    provider          TEXT NOT NULL CHECK (provider IN ('gemini', 'mistral')),
    model             TEXT NOT NULL,
    prompt_tokens     INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens      INTEGER NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.search_usage (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    engine       TEXT NOT NULL CHECK (engine IN ('tavily', 'exa')),
    num_results  INTEGER NOT NULL DEFAULT 0,
    search_depth TEXT,
    credits      INTEGER NOT NULL DEFAULT 1,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Indexes ──────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_users_username              ON public.users(username);
CREATE INDEX IF NOT EXISTS idx_login_logs_user             ON public.login_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_login_logs_time             ON public.login_logs(login_time DESC);
CREATE INDEX IF NOT EXISTS idx_projects_user               ON public.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_chats_project               ON public.chats(project_id);
CREATE INDEX IF NOT EXISTS idx_collections_project         ON public.collections(project_id);
CREATE INDEX IF NOT EXISTS idx_collection_items_collection ON public.collection_items(collection_id);
CREATE INDEX IF NOT EXISTS idx_messages_chat_time          ON public.messages(chat_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_usage_user              ON public.llm_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_created           ON public.llm_usage(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_search_usage_user           ON public.search_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_search_usage_created        ON public.search_usage(created_at DESC);

-- ── Triggers ─────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_projects_updated_at ON public.projects;
CREATE TRIGGER trg_projects_updated_at
    BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ── Row Level Security ───────────────────────────────────────────────────
ALTER TABLE public.users            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.login_logs       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chats            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.collections      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.collection_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.llm_usage        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.search_usage     ENABLE ROW LEVEL SECURITY;

-- ── Bootstrap super admin ────────────────────────────────────────────────
INSERT INTO public.users (username, password, role, is_approved)
VALUES (
    'REPLACE_WITH_USERNAME',
    'REPLACE_WITH_ARGON2_HASH',
    'superadmin',
    TRUE
)
ON CONFLICT (username) DO NOTHING;