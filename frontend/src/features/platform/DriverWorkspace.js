import {
  Building2,
  CircleCheck,
  Clock3,
  MapPin,
  Navigation,
  Phone,
  Search,
  Wrench,
} from 'lucide-react'
import { useState } from 'react'
import Link from 'next/link'
import { platform, Requests, Section, serviceNames, Stats } from './shared'
import styles from '../../styles/platform.module.css'

function directions(garage) {
  const query =
    garage.latitude === null
      ? `${garage.name}, ${garage.area}, ${garage.city}`
      : `${garage.latitude},${garage.longitude}`
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`
}

export default function DriverWorkspace({ data, busy, action }) {
  const [city, setCity] = useState('Addis Ababa')
  const [results, setResults] = useState(null)
  const [selected, setSelected] = useState(null)
  const [finding, setFinding] = useState(false)
  const [directoryError, setDirectoryError] = useState('')
  const counts = data.counts || {}

  async function search(query) {
    setFinding(true)
    setDirectoryError('')
    try {
      setResults(await platform('/directory/search', query))
      setSelected(null)
    } catch (error) {
      setDirectoryError(error.message)
    } finally {
      setFinding(false)
    }
  }

  function locate() {
    if (!navigator.geolocation) {
      setDirectoryError('Location is unavailable in this browser. Search by city instead.')
      return
    }
    setFinding(true)
    setDirectoryError('')
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => search({ latitude: coords.latitude, longitude: coords.longitude }),
      () => {
        setFinding(false)
        setDirectoryError('We could not get your location. Search by city instead.')
      },
      { timeout: 8000, maximumAge: 60000 },
    )
  }

  function sendRequest(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const description = form.get('details').trim()
    const callback = form.get('callback').trim() || null
    const current = selected
    action(async () => {
      await platform('/requests', {
        mechanic_id: current.mechanic.id,
        request_key: current.key,
        service: form.get('service'),
        details: description,
        callback,
      })
      setSelected(null)
    }, 'Request sent. Check My requests for the mechanic’s reply.')
  }

  return (
    <>
      <Stats
        items={[
          ['Awaiting reply', counts.requested, Clock3],
          ['Accepted requests', counts.accepted, Wrench],
          ['Completed', counts.completed, CircleCheck],
        ]}
      />
      <Section
        id="directory"
        title="Find a garage"
        summary="Search by city or use your location to find listed garages within 25 km."
      >
        <form
          className={styles.search}
          onSubmit={(event) => {
            event.preventDefault()
            search({ city: city.trim() })
          }}
        >
          <label className={styles.searchField}>
            <span>City</span>
            <input
              value={city}
              maxLength={80}
              required
              onChange={(event) => setCity(event.target.value)}
            />
          </label>
          <button className={styles.primary} disabled={finding}>
            <Search size={17} aria-hidden="true" /> Search
          </button>
          <button className={styles.secondary} type="button" onClick={locate} disabled={finding}>
            <Navigation size={17} aria-hidden="true" /> Use my location
          </button>
        </form>
        <p className={styles.meta}>Your location is used for this search and is not saved.</p>
        {directoryError && (
          <p className={styles.error} role="alert">
            {directoryError}
          </p>
        )}
        {finding && <p role="status">Looking for garages…</p>}
        {results && !results.garages.length && (
          <div className={styles.empty}>
            <Building2 size={24} aria-hidden="true" />
            <p>
              No listed garages match. Try another city or use the{' '}
              <Link href="/hub">map search in Car Care</Link>.
            </p>
          </div>
        )}
        {!!results?.garages.length && (
          <div className={styles.locationList}>
            {results.garages.map((garage) => (
              <article className={styles.garage} key={garage.id}>
                <div className={styles.requestTitle}>
                  <h3>{garage.name}</h3>
                  {garage.distance_km !== null && (
                    <span className={styles.pill}>{garage.distance_km} km</span>
                  )}
                </div>
                <p className={styles.meta}>
                  <MapPin size={15} aria-hidden="true" /> {garage.area}, {garage.city}
                </p>
                <div className={styles.actions}>
                  <a className={styles.secondary} href={`tel:${garage.phone}`}>
                    <Phone size={15} aria-hidden="true" /> Call garage
                  </a>
                  <a
                    className={styles.textAction}
                    href={directions(garage)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Directions
                  </a>
                </div>
                <h4>
                  {garage.mechanics.length
                    ? 'Available mechanics'
                    : 'No mechanics taking requests right now'}
                </h4>
                {garage.mechanics.map((mechanic) => (
                  <div className={styles.person} key={mechanic.id}>
                    <span>{mechanic.name}</span>
                    <button
                      className={styles.secondary}
                      type="button"
                      disabled={busy}
                      onClick={() => {
                        setSelected({ mechanic, garage, key: crypto.randomUUID() })
                      }}
                    >
                      Request help
                    </button>
                  </div>
                ))}
              </article>
            ))}
          </div>
        )}
        {selected && (
          <form key={selected.key} className={styles.workForm} onSubmit={sendRequest}>
            <h3>Request help from {selected.mechanic.name}</h3>
            <p className={styles.meta}>
              {selected.garage.name} will receive the request. You can track the reply below.
            </p>
            <label>
              Service needed
              <select name="service" required>
                {Object.entries(serviceNames).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              What is happening?
              <textarea name="details" required minLength={5} maxLength={1000} rows={3} />
            </label>
            <label>
              Callback number (optional)
              <input
                name="callback"
                type="tel"
                inputMode="tel"
                pattern="\+?[0-9]{7,15}"
                maxLength={16}
              />
              <small>Shared with the selected mechanic after they accept.</small>
            </label>
            <div className={styles.actions}>
              <button className={styles.primary} disabled={busy}>
                Send request
              </button>
              <button
                className={styles.secondary}
                type="button"
                disabled={busy}
                onClick={() => setSelected(null)}
              >
                Close
              </button>
            </div>
          </form>
        )}
      </Section>
      <Section id="requests" title="My requests">
        <Requests entries={data.requests} role="driver" busy={busy} action={action} />
      </Section>
    </>
  )
}
