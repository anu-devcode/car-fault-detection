import {
  Building2,
  CarFront,
  ClipboardList,
  LifeBuoy,
  LogOut,
  Radio,
  RefreshCw,
  ShieldCheck,
  Wrench,
} from 'lucide-react'
import Head from 'next/head'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import AdminWorkspace from '../features/platform/AdminWorkspace'
import DriverWorkspace from '../features/platform/DriverWorkspace'
import MechanicWorkspace from '../features/platform/MechanicWorkspace'
import { platform } from '../features/platform/shared'
import styles from '../styles/platform.module.css'

const roles = {
  driver: {
    label: 'Driver workspace',
    links: [
      ['directory', 'Find a garage', Building2],
      ['requests', 'My requests', ClipboardList],
    ],
    Workspace: DriverWorkspace,
  },
  mechanic: {
    label: 'Mechanic workspace',
    links: [
      ['availability', 'Availability', Radio],
      ['requests', 'Assigned requests', ClipboardList],
    ],
    Workspace: MechanicWorkspace,
  },
  admin: {
    label: 'Admin workspace',
    links: [
      ['directory', 'Garage directory', Building2],
      ['mechanics', 'Mechanic access', ShieldCheck],
    ],
    Workspace: AdminWorkspace,
  },
}

function Brand() {
  return (
    <Link href="/hub" className={styles.brand}>
      <span className={styles.brandIcon}>
        <CarFront size={22} aria-hidden="true" />
      </span>{' '}
      Car Care
    </Link>
  )
}

function Access({ busy, error, submit }) {
  const [mode, setMode] = useState('login')
  const creating = mode !== 'login'
  const invited = mode === 'invite'
  return (
    <div className={styles.accessLayout}>
      <div className={styles.accessIntro}>
        <Brand />
        <div>
          <h1>Car care, closer to home.</h1>
          <p>Find a garage, talk to a mechanic, and keep track of the help you request.</p>
        </div>
        <Link href="/hub" className={styles.accessLink}>
          <LifeBuoy size={17} aria-hidden="true" /> Go to the Car Care hub
        </Link>
      </div>
      <main className={styles.accessMain}>
        <div className={styles.accessCard}>
          <h2>
            {invited
              ? 'Accept a mechanic invitation'
              : creating
                ? 'Create a driver account'
                : 'Sign in'}
          </h2>
          <p>
            {invited
              ? 'Use the email and code provided by your administrator.'
              : creating
                ? 'Start finding garages and tracking requests.'
                : 'Open your Car Care workspace.'}
          </p>
          {error && (
            <p className={styles.error} role="alert">
              {error}
            </p>
          )}
          <form
            className={styles.accessForm}
            key={mode}
            onSubmit={(event) => {
              event.preventDefault()
              const fields = new FormData(event.currentTarget)
              const payload = { email: fields.get('email'), password: fields.get('password') }
              if (creating) payload.name = fields.get('name')
              if (invited) payload.invite = fields.get('invite').trim()
              submit(`/access/${creating ? 'register' : 'login'}`, payload)
            }}
          >
            {creating && (
              <label>
                Full name
                <input name="name" autoComplete="name" required minLength={2} maxLength={80} />
              </label>
            )}
            <label>
              Email
              <input name="email" type="email" autoComplete="username" required maxLength={254} />
            </label>
            {invited && (
              <label>
                Invitation code
                <input name="invite" autoComplete="off" required minLength={43} maxLength={43} />
              </label>
            )}
            <label>
              Password
              <input
                name="password"
                type="password"
                autoComplete={creating ? 'new-password' : 'current-password'}
                minLength={creating ? 12 : 1}
                maxLength={128}
                required
              />
              {creating && <small>Use at least 12 characters.</small>}
            </label>
            <button className={styles.primary} disabled={busy}>
              {busy ? 'Working…' : creating ? 'Create account' : 'Sign in'}
            </button>
          </form>
          <div className={styles.accessSwitch}>
            {mode !== 'login' && (
              <button type="button" disabled={busy} onClick={() => setMode('login')}>
                Sign in
              </button>
            )}
            {mode !== 'register' && (
              <button type="button" disabled={busy} onClick={() => setMode('register')}>
                Create a driver account
              </button>
            )}
            {mode !== 'invite' && (
              <button type="button" disabled={busy} onClick={() => setMode('invite')}>
                I have a mechanic invitation
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    let active = true
    platform('/workspace')
      .then((result) => {
        if (active) setData(result)
      })
      .catch((err) => {
        if (active && err.status !== 401) setError(err.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  async function action(operation, message, signOut = false) {
    if (busy) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await operation()
      if (signOut) setData(null)
      else setData(await platform('/workspace'))
      if (message) setNotice(message)
    } catch (err) {
      if (err.status === 401 && data) setData(null)
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const account = data?.account
  const role = account && roles[account.role]
  const Workspace = role?.Workspace
  return (
    <div className={styles.app}>
      <Head>
        <title>{role ? `${role.label} · Car Care` : 'Sign in · Car Care'}</title>
      </Head>
      {loading ? (
        <main className={styles.loading}>
          <CarFront size={28} />
          <p role="status">Opening Car Care…</p>
        </main>
      ) : !Workspace ? (
        <Access
          busy={busy}
          error={error}
          submit={(path, body) => action(() => platform(path, body))}
        />
      ) : (
        <div className={styles.shell}>
          <aside className={styles.sidebar}>
            <Brand />
            <nav aria-label={role.label}>
              {role.links.map(([id, label, Icon]) => (
                <a key={id} href={`#${id}`}>
                  <Icon size={18} aria-hidden="true" />
                  {label}
                </a>
              ))}
              <Link href="/hub">
                <LifeBuoy size={18} aria-hidden="true" /> Car Care hub
              </Link>
            </nav>
            <button
              className={styles.signout}
              type="button"
              disabled={busy}
              onClick={() => action(() => platform('/access/logout', {}), '', true)}
            >
              <LogOut size={18} aria-hidden="true" /> Sign out
            </button>
          </aside>
          <main className={styles.main}>
            <header className={styles.top}>
              <div className={styles.workspaceName}>
                <Wrench size={17} aria-hidden="true" />
                {role.label}
              </div>
              <div className={styles.user}>
                <span>{account.name}</span>
                <span className={styles.avatar} aria-hidden="true">
                  {account.name.trim().slice(0, 1).toUpperCase()}
                </span>
              </div>
            </header>
            <div className={styles.content}>
              <div className={styles.hero}>
                <div>
                  <h1>
                    {account.role === 'driver'
                      ? `Hello, ${account.name.split(' ')[0]}.`
                      : role.label}
                  </h1>
                  <p>
                    {account.role === 'driver'
                      ? 'Find a garage or see where your requests stand.'
                      : account.role === 'mechanic'
                        ? 'Set your availability and respond to drivers.'
                        : 'Manage garage listings and mechanic access.'}
                  </p>
                </div>
                <button
                  className={styles.heroAction}
                  type="button"
                  disabled={busy}
                  onClick={() => action(async () => {}, 'Workspace refreshed.')}
                >
                  <RefreshCw size={16} aria-hidden="true" /> Refresh
                </button>
              </div>
              {error && (
                <p className={styles.error} role="alert">
                  {error}
                </p>
              )}
              {notice && (
                <p className={styles.notice} role="status">
                  {notice}
                </p>
              )}
              <Workspace data={data} busy={busy} action={action} />
            </div>
          </main>
        </div>
      )}
    </div>
  )
}
