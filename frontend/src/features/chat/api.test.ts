import { describe, it, expect, vi, type Mock } from "vitest"

import { streamChatMessage, createChat } from "@/features/chat/api"

describe("createChat", () => {
  it("always sends a JSON body, even with no name given", async () => {
    // Regression test: the backend route requires the body itself to be
    // present (it's a required Pydantic model parameter), even though
    // every field on that model has a default. Omitting the body entirely
    // causes a silent 422 with no visible error.
    const fetchMock: Mock<typeof fetch> = vi.fn()
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "c1",
          project_id: "p1",
          name: "New Chat",
          created_at: "2026-01-01T00:00:00Z",
        }),
        { status: 201, headers: { "content-type": "application/json" } },
      ),
    )
    globalThis.fetch = fetchMock as unknown as typeof fetch

    await createChat("p1")

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(options.body).toBeDefined()
    expect(JSON.parse(options.body as string)).toEqual({ name: "New Chat" })
  })
})

function makeStreamResponse(chunks: string[]) {
  const encoder = new TextEncoder()
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk))
      }
      controller.close()
    },
  })
  return new Response(stream, {
    status: 200,
    headers: { "content-type": "text/event-stream" },
  })
}

describe("streamChatMessage", () => {
  it("parses multiple SSE frames, including one split across two chunks", async () => {
    const frame1 = `data: ${JSON.stringify({ type: "node", node: "retrieve" })}\n\n`
    const frame2 = `data: ${JSON.stringify({ type: "node", node: "generate" })}\n\n`
    const frame3 = `data: ${JSON.stringify({ type: "done", answer: "Hello there" })}\n\n`

    // Deliberately split frame2 across a chunk boundary, mid-JSON.
    const splitPoint = Math.floor(frame2.length / 2)
    const chunks = [frame1 + frame2.slice(0, splitPoint), frame2.slice(splitPoint) + frame3]

    globalThis.fetch = vi.fn(() =>
      Promise.resolve(makeStreamResponse(chunks)),
    ) as unknown as typeof fetch

    const events = []
    for await (const event of streamChatMessage("chat1", "hi", "semantic")) {
      events.push(event)
    }

    expect(events).toEqual([
      { type: "node", node: "retrieve" },
      { type: "node", node: "generate" },
      { type: "done", answer: "Hello there" },
    ])
  })

  it("passes sources through in the done event unchanged", async () => {
    const sources = [{ index: 1, source_name: "report.pdf", collection_id: "c1", item_id: "i1" }]
    const frame = `data: ${JSON.stringify({ type: "done", answer: "Revenue grew [1].", sources })}\n\n`

    globalThis.fetch = vi.fn(() =>
      Promise.resolve(makeStreamResponse([frame])),
    ) as unknown as typeof fetch

    const events = []
    for await (const event of streamChatMessage("chat1", "hi", "semantic")) {
      events.push(event)
    }

    expect(events).toEqual([{ type: "done", answer: "Revenue grew [1].", sources }])
  })

  it("throws an ApiError when the request fails before streaming starts", async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve(
        new Response(JSON.stringify({ detail: "Chat not found." }), {
          status: 404,
          headers: { "content-type": "application/json" },
        }),
      ),
    ) as unknown as typeof fetch

    await expect(async () => {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      for await (const _event of streamChatMessage("missing", "hi", "semantic")) {
        // no-op — should throw before yielding anything
      }
    }).rejects.toMatchObject({ status: 404, message: "Chat not found." })
  })
})
