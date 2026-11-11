import { test } from 'node:test'
import assert from 'node:assert/strict'
import { formatConfidence, sessionStatistics } from '../src/lib/metrics.mjs'

test('missing and invalid confidence never becomes a fabricated percentage', () => {
  for (const value of [null, undefined, NaN, -1, 1.1, '0.95']) {
    assert.equal(formatConfidence(value), 'Unavailable')
  }
  assert.equal(formatConfidence(0.735), '73.5%')
  assert.equal(formatConfidence(0), '0.0%')
})

test('statistics aggregate actual successful session records', () => {
  assert.deepEqual(sessionStatistics([]), {
    total: 0,
    meanConfidence: 'Unavailable',
    meanLatency: 'Unavailable',
  })
  assert.deepEqual(
    sessionStatistics([
      { confidenceValue: 0.7, latencyMs: 100 },
      { confidenceValue: 0.9, latencyMs: 200 },
    ]),
    { total: 2, meanConfidence: '80.0%', meanLatency: '150 ms' },
  )
})
