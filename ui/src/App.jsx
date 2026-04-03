import { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  `${window.location.protocol}//${window.location.hostname}:8001`

const starterProjects = [
  {
    title: 'Yoga Form Coach',
    projectDescription:
      "Build an at-home yoga form coach web app that uses the Gemini Live API to watch a user's live session, deliver spoken form cues through the user's active audio output, and save notes on what they did well, what to keep working on, and what they learned.",
    dataSource: 'data/yoga_form_coach_brief.md',
    dataStrategy: 'local',
  },
  {
    title: 'Yoga Research Mode',
    projectDescription:
      'Research best practices and competitor patterns for an at-home yoga form coach that uses live multimodal feedback.',
    dataSource: 'https://ai.google.dev/gemini-api/docs/live',
    dataStrategy: 'web',
  },
]

const initialForm = {
  projectDescription: starterProjects[0].projectDescription,
  dataSource: starterProjects[0].dataSource,
  dataStrategy: starterProjects[0].dataStrategy,
  useCache: true,
}

function prettyPrint(value) {
  if (typeof value === 'string') {
    return value
  }

  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

function App() {
  const [form, setForm] = useState(initialForm)
  const [serviceStatus, setServiceStatus] = useState('checking')
  const [serviceDetails, setServiceDetails] = useState('')
  const [pipelineStatus, setPipelineStatus] = useState('idle')
  const [pipelineValue, setPipelineValue] = useState('')
  const [runStatus, setRunStatus] = useState('idle')
  const [result, setResult] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadHealth() {
      try {
        const response = await fetch(`${API_BASE_URL}/health`)
        if (!response.ok) {
          throw new Error(`Health check failed with ${response.status}`)
        }

        const payload = await response.json()
        if (!cancelled) {
          setServiceStatus(payload.status || 'healthy')
          const worker = payload.backends?.worker
          const manager = payload.backends?.manager
          const evalLayer = payload.backends?.eval
          if (worker && manager && evalLayer) {
            setServiceDetails(
              `Worker ${worker.model} | Manager ${manager.model} | Eval ${evalLayer.model}`,
            )
          } else {
            setServiceDetails(`${payload.model} via ${payload.base_url}`)
          }
        }
      } catch (fetchError) {
        if (!cancelled) {
          setServiceStatus('offline')
          setServiceDetails(fetchError.message)
        }
      }
    }

    async function loadPipelineStatus() {
      try {
        const response = await fetch(`${API_BASE_URL}/status/pipeline`)
        if (response.status === 404) {
          if (!cancelled) {
            setPipelineStatus('idle')
            setPipelineValue('No runs yet.')
          }
          return
        }

        if (!response.ok) {
          throw new Error(`Status request failed with ${response.status}`)
        }

        const payload = await response.json()
        if (!cancelled) {
          setPipelineStatus(payload.status || 'unknown')
          setPipelineValue(payload.value || '')
        }
      } catch (fetchError) {
        if (!cancelled) {
          setPipelineStatus('unavailable')
          setPipelineValue(fetchError.message)
        }
      }
    }

    loadHealth()
    loadPipelineStatus()

    const intervalId = window.setInterval(() => {
      loadHealth()
      loadPipelineStatus()
    }, 4000)

    return () => {
      cancelled = true
      window.clearInterval(intervalId)
    }
  }, [])

  function applyStarter(project) {
    setForm({
      projectDescription: project.projectDescription,
      dataSource: project.dataSource,
      dataStrategy: project.dataStrategy,
      useCache: true,
    })
  }

  function updateField(event) {
    const { name, type, checked, value } = event.target
    setForm((current) => ({
      ...current,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setRunStatus('running')
    setError('')
    setResult('')
    setPipelineStatus('running')
    setPipelineValue(form.projectDescription)

    try {
      const response = await fetch(`${API_BASE_URL}/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data_source: form.dataSource,
          project_description: form.projectDescription,
          data_strategy: form.dataStrategy,
          use_cache: form.useCache,
        }),
      })

      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.detail || `Run failed with ${response.status}`)
      }

      setRunStatus(payload.cached ? 'cached' : 'complete')
      setPipelineStatus(payload.status || 'complete')
      setPipelineValue(prettyPrint(payload.result))
      setResult(prettyPrint(payload.result))
    } catch (submitError) {
      setRunStatus('failed')
      setPipelineStatus('failed')
      setPipelineValue(submitError.message)
      setError(submitError.message)
    }
  }

  return (
    <main className="shell">
      <section className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">Hackathon Orchestrator</p>
          <h1>Start the builder with a live yoga form coach brief.</h1>
          <p className="lead">
            This UI sends a product brief to the FastAPI orchestrator, monitors service health,
            and shows the latest implementation plan from the crew.
          </p>
        </div>

        <div className="status-grid">
          <article className="status-card">
            <span className="status-label">API</span>
            <strong className={`status-value is-${serviceStatus}`}>{serviceStatus}</strong>
            <p>{serviceDetails || 'Waiting for backend response.'}</p>
          </article>
          <article className="status-card">
            <span className="status-label">Pipeline</span>
            <strong className={`status-value is-${pipelineStatus}`}>{pipelineStatus}</strong>
            <p>{pipelineValue || 'Submit a run to initialize the pipeline.'}</p>
          </article>
          <article className="status-card">
            <span className="status-label">API Base</span>
            <strong className="status-value mono">{API_BASE_URL}</strong>
            <p>Override with <code>VITE_API_BASE_URL</code> if needed.</p>
          </article>
        </div>
      </section>

      <section className="workspace">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Launch Run</p>
              <h2>Project Input</h2>
            </div>
            <div className="starter-list">
              {starterProjects.map((project) => (
                <button
                  key={project.title}
                  className="starter-chip"
                  type="button"
                  onClick={() => applyStarter(project)}
                >
                  {project.title}
                </button>
              ))}
            </div>
          </div>

          <form className="run-form" onSubmit={handleSubmit}>
            <label>
              <span>Project idea</span>
              <textarea
                name="projectDescription"
                rows="4"
                value={form.projectDescription}
                onChange={updateField}
                placeholder="Describe the product you want the builder to generate."
                required
              />
            </label>

            <label>
              <span>Data source</span>
              <input
                name="dataSource"
                type="text"
                value={form.dataSource}
                onChange={updateField}
                placeholder="Local file path or URL"
                required
              />
            </label>

            <div className="form-row">
              <label>
                <span>Strategy</span>
                <select name="dataStrategy" value={form.dataStrategy} onChange={updateField}>
                  <option value="local">Local file</option>
                  <option value="web">Web scrape</option>
                </select>
              </label>

              <label className="checkbox">
                <input
                  name="useCache"
                  type="checkbox"
                  checked={form.useCache}
                  onChange={updateField}
                />
                <span>Use Redis cache when available</span>
              </label>
            </div>

            <button className="submit-button" type="submit" disabled={runStatus === 'running'}>
              {runStatus === 'running' ? 'Running agents...' : 'Start builder'}
            </button>
          </form>

          {error ? <p className="message error">{error}</p> : null}
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Latest Output</p>
              <h2>Builder Result</h2>
            </div>
            <span className={`result-pill is-${runStatus}`}>{runStatus}</span>
          </div>

          <pre className="result-box">{result || 'No output yet.'}</pre>
        </article>
      </section>
    </main>
  )
}

export default App
