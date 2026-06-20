import { useState, useEffect } from "react"

export default function Navbar({ onGetStarted }) {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener("scroll", onScroll)
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  return (
    <nav className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
      scrolled ? "bg-[rgba(5,5,15,0.85)] backdrop-blur-xl border-b border-white/5 shadow-lg shadow-black/20" : "bg-transparent"
    }`}>
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <a href="#" className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center text-black font-bold text-sm">M</div>
          <span className="text-white font-semibold text-lg tracking-tight">Morpheus</span>
        </a>
        <div className="hidden md:flex items-center gap-8">
          {["Features", "How It Works", "Modes", "LLM Setup", "Quick Start"].map(item => (
            <a key={item} href={`#${item.toLowerCase().replace(/\s+/g, "-")}`} className="text-sm text-[var(--color-text-secondary)] hover:text-white transition-colors">
              {item}
            </a>
          ))}
        </div>
        <button onClick={onGetStarted} className="glow-btn px-5 py-2 rounded-xl text-sm cursor-pointer">Get Started</button>
      </div>
    </nav>
  )
}
