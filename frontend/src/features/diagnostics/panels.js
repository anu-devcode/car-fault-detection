import { motion } from 'framer-motion'
import { Activity, BarChart3 } from 'lucide-react'
import { formatConfidence, sessionStatistics } from '../../lib/metrics.mjs'

export function ResultCard({ result }) {
  const confidence = formatConfidence(result?.confidence)
  return (
    <section className="control-card" aria-label="Analysis result">
      <div className="hud-title">
        <BarChart3 size={16} /> Analysis Result
      </div>
      {result ? (
        <div className="diag-result">
          <div className="diag-label">{result.is_normal ? 'Normal pattern' : 'Fault pattern'}</div>
          <div className="diag-value">{result.fault_class}</div>
          <p>{result.location}</p>
          <div className="hud-title">Model confidence</div>
          <div className="diag-value" style={{ fontSize: '1.5rem' }}>
            {confidence}
          </div>
          <p className="status-note">
            Model confidence is not diagnostic accuracy. This research prototype does not establish
            whether a vehicle is safe to drive.
          </p>
        </div>
      ) : (
        <div className="empty-panel">
          <Activity size={48} />
          <p>Waiting for Sound</p>
        </div>
      )}
    </section>
  )
}

export function StatisticsPanel({ history, modelReady }) {
  const stats = sessionStatistics(history)
  const metrics = [
    ['Checks this session', stats.total],
    ['Mean model confidence', stats.meanConfidence],
    ['Mean request time', stats.meanLatency],
    ['Model status', modelReady ? 'Ready' : 'Unavailable'],
  ]
  return (
    <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="visualizer-panel">
      <h1>System Statistics</h1>
      <div className="control-card session-metrics">
        {metrics.map(([label, value]) => (
          <div key={label}>
            <div className="diag-label">{label}</div>
            <div className="diag-value" style={{ fontSize: '1.5rem' }}>
              {value}
            </div>
          </div>
        ))}
      </div>
      <p className="status-note">
        Statistics describe successful requests in this browser session. Model accuracy and service
        uptime have not been measured here.
      </p>
    </motion.section>
  )
}

export function RecordsPanel({ history }) {
  return (
    <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="visualizer-panel">
      <h1>Session Records</h1>
      <p className="status-note">Records stay in memory and clear when this page reloads.</p>
      {history.length ? (
        history.map((item) => (
          <article key={item.id} className="control-card record-row">
            <div>
              <strong>{item.class}</strong>
              <p>{item.date}</p>
            </div>
            <div>{item.system}</div>
            <div>Confidence: {item.confidence}</div>
          </article>
        ))
      ) : (
        <div className="control-card empty-panel">No Records Available</div>
      )}
    </motion.section>
  )
}

export function SettingsPanel({ theme, toggleTheme, modelReady }) {
  return (
    <section className="visualizer-panel">
      <h1>App Settings</h1>
      <div className="control-card">
        <div className="hud-title">Appearance</div>
        <button className="btn-cyber" onClick={toggleTheme}>
          Switch to {theme === 'dark' ? 'light' : 'dark'} mode
        </button>
      </div>
      <div className="control-card">
        <div className="hud-title">Prediction service</div>
        <p>
          {modelReady ? 'Model ready at the last health check.' : 'Prediction service unavailable.'}
        </p>
        <p className="status-note">
          Model sensitivity and upload encryption are not configurable from this dashboard.
        </p>
      </div>
    </section>
  )
}
