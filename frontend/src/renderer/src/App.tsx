import React, { useState } from 'react'
import SkillsTimeline from './components/SkillsTimeline'
import './App.css'

const App: React.FC = () => {
  const [isPrivate, setIsPrivate] = useState(true)

  return (
    <div className="app">
      <header className="app-header">
        <h1>Digital Work Artifact Miner</h1>
        <div className="mode-controls">
          <button 
            className={`mode-btn ${isPrivate ? 'active' : ''}`}
            onClick={() => setIsPrivate(true)}
          >
            Private
          </button>
          <button 
            className={`mode-btn ${!isPrivate ? 'active' : ''}`}
            onClick={() => setIsPrivate(false)}
          >
            Public
          </button>
        </div>
      </header>
      <main className="app-main">
        <div className="dashboard-section">
          <h2>Skills Timeline</h2>
          <div className="section-status">Ready</div>
          <SkillsTimeline />
        </div>
      </main>
    </div>
  )
}

export default App
