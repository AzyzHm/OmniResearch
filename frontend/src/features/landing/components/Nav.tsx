import { useEffect, useState } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { Button } from "@/shared/components/ui/button"
import ThemeToggle from "@/shared/components/ThemeToggle"
import appLogo from "@/assets/app-logo.svg"

const sectionLinks = [
  { label: "Features", id: "features" },
  { label: "How it works", id: "how-it-works" },
] as const

function Nav() {
  const [scrolled, setScrolled] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    onScroll()
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  function handleSectionClick(id: string, e: React.MouseEvent) {
    if (location.pathname === "/") {
      e.preventDefault()
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth" })
    } else {
      e.preventDefault()
      navigate(`/#${id}`)
    }
  }

  return (
    <nav
      className={`sticky top-0 z-50 w-full px-4 sm:px-6 md:px-10 transition-all duration-300 ${
        scrolled
          ? "bg-paper/75 backdrop-blur-md border-b border-border py-3"
          : "bg-transparent border-b border-transparent py-5"
      }`}
    >
      <div className="max-w-6xl mx-auto flex items-center justify-between gap-2">
        <Link
          to="/"
          className="flex min-w-0 items-center gap-2 font-display italic text-lg sm:text-xl text-ink"
        >
          <img src={appLogo} alt="" className="size-6 shrink-0" />
          <span className="truncate">OmniResearch</span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          {sectionLinks.map(({ label, id }) => (
            <a
              key={id}
              href={`/#${id}`}
              onClick={(e) => handleSectionClick(id, e)}
              className="text-sm text-muted-foreground hover:text-ink transition-colors"
            >
              {label}
            </a>
          ))}
        </div>

        <div className="flex shrink-0 items-center gap-1.5 sm:gap-3">
          <ThemeToggle />
          <Link to="/login">
            <Button variant="ghost" size="sm" className="sm:h-9 sm:px-4 sm:py-2 sm:text-sm">
              Log in
            </Button>
          </Link>
          <Link to="/signup">
            <Button size="sm" className="sm:h-9 sm:px-4 sm:py-2 sm:text-sm">
              Sign up
            </Button>
          </Link>
        </div>
      </div>
    </nav>
  )
}

export default Nav
