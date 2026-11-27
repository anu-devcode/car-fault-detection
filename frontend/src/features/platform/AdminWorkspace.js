import { Building2, ClipboardList, UserRoundCheck } from 'lucide-react'
import { useState } from 'react'
import { platform, Section, Stats } from './shared'
import styles from '../../styles/platform.module.css'

const blankGarage = {
  id: null,
  name: '',
  city: 'Addis Ababa',
  area: '',
  phone: '',
  latitude: '',
  longitude: '',
  published: false,
}

export default function AdminWorkspace({ data, busy, action }) {
  const [garage, setGarage] = useState(blankGarage)
  const [invitation, setInvitation] = useState(null)
  const [inviteGarage, setInviteGarage] = useState('')
  const [inviteEmail, setInviteEmail] = useState('')
  const [copied, setCopied] = useState(false)

  function edit(key, value) {
    setGarage((previous) => ({ ...previous, [key]: value }))
  }

  function save(event) {
    event.preventDefault()
    action(async () => {
      await platform('/admin/garages', {
        ...garage,
        latitude: garage.latitude === '' ? null : Number(garage.latitude),
        longitude: garage.longitude === '' ? null : Number(garage.longitude),
      })
      setGarage(blankGarage)
    }, 'Garage saved.')
  }

  function invite(event) {
    event.preventDefault()
    setInvitation(null)
    setCopied(false)
    action(async () => {
      setInvitation(
        await platform('/admin/invitations', { email: inviteEmail, garage_id: inviteGarage }),
      )
      setInviteEmail('')
    }, 'Invitation created.')
  }

  return (
    <>
      <Stats
        items={[
          ['Published garages', data.stats.published, Building2],
          ['Available mechanics', data.stats.available, UserRoundCheck],
          ['Open requests', data.stats.open, ClipboardList],
        ]}
      />
      <Section
        id="directory"
        title="Garage directory"
        summary="Review a garage’s service number and location before publishing its listing."
      >
        {!!data.garages.length && (
          <ul className={styles.directoryRows}>
            {data.garages.map((entry) => (
              <li key={entry.id}>
                <div>
                  <strong>{entry.name}</strong>
                  <p className={styles.meta}>
                    {entry.area}, {entry.city}
                  </p>
                </div>
                <span
                  className={styles.pill}
                  data-state={entry.published ? 'accepted' : 'cancelled'}
                >
                  {entry.published ? 'Published' : 'Unpublished'}
                </span>
                <button
                  type="button"
                  className={styles.secondary}
                  onClick={() => {
                    setGarage({
                      ...entry,
                      latitude: entry.latitude ?? '',
                      longitude: entry.longitude ?? '',
                    })
                    document.getElementById('garage-form')?.scrollIntoView({ block: 'start' })
                  }}
                  disabled={busy}
                >
                  Edit
                </button>
              </li>
            ))}
          </ul>
        )}
        <form className={styles.workForm} id="garage-form" onSubmit={save}>
          <h3>{garage.id ? 'Edit garage' : 'Add a garage'}</h3>
          <div className={styles.formGrid}>
            <label>
              Garage name
              <input
                value={garage.name}
                onChange={(event) => edit('name', event.target.value)}
                required
                minLength={2}
                maxLength={100}
              />
            </label>
            <label>
              City
              <input
                value={garage.city}
                onChange={(event) => edit('city', event.target.value)}
                required
                minLength={2}
                maxLength={80}
              />
            </label>
            <label>
              Area or address
              <input
                value={garage.area}
                onChange={(event) => edit('area', event.target.value)}
                required
                minLength={2}
                maxLength={140}
              />
            </label>
            <label>
              Public service number
              <input
                value={garage.phone}
                onChange={(event) => edit('phone', event.target.value)}
                required
                type="tel"
                pattern="\+?[0-9]{7,15}"
                maxLength={16}
              />
            </label>
            <label>
              Latitude (optional)
              <input
                type="number"
                min={-85}
                max={85}
                step="any"
                value={garage.latitude}
                onChange={(event) => edit('latitude', event.target.value)}
              />
            </label>
            <label>
              Longitude (optional)
              <input
                type="number"
                min={-180}
                max={180}
                step="any"
                value={garage.longitude}
                onChange={(event) => edit('longitude', event.target.value)}
              />
            </label>
          </div>
          <p className={styles.meta}>
            Add both coordinates to include this garage in nearby searches.
          </p>
          <label className={styles.checkbox}>
            <input
              type="checkbox"
              checked={garage.published}
              onChange={(event) => edit('published', event.target.checked)}
            />{' '}
            Show this garage to drivers
          </label>
          <div className={styles.actions}>
            <button className={styles.primary} disabled={busy}>
              Save garage
            </button>
            {garage.id && (
              <button
                type="button"
                className={styles.secondary}
                disabled={busy}
                onClick={() => setGarage(blankGarage)}
              >
                Cancel edit
              </button>
            )}
          </div>
        </form>
      </Section>
      <Section
        id="mechanics"
        title="Mechanic access"
        summary="Invite someone you’ve verified and assign them to a garage."
      >
        {!!data.mechanics.length && (
          <ul className={styles.directoryRows}>
            {data.mechanics.map((person) => (
              <li key={person.id}>
                <div>
                  <strong>{person.name}</strong>
                  <p className={styles.meta}>
                    {data.garages.find((item) => item.id === person.garage_id)?.name ||
                      'Assigned garage'}
                  </p>
                </div>
                <span
                  className={styles.pill}
                  data-state={person.available ? 'accepted' : 'cancelled'}
                >
                  {person.available ? 'Available' : 'Unavailable'}
                </span>
              </li>
            ))}
          </ul>
        )}
        <form className={styles.workForm} onSubmit={invite}>
          <h3>Create an invitation</h3>
          {!data.garages.length && <p>Add a garage before inviting a mechanic.</p>}
          <div className={styles.formGrid}>
            <label>
              Mechanic email
              <input
                required
                type="email"
                maxLength={254}
                value={inviteEmail}
                onChange={(event) => setInviteEmail(event.target.value)}
              />
            </label>
            <label>
              Garage
              <select
                required
                value={inviteGarage}
                onChange={(event) => setInviteGarage(event.target.value)}
              >
                <option value="">Choose a garage</option>
                {data.garages.map((entry) => (
                  <option key={entry.id} value={entry.id}>
                    {entry.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <button className={styles.primary} disabled={busy || !data.garages.length}>
            Create invitation
          </button>
        </form>
        {invitation && (
          <div className={styles.workForm} aria-live="polite">
            <h3>One-time invitation code</h3>
            <p>
              Share the code privately with the mechanic. They can use it with their email when
              creating an account. It expires in 24 hours.
            </p>
            <label>
              Invitation code
              <input readOnly value={invitation.code} onFocus={(event) => event.target.select()} />
            </label>
            <button
              className={styles.secondary}
              type="button"
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(invitation.code)
                  setCopied(true)
                } catch {
                  setCopied(false)
                }
              }}
            >
              {copied ? 'Copied' : 'Copy code'}
            </button>
          </div>
        )}
      </Section>
    </>
  )
}
