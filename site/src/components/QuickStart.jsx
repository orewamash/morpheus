import { useState, useEffect, useRef } from "react"

const steps = [
  { cmd: "pip install morpheus-cli", label: "Install" },
  { cmd: "morpheus analyze .", label: "Analyze any project" },
  { cmd: "morpheus map .", label: "Generate a dependency map" },
  { cmd: "morpheus diff main..feature", label: "Understand a PR diff" },
]

function StepCard({ cmd, label, index }) {
  const cardRef = useRef(null)
  const [copied, setCopied] = useState(false)

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

  const copy = () => {
    navigator.clipboard.writeText(cmd)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div ref={cardRef} className="card p-5 flex items-center justify-between gap-4">
      <div className="flex items-center gap-4">
        <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-300 font-mono text-sm font-bold">
          {index + 1}
        </span>
        <div>
          <code className="text-white font-mono text-sm">{cmd}</code>
          <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{label}</p>
        </div>
      </div>
      <button
        onClick={copy}
        className="flex-shrink-0 px-3 py-1.5 text-xs rounded-lg border border-white/10 hover:border-white/20 text-[var(--color-text-secondary)] hover:text-white transition-all cursor-pointer"
      >
        {copied ? "Copied!" : "Copy"}
      </button>
    </div>
  )
}

export default function QuickStart() {
  return (
    <section id="quick-start" className="relative z-10 py-24 md:py-32">
      <div className="max-w-3xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">Get Started in 10 Seconds</h2>
          <p className="text-lg text-[var(--color-text-secondary)]">
            One pip install. Zero configuration. Instant analysis.
          </p>
        </div>
        <div className="flex flex-col gap-3">
          {steps.map((s, i) => <StepCard key={s.cmd} {...s} index={i} />)}
        </div>
      </div>
    </section>
  )
}
