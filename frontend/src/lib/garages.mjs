export function garageSearch({ city = '', latitude, longitude, towing = false } = {}) {
  const service = towing ? 'vehicle towing roadside assistance' : 'car repair garage'
  const hasCoordinates =
    Number.isFinite(latitude) &&
    Number.isFinite(longitude) &&
    latitude >= -90 &&
    latitude <= 90 &&
    longitude >= -180 &&
    longitude <= 180
  const location = hasCoordinates ? `${latitude},${longitude}` : `${city.trim()} Ethiopia`.trim()
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${service} near ${location}`)}`
}
