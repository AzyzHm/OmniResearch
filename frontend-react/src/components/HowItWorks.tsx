import { useInView } from "@/hooks/useInView"

const steps = [
  {
    number: "01",
    title: "Upload",
    description:
      "Add documents, paste in links, or pull in search results, all organized into projects and collections.",
  },
  {
    number: "02",
    title: "Ask",
    description:
      "Ask a question in plain language, or search for exact keywords when you know what you're looking for.",
  },
  {
    number: "03",
    title: "Read sourced answers",
    description:
      "Get an answer grounded in your own material, with a clear path back to where it came from.",
  },
] as const

function HowItWorks() {
  const { ref, inView } = useInView<HTMLDivElement>()

  return (
    <section
      id="how-it-works"
      className="relative bg-sand px-6 md:px-10 pt-4 pb-24 md:pb-32 overflow-hidden scroll-mt-24"
    >
      <div
        className="absolute inset-0 opacity-[0.4] pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(color-mix(in srgb, var(--color-ink) 10%, transparent) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />
      <div
        className="animate-blob absolute top-32 right-[15%] size-80 rounded-full bg-teal/12 blur-3xl pointer-events-none"
        aria-hidden
      />
      <div
        className="animate-blob absolute bottom-32 left-[10%] size-64 rounded-full bg-amber/15 blur-3xl pointer-events-none"
        style={{ animationDelay: "-5s" }}
        aria-hidden
      />

      <div className="relative max-w-2xl mx-auto">
        <h2 className="font-display text-2xl md:text-3xl text-ink mb-16">
          How it works
        </h2>

        <div ref={ref} className="relative">
          <div className="absolute left-6 top-6 bottom-6 w-px bg-[color-mix(in_srgb,var(--color-ink)_15%,transparent)]" />

          {steps.map(({ number, title, description }, i) => (
            <div
              key={number}
              className={`relative flex gap-6 pb-14 last:pb-0 transition-all duration-700 ease-out ${
                inView ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
              }`}
              style={{ transitionDelay: `${i * 180}ms` }}
            >
              <div className="relative z-10 size-12 rounded-full bg-sand border border-[color-mix(in_srgb,var(--color-ink)_20%,transparent)] flex items-center justify-center shrink-0">
                <span className="font-mono text-sm text-amber font-semibold">
                  {number}
                </span>
              </div>
              <div className="pt-2">
                <h3 className="font-display text-xl text-ink">{title}</h3>
                <p className="mt-2 text-sm md:text-base text-muted-foreground leading-relaxed max-w-md">
                  {description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div
        className="absolute bottom-0 left-0 right-0 h-32 pointer-events-none"
        style={{
          background: "linear-gradient(to bottom, transparent, var(--color-paper))",
        }}
      />
    </section>
  )
}

export default HowItWorks