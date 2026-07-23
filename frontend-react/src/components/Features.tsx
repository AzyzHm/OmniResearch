import { FolderKanban, MessagesSquare, SearchCheck } from "lucide-react"
import { useInView } from "@/hooks/useInView"

const features = [
  {
    icon: FolderKanban,
    title: "Organize your research",
    description:
      "Projects, chats, and collections keep every document, link, and note in context, so nothing gets scattered across tabs.",
    accent: "teal",
  },
  {
    icon: MessagesSquare,
    title: "Ask questions, get grounded answers",
    description:
      "Answers are pulled from your own sources, not general guesswork, and you can always see where they came from.",
    accent: "amber",
  },
  {
    icon: SearchCheck,
    title: "Search your way",
    description:
      "Choose plain questions or precise keyword lookups, depending on what you're trying to find.",
    accent: "teal",
  },
] as const

function Features() {
  const { ref, inView } = useInView<HTMLDivElement>()

  return (
    <section
      id="features"
      className="relative bg-surface px-6 md:px-10 pt-4 pb-24 md:pb-32 overflow-hidden scroll-mt-24"
    >
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 size-96 rounded-full bg-amber/8 blur-3xl pointer-events-none"
        aria-hidden
      />

      <div className="relative max-w-4xl mx-auto">
        <h2 className="font-display text-2xl md:text-3xl text-ink mb-14">
          What you get
        </h2>

        <div ref={ref}>
          {features.map(({ icon: Icon, title, description, accent }, i) => (
            <div
              key={title}
              className={`flex items-start gap-6 md:gap-10 py-9 transition-all duration-700 ease-out ${
                i !== 0 ? "border-t border-border" : ""
              } ${inView ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-6"}`}
              style={{ transitionDelay: `${i * 130}ms` }}
            >
              <span className="font-mono text-sm text-muted-foreground pt-1 w-6 shrink-0">
                0{i + 1}
              </span>
              <div
                className={
                  accent === "teal"
                    ? "size-12 rounded-full flex items-center justify-center shrink-0 bg-[color-mix(in_srgb,var(--color-teal)_12%,transparent)]"
                    : "size-12 rounded-full flex items-center justify-center shrink-0 bg-[color-mix(in_srgb,var(--color-amber)_15%,transparent)]"
                }
              >
                <Icon
                  className={accent === "teal" ? "size-5 text-teal" : "size-5 text-amber"}
                />
              </div>
              <div>
                <h3 className="font-display text-xl text-ink">{title}</h3>
                <p className="mt-1.5 text-sm md:text-base text-muted-foreground leading-relaxed max-w-lg">
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
          background: "linear-gradient(to bottom, transparent, var(--color-sand))",
        }}
      />
    </section>
  )
}

export default Features