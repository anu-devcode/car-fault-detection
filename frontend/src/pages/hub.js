import Head from 'next/head'
import Link from 'next/link'
import { useState } from 'react'
import { getCareAdvice } from '../lib/api.mjs'
import { garageSearch } from '../lib/garages.mjs'
import styles from '../styles/hub.module.css'
import VehiclePanel from '../features/vehicles/VehiclePanel'

const symptomOptions = [
  ['smoke_or_fire', 'Smoke or suspected fire'],
  ['fuel_smell', 'Fuel smell or suspected leak'],
  ['brake_problem', 'Brake problem'],
  ['steering_problem', 'Steering problem'],
  ['overheating', 'Overheating'],
  ['oil_pressure_warning', 'Oil-pressure warning'],
  ['flashing_engine_light', 'Flashing engine warning'],
  ['new_noise', 'New or persistent noise'],
]

export default function CarHub() {
  const [symptoms, setSymptoms] = useState([])
  const [pattern, setPattern] = useState('')
  const [advice, setAdvice] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [city, setCity] = useState('')
  const [coordinates, setCoordinates] = useState({})
  const [locationNote, setLocationNote] = useState('')
  const towing = advice?.garage_service === 'towing'

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setAdvice(null)
    try {
      setAdvice(await getCareAdvice({ symptoms, fault_class: pattern || null }))
    } catch (err) {
      setError(err.message || 'Care guidance is unavailable. Contact a mechanic if concerned.')
    } finally {
      setBusy(false)
    }
  }

  function locate() {
    if (!navigator.geolocation) {
      setLocationNote('Location unavailable. Enter your city instead.')
      return
    }
    setLocationNote('Requesting your location…')
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setCoordinates({ latitude: coords.latitude, longitude: coords.longitude })
        setLocationNote('Location ready for your map search. It is not stored by this app.')
      },
      () => setLocationNote('Location was not provided. You can enter your city instead.'),
      { timeout: 10000, maximumAge: 60000 },
    )
  }

  return (
    <main className={styles.hub}>
      <Head>
        <title>Car Care Hub · Ethiopia</title>
      </Head>
      <nav>
        <Link href="/">← Audio diagnosis</Link>
        <span>Development preview · Ethiopia</span>
      </nav>
      <header>
        <p className={styles.eyebrow}>Your next step, explained</p>
        <h1>Car care hub</h1>
        <p>Understand a possible problem, check what is safe to do, and find professional help.</p>
        <p>
          Any make or model can use this guidance. Exact repair procedures depend on your vehicle.
        </p>
      </header>
      <div className={styles.grid}>
        <section className={styles.card}>
          <h2>What are you noticing?</h2>
          <p>Symptoms take priority over an audio result. Use this form while safely parked.</p>
          <form onSubmit={submit}>
            <label>
              Audio pattern, if available
              <select value={pattern} onChange={(event) => setPattern(event.target.value)}>
                <option value="">No audio result / unsure</option>
                {[
                  'Normal',
                  'Braking system',
                  'Oil system',
                  'Combustion & Ignition',
                  'Battery / Electrical',
                  'Belt & Accessory System',
                ].map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </select>
            </label>
            <fieldset>
              <legend>Select any symptoms</legend>
              {symptomOptions.map(([id, title]) => (
                <label className={styles.check} key={id}>
                  <input
                    type="checkbox"
                    checked={symptoms.includes(id)}
                    onChange={(event) =>
                      setSymptoms((previous) =>
                        event.target.checked
                          ? [...previous, id]
                          : previous.filter((item) => item !== id),
                      )
                    }
                  />
                  {title}
                </label>
              ))}
            </fieldset>
            <button disabled={busy}>{busy ? 'Getting guidance…' : 'Get next steps'}</button>
          </form>
          {error && (
            <p role="alert" className={styles.warning}>
              {error}
            </p>
          )}
        </section>
        <section className={styles.card} aria-live="polite" aria-label="Care guidance">
          <h2>Care guidance</h2>
          {!advice ? (
            <p>
              Your next steps will appear here. Smoke, fuel smell, brake/steering problems or red
              warning lights need professional attention regardless of the audio result.
            </p>
          ) : (
            <>
              <p className={styles.badge}>{advice.severity.replaceAll('_', ' ')}</p>
              <h3>{advice.heading}</h3>
              <h4>Immediate owner actions</h4>
              <ul>
                {advice.immediate_actions.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              <h4>Avoid</h4>
              <ul>
                {advice.do_not.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              <p className={styles.warning}>{advice.notice}</p>
              <p>Development guidance: local mechanic review is still required.</p>
              <div>
                {advice.sources.map((source) => (
                  <a key={source.url} href={source.url} target="_blank" rel="noreferrer">
                    {source.title} ↗
                  </a>
                ))}
              </div>
            </>
          )}
        </section>
        <section className={styles.card}>
          <h2>{towing ? 'Find towing or roadside assistance' : 'Find a garage in Ethiopia'}</h2>
          {towing && (
            <p className={styles.warning}>
              Arrange assistance instead of driving to a garage. Handle any immediate danger before
              searching.
            </p>
          )}
          <label>
            Your city or area
            <input
              placeholder="Enter your city or area"
              value={city}
              onChange={(event) => {
                setCity(event.target.value)
                setCoordinates({})
              }}
              maxLength={100}
            />
          </label>
          <button type="button" onClick={locate}>
            Use my current location
          </button>
          <p role="status">{locationNote}</p>
          <a
            className={styles.action}
            href={garageSearch({ city, ...coordinates, towing })}
            target="_blank"
            rel="noreferrer"
          >
            {towing ? 'Search assistance on Google Maps' : 'Search garages on Google Maps'} ↗
          </a>
          <p>
            Map results come from Google Maps. Confirm availability, contact details, capability and
            price directly. This app does not verify listings or make bookings.
          </p>
        </section>
        <VehiclePanel />
      </div>
    </main>
  )
}
