class FakeResult:
    def __init__(self, data=None, count=None):
        self.data = [] if data is None else data
        self.count = count


class FakeQuery:
    """Fluent query builder whose .execute() pops the next queued result."""
    def __init__(self, result: FakeResult):
        self._result = result

    def __getattr__(self, name):
        def _method(*args, **kwargs):
            return self
        return _method

    def execute(self) -> FakeResult:
        return self._result


class FakeRAGGraph:
    """
    Stand-in for the compiled LangGraph RAG pipeline. Configure `.answer`,
    `.sources`, or `.raise_exc` before making a request to control the
    outcome of POST /chats/{id}/message and /message/stream.
    """
    def __init__(self, answer="Mocked AI reply", sources=None, raise_exc=None):
        self.answer = answer
        self.sources = sources if sources is not None else []
        self.raise_exc = raise_exc
        self.last_invoke_state = None

    def invoke(self, state):
        self.last_invoke_state = state
        if self.raise_exc:
            raise self.raise_exc
        return {"answer": self.answer, "sources": self.sources}

    def stream(self, state, stream_mode="updates"):
        self.last_invoke_state = state
        if self.raise_exc:
            raise self.raise_exc
        yield {"router": {"needs_retrieval": False}}
        yield {"generate": {"answer": self.answer, "sources": self.sources}}


class FakeDB:
    """FIFO queue of results. Each route call to db.table(...).execute()
    pops the next queued FakeResult, so tests must queue results in the
    exact order the route under test will consume them."""
    def __init__(self):
        self._queue: list[FakeResult] = []
        self._default = FakeResult(data=[], count=0)
        self.rag_graph = FakeRAGGraph()

    def add_result(self, data=None, count=None) -> "FakeDB":
        self._queue.append(FakeResult(data=data, count=count))
        return self

    def table(self, _name: str) -> FakeQuery:
        result = self._queue.pop(0) if self._queue else self._default
        return FakeQuery(result)


class NoOpSweepDB:
    """
    Dedicated stand-in for the startup "processing" sweep (see
    services.ingestion_recovery), which runs automatically every time the
    `app` fixture's TestClient enters (real ASGI lifespan). It's
    deliberately NOT the shared FakeDB: that queue is meant for each
    test's own db.add_result(...) calls, and if the sweep consumed the
    same queue it would silently eat the first result every test queues,
    corrupting unrelated assertions instead of failing loudly.
    """
    def table(self, _name: str) -> FakeQuery:
        return FakeQuery(FakeResult(data=[]))