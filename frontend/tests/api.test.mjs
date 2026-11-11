import { test } from 'node:test'
import assert from 'node:assert/strict'
import { uploadAudio, healthCheck } from '../src/lib/api.mjs'

test('upload uses native multipart boundaries and returns server confidence', async (t) => {
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.ok(url.endsWith('/predict'))
    assert.equal(options.method, 'POST')
    assert.ok(options.body instanceof FormData)
    assert.equal(options.headers, undefined)
    assert.ok(options.body.get('file') instanceof Blob)
    return Response.json({ success: true, confidence: 0.73 })
  })
  assert.deepEqual(await uploadAudio(new Blob(['audio'], { type: 'audio/wav' })), {
    success: true,
    confidence: 0.73,
  })
})

test('API errors preserve status and readable details for the UI', async (t) => {
  t.mock.method(globalThis, 'fetch', async () =>
    Response.json({ detail: 'Prediction service is unavailable.' }, { status: 503 }),
  )
  await assert.rejects(
    healthCheck(),
    (error) =>
      error.response.status === 503 && error.message === 'Prediction service is unavailable.',
  )
})

test('timeout produces the UI-compatible error code without mutating DOMException', async (t) => {
  t.mock.method(globalThis, 'setTimeout', (callback) => {
    queueMicrotask(callback)
    return 1
  })
  t.mock.method(
    globalThis,
    'fetch',
    async (_url, { signal }) =>
      new Promise((_resolve, reject) => {
        signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))
      }),
  )
  await assert.rejects(healthCheck(), (error) => error.code === 'ECONNABORTED')
})
