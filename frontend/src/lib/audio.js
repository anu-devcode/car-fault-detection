export const encodeWav = (audioBuffer) => {
  const numChannels = 1
  const sampleRate = audioBuffer.sampleRate
  const source =
    audioBuffer.numberOfChannels > 1
      ? audioBuffer.getChannelData(0).map((_, index) => {
          let sum = 0
          for (let channel = 0; channel < audioBuffer.numberOfChannels; channel += 1) {
            sum += audioBuffer.getChannelData(channel)[index]
          }
          return sum / audioBuffer.numberOfChannels
        })
      : audioBuffer.getChannelData(0)

  const buffer = new ArrayBuffer(44 + source.length * 2)
  const view = new DataView(buffer)
  const writeString = (offset, text) => {
    for (let i = 0; i < text.length; i += 1) {
      view.setUint8(offset + i, text.charCodeAt(i))
    }
  }

  writeString(0, 'RIFF')
  view.setUint32(4, 36 + source.length * 2, true)
  writeString(8, 'WAVE')
  writeString(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, numChannels, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * numChannels * 2, true)
  view.setUint16(32, numChannels * 2, true)
  view.setUint16(34, 16, true)
  writeString(36, 'data')
  view.setUint32(40, source.length * 2, true)

  let offset = 44
  for (let i = 0; i < source.length; i += 1) {
    const sample = Math.max(-1, Math.min(1, source[i]))
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true)
    offset += 2
  }

  return buffer
}

export const blobToWavFile = async (blob) => {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)()
  try {
    const arrayBuffer = await blob.arrayBuffer()
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer.slice(0))
    return new Blob([encodeWav(audioBuffer)], { type: 'audio/wav' })
  } finally {
    await audioContext.close()
  }
}
