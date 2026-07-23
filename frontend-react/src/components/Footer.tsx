import { Link } from "react-router-dom"
import { useInView } from "@/hooks/useInView"

const legalLinks = [
  { label: "Terms of Service", href: "/terms" },
  { label: "Privacy Policy", href: "/privacy" },
  { label: "Cookie Policy", href: "/cookies" },
] as const

function Footer() {
  const { ref, inView } = useInView<HTMLDivElement>()

  return (
    <footer className="bg-paper px-6 md:px-10 pt-12 pb-10">
      <div
        ref={ref}
        className={`max-w-6xl mx-auto transition-all duration-700 ease-out ${
          inView ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
        }`}
      >
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-8">
          <div>
            <span className="font-display italic text-xl text-ink">
              OmniResearch
            </span>
            <p className="mt-3 text-sm text-muted-foreground max-w-xs">
              A personal research workspace for grounded, sourced answers.
            </p>
          </div>

          <div>
            <h4 className="font-mono text-xs uppercase tracking-wide text-muted-foreground">
              Legal
            </h4>
            <ul className="mt-4 space-y-2.5">
              {legalLinks.map((link) => (
                <li key={link.label}>
                  <Link
                    to={link.href}
                    className="text-sm text-ink hover:text-teal transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-10 pt-6 border-t border-border text-xs text-muted-foreground">
          © 2026 OmniResearch. Built by Azyz Hamdi.
        </div>
      </div>
    </footer>
  )
}

export default Footer