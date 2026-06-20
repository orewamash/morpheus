import { useEffect, useRef } from "react"

const modes = [
  { name: "spy", desc: "Snoop into Python's innards. Inspect objects, functions, modules, classes, and attributes at runtime.", badge: "No LLM", badgeColor: "bg-green-500/10 text-green-400 border-green-500/20" },
  { name: "prophecy", desc: "Predict and highlight technical debt patterns before they become production incidents.", badge: "No LLM", badgeColor: "bg-green-500/10 text-green-400 border-green-500/20" },
  { name: "analyze", desc: "Deep-dive code analysis: coupling, cohesion, complexity, architectural smells, dead code.", badge: "No LLM", badgeColor: "bg-green-500/10 text-green-400 border-green-500/20" },
  { name: "diff", desc: "Intelligent diff analysis. Understand what a PR introduces in architectural terms.", badge: "No LLM", badgeColor: "bg-green-500/10 text-green-400 border-green-500/20" },
  { name: "map", desc: "Visualize your codebase as an interactive dependency graph. Find circular deps and orphan modules.", badge: "No LLM", badgeColor: "bg-green-500/10 text-green-400 border-green-500/20" },
  { name: "narrator", desc: "Get a human-readable tour of any code path. Like a senior dev walking you through the codebase.", badge: "Requires LLM", badgeColor: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
  { name: "teach", desc: "Learn design patterns and idioms from your own codebase. Personalized upskilling at scale.", badge: "Requires LLM", badgeColor: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
  { name: "oracle", desc: "Ask architecture questions in natural language. \"What happens when a user logs in?\"", badge: "Requires LLM", badgeColor: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
]

function ModeItem({ name, desc, badge, badgeColor, index }) {
  const cardRef = useRef(null)

  useEffect(() => {
    const el = cardRef.current
    if (!el) return

    const onMove = (e) => {
      const rect = el.getBoundingClientRect()
      const x = ((e.clientX - rect.left) / rect.width) * 100
      const y = ((e.clientY - rect.top) / rect.height) * 100
      el.style.setProperty("--gx", x + "%")
      el.style.setProperty("--gy", y + "%")
      el.style.setProperty("--gi", "1")
    }
    const onLeave = () => el.style.setProperty("--gi", "0")
    el.addEventListener("mousemove", onMove)
    el.addEventListener("mouseleave", onLeave)
    return () => { el.removeEventListener("mousemove", onMove); el.removeEventListener("mouseleave", onLeave) }
  }, [])

  return (
    <div ref={cardRef} className="card p-6">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-white font-mono font-bold text-lg">{name}</h3>
        <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold border ${badgeColor}`}>{badge}</span>
      </div>
      <p className="text-sm">{desc}</p>
    </div>
  )
}

export default function Modes() {
  return (
    <section id="modes" className="relative z-10 py-24 md:py-32">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">Eight Modes. One CLI.</h2>
          <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
            Each mode is a specialized tool. Most don't even need an LLM.
          </p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {modes.map((m, i) => <ModeItem key={m.name} {...m} index={i} />)}
        </div>
      </div>
    </section>
  )
}
