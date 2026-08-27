import { describe, it, expect } from "vitest"

import { findHighlightRange, computeItemHighlights, escapeHtml } from "@/features/collections/lib/textHighlight"

describe("findHighlightRange", () => {
  it("finds an exact match and returns the original-coordinate range", () => {
    const haystack = "Intro. Revenue grew 12% year over year. Outro."
    const range = findHighlightRange(haystack, "Revenue grew 12% year over year.")
    expect(range).toEqual({ start: 7, end: 39 })
    expect(haystack.slice(range!.start, range!.end)).toBe("Revenue grew 12% year over year.")
  })

  it("matches across whitespace/newline differences (pypdf vs pdf.js extraction)", () => {
    const haystack = "Intro.\nRevenue   grew\n12%\nyear over year.\nOutro."
    const range = findHighlightRange(haystack, "Revenue grew 12% year over year.")
    expect(range).not.toBeNull()
    expect(haystack.slice(range!.start, range!.end).replace(/\s+/g, " ")).toBe(
      "Revenue   grew\n12%\nyear over year.".replace(/\s+/g, " ")
    )
  })

  it("returns null when the needle isn't present", () => {
    expect(findHighlightRange("Some unrelated text.", "Not in here.")).toBeNull()
  })

  it("returns null for empty/whitespace-only needles", () => {
    expect(findHighlightRange("Some text.", "")).toBeNull()
    expect(findHighlightRange("Some text.", "   ")).toBeNull()
    expect(findHighlightRange("Some text.", null)).toBeNull()
    expect(findHighlightRange("Some text.", undefined)).toBeNull()
  })
})

describe("computeItemHighlights", () => {
  it("locates a chunk split across multiple text-layer items on one page", () => {
    const items = [
      { str: "Intro paragraph." },
      { str: "Revenue grew", hasEOL: true },
      { str: "12% year over year." },
      { str: "Outro paragraph." },
    ]
    const highlights = computeItemHighlights(items, "Revenue grew 12% year over year.")
    expect(highlights).not.toBeNull()
    // Item 1 ("Revenue grew") and item 2 ("12% year over year.") both
    // participate in the match; items 0 and 3 don't.
    expect(highlights!.has(0)).toBe(false)
    expect(highlights!.has(1)).toBe(true)
    expect(highlights!.has(2)).toBe(true)
    expect(highlights!.has(3)).toBe(false)
    expect(highlights!.get(1)).toEqual([0, "Revenue grew".length])
    expect(highlights!.get(2)).toEqual([0, "12% year over year.".length])
  })

  it("preserves original item indices when non-text marked-content items are interleaved", () => {
    const items: Array<{ str?: string; hasEOL?: boolean }> = [
      { str: "Before." },
      {}, // a TextMarkedContent entry with no `str`
      { str: "Revenue grew 12%." },
    ]
    const highlights = computeItemHighlights(items, "Revenue grew 12%.")
    expect(highlights).toEqual(new Map([[2, [0, "Revenue grew 12%.".length]]]))
  })

  it("returns null when the chunk isn't found on this page", () => {
    const items = [{ str: "This page has nothing to do with it." }]
    expect(computeItemHighlights(items, "Revenue grew 12%.")).toBeNull()
  })

  it("returns null when there's no highlight text to search for", () => {
    const items = [{ str: "Anything." }]
    expect(computeItemHighlights(items, null)).toBeNull()
    expect(computeItemHighlights(items, undefined)).toBeNull()
    expect(computeItemHighlights(items, "  ")).toBeNull()
  })
})

describe("escapeHtml", () => {
  it("escapes &, <, and > so raw PDF text can't break the injected markup", () => {
    expect(escapeHtml("Q&A: revenue < 5% > target")).toBe("Q&amp;A: revenue &lt; 5% &gt; target")
  })
})