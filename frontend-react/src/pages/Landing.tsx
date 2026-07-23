import { useEffect } from "react"
import { useLocation } from "react-router-dom"
import Nav from "@/components/Nav"
import Hero from "@/components/Hero"
import Features from "@/components/Features"
import HowItWorks from "@/components/HowItWorks"
import Footer from "@/components/Footer"

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