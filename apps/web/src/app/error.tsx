"use client";

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="page-shell">
      <section className="status-panel" role="alert">
        <h1>Something went wrong</h1>
        <p>The page could not load its current status.</p>
        <button className="status-action" type="button" onClick={() => reset()}>Try again</button>
      </section>
    </main>
  );
}
