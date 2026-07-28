import { Link } from "react-router-dom"
import { ArrowUpRight, Sparkles } from "lucide-react"
import { Button } from "@/shared/components/ui/button"
import RagPipelineIllustration from "@/shared/components/RagPipelineIllustration"

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

        <div className="relative flex items-center justify-center">
          <div
            className="absolute inset-0 m-auto size-80 rounded-full bg-teal/10 blur-2xl pointer-events-none"
            aria-hidden
          />
          <RagPipelineIllustration className="relative z-10 w-104 h-[25.2rem] md:w-120 md:h-116" />
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