import { useEffect, useRef } from "react"

const features = [
  {
    title: "Codebase Analysis",
    desc: "Map every module, dependency, and export. Detect circular dependencies, dead code, and architectural drift in seconds.",
    icon: "🔍", cols: "md:col-span-2 md:row-span-2", align: "left",
  },
  {
    title: "Test Generation",
    desc: "Generate unit & integration tests with real coverage. Works with your existing test framework and mocks your services.",
    icon: "🧪", cols: "md:col-span-2", align: "left",
  },
  {
    title: "Diff Reasoning",
    desc: "Understand what a PR actually changes. Morpheus explains the impact of every diff in plain English.",
    icon: "📋", align: "center",
  },
  {
    title: "Architecture Maps",
    desc: "Visualize your entire project structure. See how services, components, and data flow connect.",
    icon: "🏗️", align: "center",
  },
  {
    title: "Pattern Teaching",
    desc: "Learn your codebase like a senior dev. Morpheus explains patterns, conventions, and architecture decisions.",
    icon: "🎓", cols: "md:col-span-2", align: "left",
  },
  {
    title: "Fully Offline",
    desc: "Zero data leaves your machine. Ollama + local embeddings. No API keys, no telemetry, no cloud dependency.",
    icon: "🔒", cols: "md:col-span-2", align: "left",
  },
]

function FeatureCard({ icon, title, desc, cols, align, index }) {
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

  useEffect(() => {
    const el = cardRef.current
    if (!el) return

    const onMove = (e) => {
      const rect = el.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top
      const cx = rect.width / 2
      const cy = rect.height / 2
      const rx = ((y - cy) / cy) * -6
      const ry = ((x - cx) / cx) * 6
      el.style.transform = `perspective(800px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-4px)`
    }
    const onLeave = () => el.style.transform = "perspective(800px) rotateX(0deg) rotateY(0deg) translateY(0px)"
    el.addEventListener("mousemove", onMove)
    el.addEventListener("mouseleave", onLeave)
    return () => { el.removeEventListener("mousemove", onMove); el.removeEventListener("mouseleave", onLeave) }
  }, [])

  return (
    <div ref={cardRef} className={`card ${cols} flex flex-col ${align === "center" ? "items-center text-center" : ""}`}>
      <span className="text-4xl mb-4">{icon}</span>
      <h3 className="text-white text-xl font-semibold mb-3">{title}</h3>
      <p className={`text-sm ${align === "center" ? "max-w-[20ch]" : ""}`}>{desc}</p>
    </div>
  )
}

export default function Features() {
  return (
    <section id="features" className="relative z-10 py-24 md:py-32">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">Everything a Senior Engineer Does</h2>
          <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
            Seven modes. One CLI. No compromises on privacy or power.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 md:gap-5">
          {features.map((f, i) => (
            <FeatureCard key={f.title} {...f} index={i} />
          ))}
        </div>
      </div>
    </section>
  )
}
