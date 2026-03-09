function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Digital Work Artifact Miner</h1>
        <p className="subtitle">Team 14 — Capstone Project</p>
      </header>
      <main className="app-main">
        <div className="card">
          <h2>Welcome</h2>
          <p>
            Privacy-first pipeline that scans approved folders, normalizes
            artifacts locally, and produces portfolio-ready insights.
          </p>
        </div>
        <div className="status-section">
          <h3>Quick Actions</h3>
          <div className="actions">
            <button className="action-btn" disabled>
              Upload Project
            </button>
            <button className="action-btn" disabled>
              View Projects
            </button>
            <button className="action-btn" disabled>
              Generate Report
            </button>
          </div>
          <p className="hint">Feature integrations coming soon.</p>
        </div>
      </main>
      <footer className="app-footer">
        <p>COSC 499 — Digital Work Artifact Miner</p>
      </footer>
    </div>
  )
}

export default App
