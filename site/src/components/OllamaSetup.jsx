import { useState, useEffect, useRef } from "react"

const steps = [
  {
    cmd: "ollama pull mistral",
    label: "Pull a model (Mistral 7B recommended)",
    detail: "Works with any instruct-tuned model: llama3, codellama, phi4, deepseek-coder",
  },
  {
    cmd: "# Ollama auto-starts as a background service on Mac/Linux/Win",
    label: "No manual server start needed",
    detail: "Verify with: curl http://localhost:11434/api/tags",
  },
  {
    cmd: "morpheus narrator src/app.py",
    label: "Use an LLM-powered mode",
    detail: "Auto-detects Ollama at localhost:11434. Configure with .env if needed.",
  },
]

function SetupStep({ cmd, label, detail, index }) {
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
    <div ref={cardRef} className="card p-5">
      <div className="flex items-start gap-4">
        <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-300 font-mono text-sm font-bold">
          {index + 1}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-3">
            <code className={`text-sm font-mono truncate ${cmd.startsWith("#") ? "text-[var(--color-text-muted)]" : "text-white"}`}>{cmd}</code>
            {!cmd.startsWith("#") && (
              <button
                onClick={copy}
                className="flex-shrink-0 px-3 py-1 text-xs rounded-lg border border-white/10 hover:border-white/20 text-[var(--color-text-secondary)] hover:text-white transition-all cursor-pointer"
              >
                {copied ? "Copied!" : "Copy"}
              </button>
            )}
          </div>
          <p className="text-sm text-[var(--color-text-secondary)] mt-1">{label}</p>
          <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{detail}</p>
        </div>
      </div>
    </div>
  )
}

export default function OllamaSetup() {
  return (
    <section id="llm-setup" className="relative z-10 py-24 md:py-32">
      <div className="max-w-4xl mx-auto px-6">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-amber-400/20 bg-amber-400/5 text-amber-300 text-xs font-medium mb-4">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            Optional — Only for narrator / teach / oracle
          </div>
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">LLM Setup</h2>
          <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
            Three modes use AI. Get them running with one command.
          </p>
        </div>

        <div className="flex flex-col gap-3 mb-8">
          {steps.map((s, i) => <SetupStep key={s.cmd} {...s} index={i} />)}
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <div className="card p-5 text-center">
            <div className="text-2xl mb-2">📥</div>
            <h4 className="text-white font-semibold text-sm mb-2">1. Install Ollama</h4>
            <p className="text-xs leading-relaxed">
              Download from{" "}
              <a href="https://ollama.ai" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">ollama.ai</a>
              . One-click installer for macOS, Windows, and Linux.
            </p>
          </div>
          <div className="card p-5 text-center">
            <div className="text-2xl mb-2">🤖</div>
            <h4 className="text-white font-semibold text-sm mb-2">2. Pull a Model</h4>
            <p className="text-xs leading-relaxed">
              <code className="px-1 py-0.5 rounded bg-white/5 text-cyan-300 text-xs font-mono">ollama pull mistral</code>
              {" "}(~4GB). Or use llama3, phi4, deepseek-coder, etc.
            </p>
          </div>
          <div className="card p-5 text-center">
            <div className="text-2xl mb-2">⚡</div>
            <h4 className="text-white font-semibold text-sm mb-2">3. Run Morpheus</h4>
            <p className="text-xs leading-relaxed">
              <code className="px-1 py-0.5 rounded bg-white/5 text-cyan-300 text-xs font-mono">morpheus narrator .</code>
              {" "}— auto-connects. That's it. No config, no API keys.
            </p>
          </div>
        </div>

        <div className="mt-8 p-5 rounded-xl bg-white/[0.02] border border-white/5">
          <h4 className="text-white font-semibold text-sm mb-3">Configuration (optional)</h4>
          <div className="grid md:grid-cols-2 gap-4 text-xs">
            <div>
              <p className="text-[var(--color-text-muted)] mb-1">Custom host / model:</p>
              <code className="block px-3 py-2 rounded-lg bg-white/5 text-cyan-300 font-mono">
                MORPHEUS_LLM_BACKEND=ollama{'\n'}
                MORPHEUS_LLM_MODEL=codellama{'\n'}
                OLLAMA_HOST=http://192.168.1.5:11434
              </code>
            </div>
            <div>
              <p className="text-[var(--color-text-muted)] mb-1">Use OpenAI instead:</p>
              <code className="block px-3 py-2 rounded-lg bg-white/5 text-cyan-300 font-mono">
                MORPHEUS_LLM_BACKEND=openai{'\n'}
                OPENAI_API_KEY=sk-...{'\n'}
                MORPHEUS_LLM_MODEL=gpt-4o-mini
              </code>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
