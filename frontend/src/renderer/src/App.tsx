import { useMemo, useState } from 'react'

type DashboardMode = 'private' | 'public'
type DashboardCategory = 'all' | 'resume' | 'portfolio' | 'timeline' | 'heatmap' | 'showcase'

type DashboardCard = {
  id: string
  title: string
  category: Exclude<DashboardCategory, 'all'>
  status: 'ready' | 'coming-soon'
  description: string
}

const dashboardCards: DashboardCard[] = [
  {
    id: 'resume',
    title: 'One-Page Resume',
    category: 'resume',
    status: 'ready',
    description: 'Generate and review a concise one-page resume from analyzed projects.',
  },
  {
    id: 'portfolio',
    title: 'Web Portfolio',
    category: 'portfolio',
    status: 'ready',
    description: 'Assemble project summaries and evidence into portfolio-ready sections.',
  },
  {
    id: 'timeline',
    title: 'Skills Timeline',
    category: 'timeline',
    status: 'ready',
    description: 'Track learning progression and depth across projects over time.',
  },
  {
    id: 'heatmap',
    title: 'Project Activity Heatmap',
    category: 'heatmap',
    status: 'coming-soon',
    description: 'Visualize activity intensity and productivity trends.',
  },
  {
    id: 'showcase',
    title: 'Top 3 Project Showcase',
    category: 'showcase',
    status: 'coming-soon',
    description: 'Highlight top projects and evolution of key changes.',
  },
]

function App() {
  const [mode, setMode] = useState<DashboardMode>('private')
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<DashboardCategory>('all')

  const filteredCards = useMemo(() => {
    const lowered = query.trim().toLowerCase()
    return dashboardCards.filter((card) => {
      const matchesCategory = category === 'all' || card.category === category
      const matchesQuery =
        lowered.length === 0 ||
        card.title.toLowerCase().includes(lowered) ||
        card.description.toLowerCase().includes(lowered)
      return matchesCategory && matchesQuery
    })
  }, [category, query])

  return (
    <div className="app">
      <header className="app-header">
        <h1>Digital Work Artifact Miner</h1>
        <p className="subtitle">Team 14 — Capstone Project</p>
      </header>

      <main className="app-main">
        <section className="card" aria-label="dashboard-mode">
          <h2>Dashboard Mode</h2>
          <p>
            Private mode enables customization controls. Public mode limits interaction to search and filter.
          </p>
          <div className="mode-toggle" role="group" aria-label="Mode Toggle">
            <button
              className={`mode-btn ${mode === 'private' ? 'is-active' : ''}`}
              onClick={() => setMode('private')}
              aria-pressed={mode === 'private'}
            >
              Private
            </button>
            <button
              className={`mode-btn ${mode === 'public' ? 'is-active' : ''}`}
              onClick={() => setMode('public')}
              aria-pressed={mode === 'public'}
            >
              Public
            </button>
          </div>
          {mode === 'private' ? (
            <p className="mode-hint">Customization controls are enabled.</p>
          ) : (
            <p className="mode-hint">Customization controls are disabled in public mode.</p>
          )}
        </section>

        <section className="status-section" aria-label="search-filter">
          <h3>Search and Filter</h3>
          <div className="controls">
            <input
              className="input"
              type="text"
              placeholder="Search dashboard sections"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              aria-label="Search sections"
            />
            <select
              className="select"
              value={category}
              onChange={(event) => setCategory(event.target.value as DashboardCategory)}
              aria-label="Filter category"
            >
              <option value="all">All Categories</option>
              <option value="resume">Resume</option>
              <option value="portfolio">Portfolio</option>
              <option value="timeline">Timeline</option>
              <option value="heatmap">Heatmap</option>
              <option value="showcase">Showcase</option>
            </select>
          </div>
        </section>

        <section className="cards-grid" aria-label="dashboard-cards">
          {filteredCards.length === 0 ? (
            <p className="empty-state">No sections match your search/filter.</p>
          ) : (
            filteredCards.map((card) => (
              <article className="feature-card" key={card.id}>
                <div className="feature-head">
                  <h4>{card.title}</h4>
                  <span className={`pill ${card.status}`}>{card.status === 'ready' ? 'Ready' : 'Coming Soon'}</span>
                </div>
                <p>{card.description}</p>
                <button
                  className="action-btn"
                  disabled={mode === 'public' || card.status === 'coming-soon'}
                >
                  Customize
                </button>
              </article>
            ))
          )}
        </section>
      </main>

      <footer className="app-footer">
        <p>COSC 499 — Digital Work Artifact Miner</p>
      </footer>
    </div>
  )
}

export default App
