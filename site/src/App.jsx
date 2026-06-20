import { useEffect } from "react"
import Navbar from "./components/Navbar"
import Hero from "./components/Hero"
import Features from "./components/Features"
import HowItWorks from "./components/HowItWorks"
import Modes from "./components/Modes"
import QuickStart from "./components/QuickStart"
import CtaSection from "./components/CtaSection"
import Footer from "./components/Footer"

export default function App() {
  const scrollToQuickStart = () => {
    document.getElementById("quick-start")?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("opacity-100", "translate-y-0")
            entry.target.classList.remove("opacity-0", "translate-y-8")
          }
        })
      },
      { threshold: 0.08, rootMargin: "0px 0px -40px 0px" }
    )

    document.querySelectorAll("section").forEach((el) => {
      el.classList.add("transition-all", "duration-700", "ease-out")
      if (!el.classList.contains("opacity-100")) {
        el.classList.add("opacity-0", "translate-y-8")
      }
      observer.observe(el)
    })
    return () => observer.disconnect()
  }, [])

  return (
    <div className="relative min-h-screen bg-[var(--color-surface)] overflow-hidden selection:bg-cyan-500/30 selection:text-white">
      <div className="bg-grid" />
      <div className="glow-1" />
      <div className="glow-2" />
      <Navbar onGetStarted={scrollToQuickStart} />
      <main className="relative z-10">
        <Hero onGetStarted={scrollToQuickStart} />
        <Features />
        <HowItWorks />
        <Modes />
        <QuickStart />
        <CtaSection onGetStarted={scrollToQuickStart} />
      </main>
      <Footer />
    </div>
  )
}
