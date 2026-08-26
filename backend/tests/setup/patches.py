from tests.setup.fakes import FakeDB, NoOpSweepDB


def patch_all_get_supabase(fake_db: FakeDB):
    """
    Replace `get_supabase` in every route module that imported it directly
    (since `from x import f` binds f locally, patching the source module
    is not enough -- each consumer module's reference must be replaced).
    Returns a restore function.
    """
    import database.db as db_mod
    import routes.admin.logs as r_admin_logs
    import routes.admin.quota as r_admin_quota
    import routes.admin.stats as r_admin_stats
    import routes.admin.usage as r_admin_usage
    import routes.admin.users as r_admin_users
    import routes.auth as r_auth
    import routes.chat._shared as r_chat_shared
    import routes.chat.crud as r_chat_crud
    import routes.chat.messages as r_chat_messages
    import routes.chat.send as r_chat_send
    import routes.collections._shared as r_collections_shared
    import routes.collections.crud as r_collections_crud
    import routes.collections.ingest as r_collections_ingest
    import routes.collections.items as r_collections_items
    import routes.notes._shared as r_notes_shared
    import routes.notes.crud as r_notes_crud
    import routes.notes.items as r_notes_items
    import routes.projects as r_projects
    import services.ingestion_recovery as r_ingestion_recovery

    modules = [
        r_auth, r_projects, db_mod,
        r_admin_users, r_admin_logs, r_admin_stats, r_admin_usage, r_admin_quota,
        r_chat_shared, r_chat_crud, r_chat_messages, r_chat_send,
        r_collections_shared, r_collections_crud, r_collections_ingest, r_collections_items,
        r_notes_shared, r_notes_crud, r_notes_items,
    ]
    originals = {m: m.get_supabase for m in modules}
    originals[r_ingestion_recovery] = r_ingestion_recovery.get_supabase

    def stub():
        return fake_db

    for m in modules:
        m.get_supabase = stub
    r_ingestion_recovery.get_supabase = lambda: NoOpSweepDB()

    def restore():
        for m, orig in originals.items():
            m.get_supabase = orig

    return restore