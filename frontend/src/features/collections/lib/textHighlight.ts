interface NormalizedText {
  normalized: string
  map: number[]
}

function normalizeWithMap(text: string): NormalizedText {
  let normalized = ""
  const map: number[] = []
  let lastWasSpace = true // collapses leading whitespace too

  for (let i = 0; i < text.length; i++) {
    const ch = text[i]
    if (/\s/.test(ch)) {
      if (!lastWasSpace) {
        normalized += " "
        map.push(i)
        lastWasSpace = true
      }
    } else {
      normalized += ch
      map.push(i)
      lastWasSpace = false
    }
  }

  if (normalized.endsWith(" ")) {
    normalized = normalized.slice(0, -1)
    map.pop()
  }

  return { normalized, map }
}

export function findHighlightRange(
  haystack: string,
  needle: string | null | undefined
): { start: number; end: number } | null {
  const needleTrimmed = needle?.trim()
  if (!needleTrimmed) return null

  const { normalized: normalizedNeedle } = normalizeWithMap(needleTrimmed)
  if (!normalizedNeedle) return null

  const { normalized: normalizedHaystack, map } = normalizeWithMap(haystack)
  const index = normalizedHaystack.indexOf(normalizedNeedle)
  if (index === -1) return null

  return {
    start: map[index],
    end: map[index + normalizedNeedle.length - 1] + 1,
  }
}

export interface TextLayerItemLike {
  str?: string
  hasEOL?: boolean
}

export function computeItemHighlights(
  items: ReadonlyArray<TextLayerItemLike>,
  needle: string | null | undefined
): Map<number, [number, number]> | null {
  if (!needle?.trim()) return null

  let pageText = ""
  const itemRanges = new Map<number, [number, number]>()

  items.forEach((item, index) => {
    if (typeof item.str !== "string") return
    const start = pageText.length
    pageText += item.str
    itemRanges.set(index, [start, pageText.length])
    if (item.hasEOL) pageText += "\n"
  })

  const match = findHighlightRange(pageText, needle)
  if (!match) return null

  const highlights = new Map<number, [number, number]>()
  for (const [index, [itemStart, itemEnd]] of itemRanges) {
    const overlapStart = Math.max(itemStart, match.start)
    const overlapEnd = Math.min(itemEnd, match.end)
    if (overlapStart < overlapEnd) {
      highlights.set(index, [overlapStart - itemStart, overlapEnd - itemStart])
    }
  }

  return highlights.size > 0 ? highlights : null
}

export function escapeHtml(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
}