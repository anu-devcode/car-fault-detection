import { CalendarClock, Phone, Wrench } from 'lucide-react'
import styles from '../../styles/platform.module.css'

export const serviceNames = {
  inspection: 'Vehicle inspection',
  breakdown: 'Breakdown assistance',
  maintenance: 'Routine maintenance',
  tyres: 'Tyres and wheels',
  electrical: 'Electrical problem',
  other: 'Other service',
}

const labels = {
  requested: 'Awaiting reply',
  accepted: 'Accepted',
  declined: 'Declined',
  completed: 'Completed',
  cancelled: 'Cancelled',
}

export async function platform(path, body) {
  const response = await fetch(`/api/platform${path}`, {
    cache: 'no-store',
    ...(body === undefined
      ? {}
      : {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        }),
  })
  const result = await response.json().catch(() => null)
  if (!response.ok || !result) {
    const error = new Error(result?.detail || 'The workspace could not respond. Please try again.')
    error.status = response.status
    throw error
  }
  return result
}

export function Section({ id, title, summary, children }) {
  return (
    <section className={styles.section} id={id}>
      <header className={styles.sectionHeader}>
        <h2>{title}</h2>
        {summary && <p>{summary}</p>}
      </header>
      {children}
    </section>
  )
}

export function Stats({ items }) {
  return (
    <dl className={styles.stats}>
      {items.map(([label, value, Icon]) => (
        <div className={styles.stat} key={label}>
          <dt>
            <Icon size={18} aria-hidden="true" />
            {label}
          </dt>
          <dd>{value ?? 0}</dd>
        </div>
      ))}
    </dl>
  )
}

export function Requests({ entries, role, busy, action }) {
  if (!entries.length)
    return (
      <div className={styles.empty}>
        <CalendarClock size={24} aria-hidden="true" />
        <p>
          {role === 'driver'
            ? 'Help requests you send will appear here.'
            : 'Requests from drivers will appear here.'}
        </p>
      </div>
    )
  const allowed = (status) => {
    if (role === 'driver')
      return ['requested', 'accepted'].includes(status) ? [['cancelled', 'Cancel request']] : []
    if (status === 'requested')
      return [
        ['accepted', 'Accept'],
        ['declined', 'Decline'],
      ]
    return status === 'accepted' ? [['completed', 'Mark complete']] : []
  }
  return (
    <ul className={styles.requestList}>
      {entries.map((item) => (
        <li key={item.id}>
          <div className={styles.requestIcon}>
            <Wrench size={20} aria-hidden="true" />
          </div>
          <div className={styles.requestContent}>
            <div className={styles.requestTitle}>
              <h3>{serviceNames[item.service] || 'Assistance request'}</h3>
              <span className={styles.pill} data-state={item.status}>
                {labels[item.status]}
              </span>
            </div>
            <p className={styles.meta}>
              {item.counterpart} · {item.garage} ·{' '}
              <time dateTime={new Date(item.created_at * 1000).toISOString()}>
                {new Date(item.created_at * 1000).toLocaleDateString()}
              </time>
            </p>
            <p className={styles.requestDetails}>{item.details}</p>
            <div className={styles.actions}>
              {allowed(item.status).map(([status, label], index) => (
                <button
                  key={status}
                  className={role === 'mechanic' && index === 0 ? styles.primary : styles.secondary}
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    action(
                      () => platform(`/requests/${item.id}/status`, { status }),
                      status === 'completed' ? 'Request marked complete.' : 'Request updated.',
                    )
                  }
                >
                  {label}
                </button>
              ))}
              {role === 'driver' &&
                item.garage_phone &&
                ['requested', 'accepted'].includes(item.status) && (
                  <a className={styles.textAction} href={`tel:${item.garage_phone}`}>
                    <Phone size={15} aria-hidden="true" /> Call garage
                  </a>
                )}
              {role === 'mechanic' && item.callback && (
                <a className={styles.textAction} href={`tel:${item.callback}`}>
                  <Phone size={15} aria-hidden="true" /> Call driver
                </a>
              )}
            </div>
          </div>
        </li>
      ))}
    </ul>
  )
}
