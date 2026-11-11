import { test } from 'node:test'
import assert from 'node:assert/strict'
import { garageSearch } from '../src/lib/garages.mjs'

test('garage searches use Ethiopia without inventing a verified garage', () => {
  const url = new URL(garageSearch({ city: 'Hawassa & nearby' }))
  assert.equal(url.hostname, 'www.google.com')
  assert.ok(url.searchParams.get('query').includes('Hawassa & nearby Ethiopia'))
})

test('location and towing are explicit; invalid coordinates fall back to location text', () => {
  assert.ok(
    new URL(garageSearch({ latitude: 9, longitude: 38, towing: true })).searchParams
      .get('query')
      .includes('towing roadside assistance near 9,38'),
  )
  assert.ok(
    new URL(garageSearch({ latitude: 999, longitude: 38 })).searchParams
      .get('query')
      .includes('Ethiopia'),
  )
})
