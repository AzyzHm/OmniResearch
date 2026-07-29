import { Link } from "react-router-dom"
import AssistantBot from "@/shared/components/AssistantBot"

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
      <div
        className="relative hidden lg:flex flex-col justify-between px-12 py-10 overflow-hidden"
        style={{ backgroundColor: "#1C2321" }}
      >
        <div
          className="absolute inset-0 opacity-[0.5] pointer-events-none"
          style={{
            backgroundImage:
              "radial-gradient(color-mix(in srgb, #F1F3F0 8%, transparent) 1px, transparent 1px)",
            backgroundSize: "24px 24px",
          }}
        />
        <Link
          to="/"
          className="relative font-display italic text-xl"
          style={{ color: "#F1F3F0" }}
        >
          OmniResearch
        </Link>

        <div className="relative">
          <h2
            className="font-display text-3xl leading-[1.2] max-w-sm"
            style={{ color: "#F1F3F0" }}
          >
            Every answer, <span className="italic text-teal">traced back</span> to a source.
          </h2>
          <div className="mt-8 flex justify-center">
            <AssistantBot scheme="onDark" className="w-64 h-64" />
          </div>
        </div>

        <span
          className="relative text-xs"
          style={{ color: "color-mix(in srgb, #F1F3F0 50%, transparent)" }}
        >
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