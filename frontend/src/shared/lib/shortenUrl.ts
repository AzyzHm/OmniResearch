export function shortenUrl(url: string, maxLength = 42): string {
  let display: string
  try {
    const parsed = new URL(url)
    const host = parsed.hostname.replace(/^www\./, "")
    display = host + parsed.pathname + parsed.search
  } catch {
    display = url
  }
  if (display.length <= maxLength) return display
  return display.slice(0, maxLength - 1) + "…"
}