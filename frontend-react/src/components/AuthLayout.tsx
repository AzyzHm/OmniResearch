import { Link } from "react-router-dom"
import { FileText } from "lucide-react"

function AuthLayout({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle: string
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      <div className="relative hidden lg:flex flex-col justify-between bg-ink px-12 py-10 overflow-hidden">
        <div
          className="absolute inset-0 opacity-[0.5] pointer-events-none"
          style={{
            backgroundImage:
              "radial-gradient(color-mix(in srgb, var(--color-paper) 8%, transparent) 1px, transparent 1px)",
            backgroundSize: "24px 24px",
          }}
        />
        <Link
          to="/"
          className="relative font-display italic text-xl text-paper"
        >
          OmniResearch
        </Link>

        <div className="relative">
          <h2 className="font-display text-3xl leading-[1.2] text-paper max-w-sm">
            Every answer, <span className="italic text-teal">traced back</span> to a source.
          </h2>
          <div className="mt-8 bg-[color-mix(in_srgb,var(--color-paper)_6%,transparent)] border border-[color-mix(in_srgb,var(--color-paper)_15%,transparent)] rounded-xl p-4 max-w-sm">
            <div className="flex items-center gap-1.5 text-[color-mix(in_srgb,var(--color-paper)_60%,transparent)]">
              <FileText className="size-3.5" />
              <span className="font-mono text-[11px]">
                q3_market_report.pdf
              </span>
            </div>
            <blockquote className="mt-2 border-l-2 border-teal pl-2.5 text-sm text-paper leading-relaxed italic">
              Overhead costs fell roughly 30%
              <sup className="not-italic font-mono text-teal font-semibold">
                1
              </sup>
            </blockquote>
          </div>
        </div>

        <span className="relative text-xs text-[color-mix(in_srgb,var(--color-paper)_50%,transparent)]">
          © 2026 OmniResearch
        </span>
      </div>

      <div className="flex flex-col justify-center px-6 md:px-16 py-16 bg-paper">
        <div className="max-w-sm w-full mx-auto">
          <Link
            to="/"
            className="lg:hidden font-display italic text-xl text-ink mb-10 inline-block"
          >
            OmniResearch
          </Link>
          <h1 className="font-display text-2xl text-ink">{title}</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
      </div>
    </div>
  )
}

export default AuthLayout