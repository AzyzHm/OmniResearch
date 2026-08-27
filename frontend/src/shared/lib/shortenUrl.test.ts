import { describe, it, expect } from "vitest"

import { shortenUrl } from "@/shared/lib/shortenUrl"

describe("shortenUrl", () => {
  it("strips protocol and www, keeping host + path", () => {
    expect(shortenUrl("https://www.example.com/articles/foo")).toBe(
      "example.com/articles/foo"
    )
  })

  it("leaves short URLs untouched", () => {
    expect(shortenUrl("https://example.com/")).toBe("example.com/")
  })

  it("truncates long paths with an ellipsis", () => {
    const long =
      "https://example.com/a/very/long/path/that/goes/on/and/on/and/on/forever"
    const result = shortenUrl(long, 30)
    expect(result.length).toBe(30)
    expect(result.endsWith("…")).toBe(true)
  })

  it("falls back to the raw string for an unparsable URL", () => {
    expect(shortenUrl("not-a-real-url", 30)).toBe("not-a-real-url")
  })
})