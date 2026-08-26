import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import Nav from "@/features/landing/components/Nav"
import Footer from "@/features/landing/components/Footer"

interface LegalPageProps {
  title: string
  lastUpdated: string
  content: string
}

function LegalPage({ title, lastUpdated, content }: LegalPageProps) {
  return (
    <div className="min-h-screen bg-paper flex flex-col">
      <Nav />
      <div className="flex-1 px-6 md:px-10 py-20 max-w-3xl mx-auto w-full">
        <h1 className="font-display text-3xl text-ink">{title}</h1>
        <p className="mt-2 font-mono text-xs text-muted-foreground">Last updated: {lastUpdated}</p>

        <div
          className={[
            "mt-8",
            "[&>*:first-child]:mt-0",
            "[&_h2]:font-display [&_h2]:text-xl [&_h2]:font-medium [&_h2]:text-ink [&_h2]:mt-8 [&_h2]:mb-3",
            "[&_h3]:font-display [&_h3]:text-base [&_h3]:font-medium [&_h3]:text-ink [&_h3]:mt-6 [&_h3]:mb-2",
            "[&_p]:my-3 [&_p]:text-sm [&_p]:leading-relaxed [&_p]:text-ink",
            "[&_ul]:my-3 [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:space-y-1",
            "[&_ol]:my-3 [&_ol]:list-decimal [&_ol]:pl-5 [&_ol]:space-y-1",
            "[&_li]:text-sm [&_li]:leading-relaxed [&_li]:text-ink",
            "[&_strong]:font-semibold",
            "[&_a]:text-teal [&_a]:underline [&_a]:underline-offset-2",
            "[&_hr]:my-8 [&_hr]:border-border",
            "[&_blockquote]:border-l-2 [&_blockquote]:border-teal [&_blockquote]:pl-4 [&_blockquote]:italic [&_blockquote]:text-muted-foreground",
            "[&_table]:my-4 [&_table]:w-full [&_table]:border-collapse [&_table]:text-sm",
            "[&_th]:border [&_th]:border-border [&_th]:bg-muted/50 [&_th]:px-3 [&_th]:py-2 [&_th]:text-left [&_th]:font-medium",
            "[&_td]:border [&_td]:border-border [&_td]:px-3 [&_td]:py-2",
          ].join(" ")}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>
      </div>
      <Footer />
    </div>
  )
}

export default LegalPage
