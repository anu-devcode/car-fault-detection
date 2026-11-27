import styles from '../../styles/hub.module.css'

export default function PhotoReview({ options, inspection, review, onChange, profile, busy }) {
  const selected = options.find((option) => option.scene === review.scene)
  const suggested = new Set(
    inspection?.scene === review.scene ? inspection.findings.map((finding) => finding.code) : [],
  )
  const confirmed = selected?.findings.filter((finding) => review.confirmed.includes(finding.code))

  function toggle(code) {
    const codes = review.confirmed
    onChange({
      scene: review.scene,
      confirmed: codes.includes(code) ? codes.filter((item) => item !== code) : [...codes, code],
    })
  }

  function downloadNotes() {
    const vehicle = [profile.make.trim(), profile.model.trim(), profile.year]
      .filter(Boolean)
      .join(' ')
    const lines = [
      'Vehicle inspection notes',
      new Date().toLocaleString(),
      ...(vehicle ? [`Vehicle details supplied by driver — ${vehicle}`] : []),
      `Area reviewed — ${selected.subject}`,
      '',
      ...confirmed.flatMap((finding) => [
        finding.title,
        finding.next_step,
        ...(finding.source_url ? [finding.source_url] : []),
        '',
      ]),
      'Observations supplied by the driver. A mechanic should confirm the cause.',
    ]
    const url = URL.createObjectURL(new Blob([lines.join('\n')], { type: 'text/plain' }))
    const link = document.createElement('a')
    link.href = url
    link.download = 'vehicle-inspection-notes.txt'
    document.body.append(link)
    link.click()
    link.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  if (!options.length) return null
  return (
    <div className={styles.photoResult}>
      <h3>Review visible clues</h3>
      {inspection && (
        <div aria-live="polite">
          <p>
            Suggested view — {inspection.subject}. {inspection.next_photo}
          </p>
          {!inspection.findings.length && <p>The model did not flag a specific visible clue.</p>}
        </div>
      )}
      <label>
        Area to review
        <select
          value={review.scene}
          disabled={busy}
          onChange={(event) => onChange({ scene: event.target.value, confirmed: [] })}
        >
          <option value="">Choose the vehicle area</option>
          {options.map((option) => (
            <option key={option.scene} value={option.scene}>
              {option.subject}
            </option>
          ))}
        </select>
      </label>
      {selected && (
        <fieldset disabled={busy}>
          <legend>Select the clues you can see</legend>
          {selected.findings.map((finding) => (
            <label key={finding.code} className={styles.check}>
              <input
                type="checkbox"
                checked={review.confirmed.includes(finding.code)}
                onChange={() => toggle(finding.code)}
              />
              {finding.title}
              {suggested.has(finding.code) && <small>Suggested by photo</small>}
            </label>
          ))}
        </fieldset>
      )}
      {!!confirmed?.length && (
        <div aria-live="polite">
          <h4>Follow-up checks</h4>
          <ul>
            {confirmed.map((finding) => (
              <li key={finding.code}>
                <strong>{finding.title}</strong>
                <p>{finding.next_step}</p>
                {finding.source_url && (
                  <a href={finding.source_url} target="_blank" rel="noreferrer">
                    Reference guidance ↗
                  </a>
                )}
              </li>
            ))}
          </ul>
          <button type="button" onClick={downloadNotes} disabled={busy}>
            Download inspection notes
          </button>
        </div>
      )}
      <p className={styles.warning}>
        {inspection?.notice ||
          'A visual check cannot rule out hidden faults or establish whether the vehicle is safe to drive.'}
      </p>
      <a href="#symptom-check">Continue with the symptom check</a>
    </div>
  )
}
