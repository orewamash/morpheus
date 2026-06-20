import { useEffect, useRef } from "react"

const steps = [
  { num: "01", title: "Trace", desc: "Records every function call, import resolution, and module dependency as your code runs — building a live map of execution flow.", color: "from-cyan-500 to-cyan-600" },
  { num: "02", title: "Analyze", desc: "Walks the dependency graph to compute metrics: coupling, cohesion, cyclomatic complexity, maintainability index, and architectural smells.", color: "from-cyan-400 to-teal-500" },
  { num: "03", title: "Compress", desc: "Structures findings into a compact, LLM-ready representation — so the AI gets perfect context without the 200K token firehose.", color: "from-teal-400 to-cyan-500" },
  { num: "04", title: "Act", desc: "Generates tests, diffs, explanations, or architecture maps. Each mode specializes in one output — fast, focused, predictable.", color: "from-cyan-600 to-teal-500" },
]

function StepCard({ num, title, desc, color, index }) {
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
    <div ref={cardRef} className="card flex gap-6 items-start">
      <div className={`flex-shrink-0 w-14 h-14 rounded-2xl bg-gradient-to-br ${color} flex items-center justify-center text-white font-bold text-2xl shadow-lg`}>
        {num}
      </div>
      <div>
        <h3 className="text-white text-xl font-semibold mb-2">{title}</h3>
        <p className="text-sm leading-relaxed">{desc}</p>
      </div>
    </div>
  )
}

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="relative z-10 py-24 md:py-32">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">How It Works</h2>
          <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
            A four-stage pipeline that turns messy codebases into actionable intelligence.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-5 mb-16">
          {steps.map((s, i) => <StepCard key={s.num} {...s} index={i} />)}
        </div>

        <div className="card p-8 md:p-10">
          <h3 className="text-white text-xl font-semibold mb-6 text-center">The LLM Dependency</h3>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h4 className="text-white font-medium mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-red-400" />
                Needs Ollama (narrator, teach, oracle)
              </h4>
              <p className="text-sm leading-relaxed">
                These modes send a structured prompt to your local Ollama instance at{" "}
                <code className="px-1.5 py-0.5 rounded bg-white/5 text-cyan-300 text-xs font-mono">http://localhost:11434/api/generate</code>.
                The prompt includes the compressed code graph, the user's intent, and a mode-specific
                instruction template. Mistral (7B) or any instruct-tuned model works.
              </p>
            </div>
            <div>
              <h4 className="text-white font-medium mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-400" />
                No LLM Needed (spy, prophecy, analyze, diff, map)
              </h4>
              <p className="text-sm leading-relaxed">
                These modes are purely algorithmic. They traverse the AST and dependency graph
                using Python's <code className="px-1.5 py-0.5 rounded bg-white/5 text-cyan-300 text-xs font-mono">ast</code>,{" "}
                <code className="px-1.5 py-0.5 rounded bg-white/5 text-cyan-300 text-xs font-mono">networkx</code>, and custom graph
                traversal logic. Results are computed locally with zero model inference — making
                them instant and free.
              </p>
            </div>
          </div>
          <div className="mt-6 p-4 rounded-xl bg-white/[0.02] border border-white/5 text-xs text-[var(--color-text-muted)] leading-relaxed">
            <span className="text-cyan-300 font-semibold">Architecture:</span> After trace/analyze/compress, the structured data
            either feeds an LLM prompt (narrator, teach, oracle) or directly generates output
            (spy, prophecy, analyze, diff, map). The pipeline is{" "}
            <span className="text-white">exactly the same up to the Act stage</span> — only the final
            output generator differs.
          </div>
        </div>
      </div>
    </section>
  )
}
