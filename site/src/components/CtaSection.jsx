export default function CtaSection({ onGetStarted }) {
  return (
    <section className="relative z-10 py-24 md:py-32">
      <div className="max-w-4xl mx-auto px-6 text-center">
        <div className="relative p-10 md:p-16 rounded-3xl border border-cyan-500/10 bg-gradient-to-br from-cyan-500/5 via-transparent to-teal-500/5 overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-teal-500/5 rounded-full blur-3xl" />
          <div className="relative">
            <h2 className="text-3xl md:text-5xl font-bold text-white mb-6 leading-[1.15]">
              Ready to See Through<br />
              <span className="gradient-text">Your Codebase?</span>
            </h2>
            <p className="text-lg text-[var(--color-text-secondary)] max-w-xl mx-auto mb-10">
              No sign-ups. No data sharing. Just a terminal and your code.
            </p>
            <div className="flex items-center justify-center gap-4">
              <button onClick={onGetStarted} className="glow-btn px-8 py-3.5 rounded-xl text-base cursor-pointer">
                Install Now
              </button>
              <a
                href="https://github.com/orewamash/morpheus"
                target="_blank"
                rel="noopener noreferrer"
                className="px-8 py-3.5 rounded-xl text-base font-medium text-[var(--color-text-secondary)] border border-white/10 hover:border-white/20 hover:text-white transition-all"
              >
                View on GitHub
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
