import { CircleCheck, Clock3, Wrench } from 'lucide-react'
import { platform, Requests, Section, Stats } from './shared'
import styles from '../../styles/platform.module.css'

export default function MechanicWorkspace({ data, busy, action }) {
  const { account, counts, garage } = data
  return (
    <>
      <Stats
        items={[
          ['Waiting for a reply', counts.requested, Clock3],
          ['Accepted', counts.accepted, Wrench],
          ['Completed', counts.completed, CircleCheck],
        ]}
      />
      <Section id="availability" title="Your availability">
        <div className={styles.availability}>
          <div>
            <h3>{garage.name}</h3>
            <p>
              {garage.area}, {garage.city}
            </p>
            <span
              className={styles.pill}
              data-state={account.available && garage.published ? 'accepted' : 'cancelled'}
            >
              {!garage.published
                ? 'Garage listing unpublished'
                : account.available
                  ? 'Accepting requests'
                  : 'Unavailable'}
            </span>
          </div>
          <button
            type="button"
            className={account.available ? styles.secondary : styles.primary}
            disabled={busy}
            onClick={() =>
              action(
                () => platform('/mechanic/availability', { available: !account.available }),
                account.available ? 'You’re unavailable for new requests.' : 'Availability saved.',
              )
            }
          >
            {account.available ? 'Mark unavailable' : 'Mark available'}
          </button>
        </div>
      </Section>
      <Section
        id="requests"
        title="Assigned requests"
        summary="Accept requests you can handle. A driver’s callback number is available after you accept."
      >
        <Requests entries={data.requests} role="mechanic" busy={busy} action={action} />
      </Section>
    </>
  )
}
