import { useCallback, useEffect, useMemo, useState } from 'react'
import './App.css'
import {
  STATUSES,
  createApplication,
  deleteApplication,
  listApplications,
  updateApplicationStatus,
  type Application,
  type ApplicationStatus,
} from './api'

const filters = ['All', ...STATUSES] as const

type Connection = 'connecting' | 'online' | 'offline'

function getGreeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

// Parse YYYY-MM-DD as a local date (new Date('YYYY-MM-DD') is UTC and can
// show the previous day in US timezones).
function formatDate(value: string) {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function logoClass(company: string) {
  const letter = company.toLowerCase().replace(/[^a-z]/g, '')[0]
  return letter ? `logo-${letter}` : ''
}

const emptyForm = { company: '', role: '', location: '' }

function App() {
  const [applications, setApplications] = useState<Application[]>([])
  const [loading, setLoading] = useState(true)
  const [connection, setConnection] = useState<Connection>('connecting')
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<(typeof filters)[number]>('All')
  const [activeNav, setActiveNav] = useState<'dashboard' | 'applications'>(
    'dashboard',
  )
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)

  const greeting = useMemo(getGreeting, [])

  // Fetch applications from the FastAPI backend.
  const loadApplications = useCallback(async (signal?: AbortSignal) => {
    setLoading(true)
    setConnection('connecting')
    try {
      const data = await listApplications(signal)
      setApplications(data)
      setConnection('online')
      setError('')
    } catch (err) {
      if (signal?.aborted) return
      console.error('Failed to load applications:', err)
      setConnection('offline')
      setError(
        'Could not connect to the API. Check that the backend is running.',
      )
    } finally {
      if (!signal?.aborted) setLoading(false)
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    void loadApplications(controller.signal)
    return () => controller.abort()
  }, [loadApplications])

  // Highlight the sidebar link for the section currently in view.
  useEffect(() => {
    const panel = document.getElementById('applications')
    if (!panel) return

    const observer = new IntersectionObserver(
      ([entry]) =>
        setActiveNav(entry.isIntersecting ? 'applications' : 'dashboard'),
      { threshold: 0.4 },
    )
    observer.observe(panel)
    return () => observer.disconnect()
  }, [])

  // Search and filter applications.
  const filteredApplications = useMemo(() => {
    const query = search.trim().toLowerCase()
    return applications.filter((application) => {
      const matchesSearch =
        `${application.company} ${application.role} ${application.location}`
          .toLowerCase()
          .includes(query)

      return (
        matchesSearch && (filter === 'All' || application.status === filter)
      )
    })
  }, [applications, search, filter])

  // Calculate dashboard statistics.
  const counts = useMemo(() => {
    const count = (status: ApplicationStatus) =>
      applications.filter((app) => app.status === status).length
    const applied = count('Applied')
    const interviews = count('Interview')
    return {
      total: applications.length,
      inProgress: applied + interviews,
      interviews,
      offers: count('Offer'),
    }
  }, [applications])

  // Optimistically update the status, then persist it. Roll back on failure.
  async function updateStatus(id: number, status: ApplicationStatus) {
    const previous = applications.find((app) => app.id === id)?.status
    if (!previous || previous === status) return

    const setStatus = (value: ApplicationStatus) =>
      setApplications((current) =>
        current.map((app) =>
          app.id === id ? { ...app, status: value } : app,
        ),
      )

    setStatus(status)
    try {
      await updateApplicationStatus(id, status)
      setError('')
    } catch (err) {
      console.error('Failed to update status:', err)
      setStatus(previous)
      setError('Could not save the status change, so it was reverted.')
    }
  }

  async function removeApplication(application: Application) {
    if (
      !window.confirm(
        `Delete ${application.company} - ${application.role}?`,
      )
    ) {
      return
    }

    try {
      await deleteApplication(application.id)
      setApplications((current) =>
        current.filter((app) => app.id !== application.id),
      )
      setError('')
    } catch (err) {
      console.error('Failed to delete application:', err)
      setError('Could not delete the application.')
    }
  }

  function closeForm() {
    setShowForm(false)
    setForm(emptyForm)
  }

  async function submitForm(event: React.FormEvent) {
    event.preventDefault()
    const company = form.company.trim()
    const role = form.role.trim()
    if (!company || !role) return

    setSaving(true)
    try {
      const created = await createApplication({
        company,
        role,
        location: form.location.trim() || undefined,
      })
      setApplications((current) => [created, ...current])
      setError('')
      closeForm()
    } catch (err) {
      console.error('Failed to add application:', err)
      setError('Could not save the application. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const connectionLabel =
    connection === 'online'
      ? 'API connected'
      : connection === 'offline'
        ? 'API offline'
        : 'Connecting...'

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#dashboard">
          <span className="brand-mark">A</span>
          <span>
            applyflow<span className="brand-period">.</span>
          </span>
        </a>

        <div className="sidebar-label">WORKSPACE</div>

        <nav className="navigation">
          <a
            className={`nav-link ${activeNav === 'dashboard' ? 'active' : ''}`}
            href="#dashboard"
            aria-current={activeNav === 'dashboard' ? 'page' : undefined}
          >
            <span>▦</span> Dashboard
          </a>
          <a
            className={`nav-link ${activeNav === 'applications' ? 'active' : ''}`}
            href="#applications"
            aria-current={activeNav === 'applications' ? 'page' : undefined}
          >
            <span>▤</span> Applications
          </a>
        </nav>

        <div className="sidebar-bottom">
          <div className="upgrade-card">
            <div className="upgrade-icon">✦</div>
            <strong>Your next opportunity starts here.</strong>
            <p>Stay organized. Keep moving forward.</p>
          </div>

          <div className="profile">
            <div className="avatar">F</div>
            <div className="profile-copy">
              <strong>My workspace</strong>
              <span>Free plan</span>
            </div>
            <span className="profile-menu">···</span>
          </div>
        </div>
      </aside>

      <main className="main-content" id="dashboard">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> Dashboard
          </div>
          <div className="topbar-right">
            <span className={`live-dot ${connection}`} />
            {connectionLabel}
            <div className="top-avatar">F</div>
          </div>
        </header>

        <section className="page-heading">
          <div>
            <div className="eyebrow">YOUR CAREER, IN MOTION</div>
            <h1>
              {greeting} <span className="wave">✳</span>
            </h1>
            <p className="page-subtitle">
              Every application gets you one step closer. Here's your progress.
            </p>
          </div>

          <button
            className="primary-button"
            onClick={() => setShowForm(true)}
          >
            <span>＋</span> Add application
          </button>
        </section>

        <section className="stats-grid" aria-label="Application statistics">
          <article className="stat-card">
            <div className="stat-top">
              <span>Total applications</span>
              <span className="stat-icon purple">▤</span>
            </div>
            <div className="stat-number">{counts.total}</div>
            <div className="stat-foot">
              <span className="trend">↗</span> Your job search at a glance
            </div>
          </article>

          <article className="stat-card">
            <div className="stat-top">
              <span>In progress</span>
              <span className="stat-icon blue">◷</span>
            </div>
            <div className="stat-number">{counts.inProgress}</div>
            <div className="stat-foot">Applied or interviewing</div>
          </article>

          <article className="stat-card">
            <div className="stat-top">
              <span>Interviews</span>
              <span className="stat-icon orange">↗</span>
            </div>
            <div className="stat-number">{counts.interviews}</div>
            <div className="stat-foot">Opportunities to shine</div>
          </article>

          <article className="stat-card">
            <div className="stat-top">
              <span>Offers</span>
              <span className="stat-icon green">✦</span>
            </div>
            <div className="stat-number">{counts.offers}</div>
            <div className="stat-foot">The goal is getting closer</div>
          </article>
        </section>

        <section className="applications-panel" id="applications">
          {loading && <p className="api-message">Loading applications...</p>}

          {error && (
            <div className="api-error" role="alert">
              <span>{error}</span>
              {connection === 'offline' && (
                <button
                  className="retry-button"
                  onClick={() => void loadApplications()}
                >
                  Retry
                </button>
              )}
            </div>
          )}

          <div className="panel-heading">
            <div>
              <h2>Your applications</h2>
              <p>Keep track of every opportunity in one place.</p>
            </div>
            <span className="application-count">
              {filteredApplications.length} records
            </span>
          </div>

          <div className="toolbar">
            <label className="search-box">
              <span>⌕</span>
              <input
                aria-label="Search applications"
                placeholder="Search company, role, location..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </label>

            <div className="filter-list" role="group" aria-label="Filter by status">
              {filters.map((item) => (
                <button
                  key={item}
                  className={`filter-button ${
                    filter === item ? 'selected' : ''
                  }`}
                  aria-pressed={filter === item}
                  onClick={() => setFilter(item)}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>COMPANY & ROLE</th>
                  <th>LOCATION</th>
                  <th>STATUS</th>
                  <th>DATE ADDED</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>

              <tbody>
                {filteredApplications.map((application) => (
                  <tr key={application.id}>
                    <td>
                      <div className="company-cell">
                        <div
                          className={`company-logo ${logoClass(application.company)}`}
                        >
                          {application.company[0]}
                        </div>
                        <div className="company-copy">
                          <strong>{application.company}</strong>
                          <span>{application.role}</span>
                        </div>
                      </div>
                    </td>

                    <td className="location-cell">{application.location}</td>

                    <td>
                      <select
                        className={`status-select status-${application.status.toLowerCase()}`}
                        aria-label={`Status for ${application.company}`}
                        value={application.status}
                        onChange={(event) =>
                          void updateStatus(
                            application.id,
                            event.target.value as ApplicationStatus,
                          )
                        }
                      >
                        {STATUSES.map((status) => (
                          <option key={status} value={status}>
                            {status}
                          </option>
                        ))}
                      </select>
                    </td>

                    <td className="date-cell">
                      {formatDate(application.date_added)}
                    </td>

                    <td className="actions-cell">
                      <button
                        className="icon-button"
                        aria-label={`Delete ${application.company}`}
                        onClick={() => void removeApplication(application)}
                      >
                        ✕
                      </button>
                    </td>
                  </tr>
                ))}

                {!loading && filteredApplications.length === 0 && (
                  <tr>
                    <td className="empty-state" colSpan={5}>
                      {connection === 'offline'
                        ? 'Applications could not be loaded.'
                        : applications.length === 0
                          ? 'No applications yet. Add your first one!'
                          : 'No applications match your search. Try another filter.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="panel-footer">
            <span>
              Showing {filteredApplications.length} of {applications.length}{' '}
              applications
            </span>
            <span>
              Built for your next move <span className="footer-star">✦</span>
            </span>
          </div>
        </section>

        <footer className="page-footer">
          Small steps. Big opportunities.
          <span>Made with intention ✦</span>
        </footer>
      </main>

      {showForm && (
        <div
          className="modal-backdrop"
          onClick={closeForm}
          onKeyDown={(event) => event.key === 'Escape' && closeForm()}
        >
          <form
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="add-title"
            onClick={(event) => event.stopPropagation()}
            onSubmit={(event) => void submitForm(event)}
          >
            <h2 id="add-title">Add application</h2>

            <label>
              Company
              <input
                autoFocus
                required
                maxLength={120}
                value={form.company}
                onChange={(event) =>
                  setForm({ ...form, company: event.target.value })
                }
              />
            </label>

            <label>
              Job title
              <input
                required
                maxLength={160}
                value={form.role}
                onChange={(event) =>
                  setForm({ ...form, role: event.target.value })
                }
              />
            </label>

            <label>
              Location <small>(optional)</small>
              <input
                maxLength={120}
                value={form.location}
                onChange={(event) =>
                  setForm({ ...form, location: event.target.value })
                }
              />
            </label>

            <div className="modal-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={closeForm}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="primary-button"
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Add application'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}

export default App
