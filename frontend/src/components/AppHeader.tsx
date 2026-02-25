export function AppHeader() {
  return (
    <header className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
      <div>
        <h1 className="font-display text-5xl lg:text-6xl text-neon">ACRA AI</h1>
        <p className="text-slate-300 max-w-xl mt-3">
          Fast, rigorous code reviews with OWASP focus, performance tuning, and clear quality scoring.
        </p>
      </div>
    </header>
  );
}
