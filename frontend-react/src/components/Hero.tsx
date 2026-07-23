import { Link } from "react-router-dom"
import { ArrowUpRight, FileText, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"

function Hero() {
  return (
    <section className="relative px-6 md:px-10 pt-16 md:pt-20 pb-24 md:pb-32 overflow-hidden">
      <div
        className="absolute inset-0 opacity-[0.4] pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(color-mix(in srgb, var(--color-ink) 12%, transparent) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
          maskImage:
            "radial-gradient(ellipse 55% 45% at 50% 15%, black 30%, transparent 85%)",
        }}
      />

      <div
        className="animate-blob absolute top-24 right-[12%] size-64 rounded-full bg-teal/15 blur-3xl pointer-events-none"
        aria-hidden
      />
      <div
        className="animate-blob absolute top-56 left-[6%] size-48 rounded-full bg-amber/15 blur-3xl pointer-events-none"
        style={{ animationDelay: "-4s" }}
        aria-hidden
      />

      <div className="relative max-w-6xl mx-auto grid lg:grid-cols-[1.05fr_1fr] gap-16 items-center">
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-3 py-1 text-xs font-mono text-teal">
            <Sparkles className="size-3.5" />
            Personal research workspace
          </span>

          <h1 className="font-display text-5xl md:text-6xl leading-[1.08] text-ink mt-6">
            Every answer,{" "}
            <span className="italic text-teal">traced back</span> to a
            source.
          </h1>
          <p className="mt-6 text-lg text-muted-foreground max-w-md">
            Upload documents, add links, or pull in web research. Then ask
            questions and get answers grounded in what you gave it, not
            guesswork.
          </p>
          <div className="mt-8 flex items-center gap-5">
            <Link to="/signup">
              <Button size="lg" className="text-base px-6">
                Sign up
              </Button>
            </Link>
            <a
              href="https://github.com/AzyzHm/OmniResearch"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm font-medium text-ink hover:text-teal transition-colors"
            >
              View on GitHub
              <ArrowUpRight className="size-4" />
            </a>
          </div>
        </div>

        <div className="relative">
          <div className="hidden md:block absolute -left-8 -bottom-10 bg-surface border border-border rounded-xl shadow-sm p-4 w-56 rotate-[-6deg] z-0">
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <FileText className="size-3.5" />
              <span className="font-mono text-[11px]">
                q3_market_report.pdf
              </span>
            </div>
            <blockquote className="mt-2 border-l-2 border-teal pl-2.5 text-xs text-ink leading-relaxed italic">
              Overhead costs fell roughly 30%
              <sup className="not-italic font-mono text-teal font-semibold">
                1
              </sup>
            </blockquote>
          </div>

          <div className="relative z-10 bg-surface border border-border rounded-xl shadow-md overflow-hidden">
            <div className="flex items-center gap-1.5 px-4 py-3 border-b border-border bg-[color-mix(in_srgb,var(--color-ink)_4%,var(--color-surface))]">
              <span className="size-2.5 rounded-full bg-border" />
              <span className="size-2.5 rounded-full bg-border" />
              <span className="size-2.5 rounded-full bg-border" />
              <span className="ml-2 font-mono text-xs text-muted-foreground">
                Q3 Market Analysis
              </span>
            </div>

            <div className="p-5 space-y-4">
              <div className="flex justify-end">
                <div className="bg-ink text-paper rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm max-w-[80%]">
                  Did remote work actually cut costs for these firms?
                </div>
              </div>

              <div className="flex justify-start">
                <div className="bg-[color-mix(in_srgb,var(--color-teal)_8%,var(--color-surface))] rounded-2xl rounded-tl-sm px-4 py-3 text-sm max-w-[85%] text-ink leading-relaxed">
                  Remote work reduced office overhead costs by roughly 30% in
                  the surveyed firms
                  <sup className="font-mono text-teal font-semibold mx-0.5">
                    1
                  </sup>
                  .
                  <div className="mt-2.5 pt-2.5 border-t border-border/70 flex items-center gap-1.5 text-xs text-muted-foreground">
                    <FileText className="size-3.5 text-teal" />
                    <span className="font-mono">
                      q3_market_report.pdf · p.4
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <span className="rounded-full border border-border px-2.5 py-1 text-[11px] font-mono text-teal bg-[color-mix(in_srgb,var(--color-teal)_6%,var(--color-surface))]">
                  semantic
                </span>
                <span className="rounded-full border border-border px-2.5 py-1 text-[11px] font-mono text-muted-foreground">
                  keyword
                </span>
                <span className="rounded-full border border-border px-2.5 py-1 text-[11px] font-mono text-muted-foreground">
                  hybrid
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        className="absolute bottom-0 left-0 right-0 h-24 pointer-events-none"
        style={{
          background:
            "linear-gradient(to bottom, transparent, var(--color-surface))",
        }}
      />
    </section>
  )
}

export default Hero