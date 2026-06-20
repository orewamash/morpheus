export default function Footer() {
  return (
    <footer className="relative z-10 border-t border-white/5 py-8">
      <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-[var(--color-text-muted)]">
        <div className="flex items-center gap-2">
          <span className="w-5 h-5 rounded bg-gradient-to-br from-cyan-400 to-cyan-600 flex items-center justify-center text-black font-bold text-xs">M</span>
          <span>Morpheus — Fully Local AI Code Agent</span>
        </div>
        <div className="flex items-center gap-6">
          <a href="https://github.com/orewamash/morpheus" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">GitHub</a>
          <a href="https://pypi.org/project/morpheus-cli/" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">PyPI</a>
          <span>v0.1.0</span>
        </div>
      </div>
    </footer>
  )
}
