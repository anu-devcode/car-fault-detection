export function formatConfidence(value) {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1
    ? `${(value * 100).toFixed(1)}%`
    : 'Unavailable'
}

export function sessionStatistics(history) {
  const scores = history
    .map((item) => item.confidenceValue)
    .filter(
      (value) => typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1,
    )
  const latencies = history
    .map((item) => item.latencyMs)
    .filter((value) => typeof value === 'number' && Number.isFinite(value) && value >= 0)
  return {
    total: history.length,
    meanConfidence: scores.length
      ? formatConfidence(scores.reduce((a, b) => a + b, 0) / scores.length)
      : 'Unavailable',
    meanLatency: latencies.length
      ? `${Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length)} ms`
      : 'Unavailable',
  }
}
