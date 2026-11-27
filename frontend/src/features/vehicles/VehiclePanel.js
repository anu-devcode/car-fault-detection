import { useEffect, useState } from 'react'
import {
  identifyVehicle,
  inspectVehiclePhoto,
  photoModelStatus,
  vehicleResources,
} from '../../lib/api.mjs'
import { formatConfidence } from '../../lib/metrics.mjs'
import styles from '../../styles/hub.module.css'
import PhotoReview from './PhotoReview'

const emptyReview = { scene: '', confirmed: [] }

export default function VehiclePanel() {
  const [ready, setReady] = useState(false)
  const [inspectionConfigured, setInspectionConfigured] = useState(false)
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [matches, setMatches] = useState(null)
  const [inspection, setInspection] = useState(null)
  const [reviewOptions, setReviewOptions] = useState([])
  const [review, setReview] = useState(emptyReview)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [profile, setProfile] = useState({ make: '', model: '', year: '' })
  const [resources, setResources] = useState(null)

  useEffect(() => {
    let active = true
    photoModelStatus()
      .then((value) => {
        if (active) {
          setReady(value.ready)
          setInspectionConfigured(value.inspection_configured)
          setReviewOptions(value.inspection_options || [])
        }
      })
      .catch(() => {})
    return () => {
      active = false
    }
  }, [])
  useEffect(() => {
    if (!file) {
      setPreview(null)
      return
    }
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  function choose(event) {
    if (busy) return
    const selected = event.target.files?.[0]
    if (!selected) return
    setMatches(null)
    setInspection(null)
    setReview(emptyReview)
    setFile(null)
    setError('')
    event.target.value = ''
    if (selected.size > 8 * 1024 * 1024) {
      setError('Photo exceeds the 8 MB limit.')
      return
    }
    setFile(selected)
  }
  async function inspect() {
    if (!file || busy) return
    setBusy(true)
    setError('')
    setInspection(null)
    setReview(emptyReview)
    try {
      const result = await inspectVehiclePhoto(file)
      setInspection(result)
      if (reviewOptions.some((option) => option.scene === result.scene)) {
        setReview({ scene: result.scene, confirmed: [] })
      }
    } catch (err) {
      setError(err.message || 'Photo inspection was unavailable. Review visible clues below.')
    } finally {
      setBusy(false)
    }
  }
  async function identify() {
    if (!file || busy) return
    setBusy(true)
    setError('')
    setMatches(null)
    try {
      setMatches(await identifyVehicle(file))
    } catch (err) {
      setError(err.message || 'Unable to identify this photo. Use manual entry.')
    } finally {
      setBusy(false)
    }
  }
  async function confirm(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setResources(null)
    try {
      setResources(
        await vehicleResources({ ...profile, year: profile.year ? Number(profile.year) : null }),
      )
    } catch (err) {
      setError(err.message || 'Vehicle resources unavailable.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className={styles.card} id="vehicle-profile">
      <h2>Vehicle photo check</h2>
      <p>
        Use a whole-car photo to find possible make and model matches. Use a close-up of a tyre,
        dashboard, engine bay or body panel to look for visible clues.
      </p>
      <div className={styles.photoActions}>
        <label>
          Take a photo
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            onChange={choose}
            disabled={busy}
          />
        </label>
        <label>
          Choose a photo
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={choose}
            disabled={busy}
          />
        </label>
      </div>
      {preview && (
        <div
          className={styles.preview}
          style={{ backgroundImage: `url("${preview}")` }}
          role="img"
          aria-label="Selected car photograph"
        />
      )}
      {file && <p>{file.name}</p>}
      <div className={styles.photoActions}>
        <button type="button" disabled={!inspectionConfigured || !file || busy} onClick={inspect}>
          Inspect visible clues
        </button>
        <button type="button" disabled={!ready || !file || busy} onClick={identify}>
          Find make and model matches
        </button>
      </div>
      {busy && <p role="status">Working…</p>}
      {!inspectionConfigured && (
        <p>Automatic photo inspection is unavailable here. You can review visible clues below.</p>
      )}
      {!ready && <p>Photo matching is unavailable here. You can enter the make and model below.</p>}
      {error && (
        <p role="alert" className={styles.warning}>
          {error}
        </p>
      )}
      <PhotoReview
        options={reviewOptions}
        inspection={inspection}
        review={review}
        onChange={setReview}
        profile={profile}
        busy={busy}
      />
      {matches && (
        <div>
          <p className={styles.warning}>{matches.notice}</p>
          {matches.manual_entry_recommended && (
            <p role="status">No reliable photo match. Enter your vehicle details manually.</p>
          )}
          <ul>
            {!matches.manual_entry_recommended &&
              matches.candidates.map((candidate) => (
                <li key={candidate.label}>
                  <p>
                    {candidate.label} · model score {formatConfidence(candidate.confidence)}
                  </p>
                  <button
                    type="button"
                    onClick={() => {
                      setProfile({
                        make: candidate.make,
                        model: candidate.model,
                        year: candidate.year_candidate || '',
                      })
                      setResources(null)
                    }}
                  >
                    Use this candidate for review
                  </button>
                </li>
              ))}
          </ul>
        </div>
      )}
      <form onSubmit={confirm}>
        <h3>Confirm or enter your vehicle</h3>
        <label>
          Make
          <input
            required
            maxLength={80}
            value={profile.make}
            onChange={(event) => setProfile({ ...profile, make: event.target.value })}
          />
        </label>
        <label>
          Model
          <input
            required
            maxLength={100}
            value={profile.model}
            onChange={(event) => setProfile({ ...profile, model: event.target.value })}
          />
        </label>
        <label>
          Year, if known
          <input
            type="number"
            min={1900}
            max={2030}
            value={profile.year}
            onChange={(event) => setProfile({ ...profile, year: event.target.value })}
          />
        </label>
        <button disabled={busy}>Get vehicle resources</button>
      </form>
      {resources && (
        <div aria-live="polite">
          <h3>
            {resources.vehicle.make} {resources.vehicle.model} {resources.vehicle.year}
          </h3>
          <p>User-provided details; not independently verified.</p>
          <p>{resources.notice}</p>
          {resources.resources.length ? (
            resources.resources.map((resource) => (
              <a key={resource.url} href={resource.url} target="_blank" rel="noreferrer">
                {resource.title} ↗
              </a>
            ))
          ) : (
            <p>
              No verified manufacturer link is listed for this make. Use the official manufacturer
              site or an authorized local representative.
            </p>
          )}
          <h4>What to check next</h4>
          <ul>
            {resources.maintenance_topics.map((topic) => (
              <li key={topic}>{topic}</li>
            ))}
          </ul>
          <p>Still unknown: {resources.unknown_fields.join(', ').replaceAll('_', ' ')}.</p>
        </div>
      )}
      <p>
        Photo inspection uses the model on the API host. Review any make or model match before using
        its owner resources.
      </p>
    </section>
  )
}
