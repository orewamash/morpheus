export default function Hero({ onGetStarted }) {
  return (
    <section className="relative z-10 pt-32 pb-20 md:pt-40 md:pb-28 text-center">
      <div className="max-w-4xl mx-auto px-6">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-cyan-400/20 bg-cyan-400/5 text-cyan-300 text-xs font-medium mb-6">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
          v0.1.0 — Fully Local AI Agent
        </div>

        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white leading-[1.1] mb-6">
          Your CLI Agent{" "}
          <span className="gradient-text">Beyond the Hype</span>
        </h1>

        <p className="text-lg md:text-xl text-[var(--color-text-secondary)] max-w-2xl mx-auto leading-relaxed mb-10">
          Morpheus analyzes codebases like a senior engineer — traces execution paths, generates tests, 
          teaches patterns, and maps architecture. All fully local. No API keys, no cloud, no data leaks.
        </p>

        <div className="flex items-center justify-center gap-4 mb-14">
          <button onClick={onGetStarted} className="glow-btn px-8 py-3.5 rounded-xl text-base cursor-pointer">Install Morpheus</button>
          <a
            href="#how-it-works"
            className="px-8 py-3.5 rounded-xl text-base font-medium text-[var(--color-text-secondary)] border border-white/10 hover:border-white/20 hover:text-white transition-all"
          >
            How It Works
          </a>
        </div>

        <div className="relative group">
          <div className="absolute -inset-6 bg-gradient-to-r from-cyan-500/10 via-transparent to-teal-500/10 rounded-3xl blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
          <div className="relative rounded-2xl border border-white/[0.06] bg-[rgba(5,5,15,0.6)] backdrop-blur-sm overflow-hidden shadow-2xl">
            <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-white/5 bg-[rgba(10,10,20,0.5)]">
              {["#ff5f57", "#ffbd2e", "#28c840"].map((c, i) => (
                <div key={i} className="w-3 h-3 rounded-full" style={{ backgroundColor: c }} />
              ))}
              <span className="ml-3 text-xs text-[var(--color-text-muted)] font-mono">zsh — morpheus analyze</span>
            </div>
            <pre className="p-5 md:p-7 text-left text-sm font-mono leading-relaxed overflow-x-auto">
              <code>
                <span className="text-green-400">$</span> <span className="text-cyan-300">morpheus</span> analyze src/components/{'\n'}
                <span className="text-white/70">  ✓ Analyzing 47 files...</span>{'\n'}
                <span className="text-white/70">  ✓ Building dependency graph</span>{'\n'}
                <span className="text-white/70">  ✓ Tracing 312 module relationships</span>{'\n\n'}
                <span className="text-orange-400">Analysis Complete</span>{'\n'}
                <span className="text-cyan-300">  ·</span> <span className="text-white/80">6 circular dependencies found</span>{'\n'}
                <span className="text-cyan-300">  ·</span> <span className="text-white/80">18 unused exports detected</span>{'\n'}
                <span className="text-cyan-300">  ·</span> <span className="text-white/80">Components: 23 props, 12 hooks, 47 utils</span>{'\n\n'}
                <span className="text-[var(--color-text-muted)]"># Recommendation: extract utils/format.ts into 2 modules</span>
              </code>
            </pre>
          </div>
        </div>
      </div>
    </section>
  )
}
