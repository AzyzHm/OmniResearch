import { useEffect } from "react"
import { useLocation } from "react-router-dom"
import Nav from "@/features/landing/components/Nav"
import Hero from "@/features/landing/components/Hero"
import Features from "@/features/landing/components/Features"
import HowItWorks from "@/features/landing/components/HowItWorks"
import Footer from "@/features/landing/components/Footer"

function Landing() {
  const location = useLocation()

  useEffect(() => {
    if (location.hash) {
      const el = document.getElementById(location.hash.slice(1))
      el?.scrollIntoView({ behavior: "smooth" })
    }
  }, [location])

  return (
    <div className="min-h-screen bg-paper">
      <Nav />
      <Hero />
      <Features />
      <HowItWorks />
      <Footer />
    </div>
  )
}

export default Landing
