import { useState, useRef, useEffect } from 'react'
import { uploadAudio, healthCheck } from '../../lib/api.mjs'
import { blobToWavFile } from '../../lib/audio'
import { formatConfidence } from '../../lib/metrics.mjs'

export function useDiagnosticSession() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [modelReady, setModelReady] = useState(false)
  const [dragover, setDragover] = useState(false)
  const [activeTab, setActiveTab] = useState('terminal')
  const [theme, setTheme] = useState('dark')
  const [history, setHistory] = useState([])
  const [previewUrl, setPreviewUrl] = useState(null)
  const fileInputRef = useRef(null)
  const [recording, setRecording] = useState(false)
  const [mediaRecorder, setMediaRecorder] = useState(null)
  const recorderRef = useRef(null)
  useEffect(
    () => () => {
      const recorder = recorderRef.current
      if (recorder) {
        recorder.onstop = null
        if (recorder.state !== 'inactive') recorder.stop()
        recorder.stream.getTracks().forEach((track) => track.stop())
      }
    },
    [],
  )
  const [scanProgress, setScanProgress] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [statusMsg, setStatusMsg] = useState('READY')
  const audioRef = useRef(null)

  useEffect(() => {
    const savedTheme = localStorage.getItem('diag-theme') || 'dark'
    setTheme(savedTheme)
    document.documentElement.setAttribute('data-theme', savedTheme)

    const checkModel = async () => {
      try {
        const response = await healthCheck()
        setModelReady(response.model === 'loaded')
        if (response.model !== 'loaded') setError('Prediction service is unavailable.')
      } catch (err) {
        setError('System error. Please check if the app is running.')
      }
    }
    checkModel()
  }, [])

  useEffect(() => {
    if (loading) {
      const interval = setInterval(() => {
        setScanProgress((prev) => (prev >= 90 ? 90 : prev + 2))
      }, 50)
      return () => clearInterval(interval)
    } else {
      setScanProgress(0)
    }
  }, [loading])

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null)
      return
    }
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
    localStorage.setItem('diag-theme', newTheme)
  }

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) validateFile(selectedFile)
  }

  const validateFile = (selectedFile) => {
    const MAX_SIZE = 5 * 1024 * 1024
    const MIN_SIZE = 1024
    const allowedTypes = [
      'audio/wav',
      'audio/x-wav',
      'audio/mpeg',
      'audio/mp3',
      'audio/mp4',
      'audio/aac',
      'audio/ogg',
      'audio/flac',
      'audio/webm',
      'audio/opus',
    ]
    if (!selectedFile || loading) return
    if (selectedFile.size > MAX_SIZE) {
      setError(`File is too big. Max size is 5MB.`)
      return
    }
    if (selectedFile.size < MIN_SIZE) {
      setError('Audio file is too small or empty. Please upload a valid sound file.')
      return
    }
    if (selectedFile.type && !allowedTypes.includes(selectedFile.type.toLowerCase())) {
      setError(
        'Unsupported file type. Please upload a WAV, MP3, M4A, OGG, FLAC, AAC, WEBM, or OPUS file.',
      )
      return
    }
    setFile(selectedFile)
    setError(null)
    setResult(null)
  }

  const startRecording = async () => {
    if (loading || recording) return
    setError(null)
    let stream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream)
      const chunks = []
      mr.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data)
      }
      mr.onstop = async () => {
        try {
          const recordedBlob = new Blob(chunks, { type: mr.mimeType || 'audio/webm' })
          const wavBlob = await blobToWavFile(recordedBlob)
          const wavFile = new File([wavBlob], `recording_${Date.now()}.wav`, { type: 'audio/wav' })
          await validateFile(wavFile)
        } catch (recordingError) {
          setError('Could not convert microphone recording to WAV.')
        }
      }
      mr.start()
      recorderRef.current = mr
      setMediaRecorder(mr)
      setRecording(true)
    } catch (err) {
      stream?.getTracks().forEach((track) => track.stop())
      setError('Microphone error.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop()
      setRecording(false)
      mediaRecorder.stream.getTracks().forEach((t) => t.stop())
    }
  }

  const handlePredict = async () => {
    if (!file || loading) return
    setLoading(true)
    setError(null)
    setResult(null)
    setStatusMsg('UPLOADING')

    try {
      setStatusMsg('ANALYZING AUDIO')
      const started = performance.now()
      const data = await uploadAudio(file)
      if (data.success !== true || !data.fault_class)
        throw new Error('Invalid prediction response.')
      setModelReady(true)
      const latencyMs = Math.round(performance.now() - started)

      setStatusMsg('ANALYSIS COMPLETE')
      setResult(data)

      setHistory((prev) => [
        {
          id: Date.now(),
          class: data.fault_class,
          system: data.location,
          date: new Date().toISOString().slice(0, 16).replace('T', ' '),
          confidence: formatConfidence(data.confidence),
          confidenceValue: data.confidence ?? null,
          latencyMs,
        },
        ...prev,
      ])
    } catch (err) {
      if (err.response?.status === 503) setModelReady(false)
      const isTimeout = err.code === 'ECONNABORTED' || err.message?.includes('timeout')
      setError(
        isTimeout
          ? 'Server timeout. It might be warming up. Please try again.'
          : err.response?.data?.detail || err.message || 'Problem analyzing sound.',
      )
      setStatusMsg('ERROR')
    } finally {
      setLoading(false)
    }
  }

  const clearFile = () => {
    if (loading) return
    setFile(null)
    setResult(null)
    setError(null)
    setIsPlaying(false)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const togglePlay = () => {
    if (!audioRef.current) return
    if (isPlaying) {
      audioRef.current.pause()
    } else {
      audioRef.current.play().catch(() => {
        setError('Unable to play this audio file.')
        setIsPlaying(false)
      })
    }
    setIsPlaying(!isPlaying)
  }

  const handleAudioEnd = () => {
    setIsPlaying(false)
  }

  return {
    file,
    loading,
    result,
    error,
    modelReady,
    dragover,
    activeTab,
    theme,
    history,
    previewUrl,
    fileInputRef,
    recording,
    scanProgress,
    isPlaying,
    statusMsg,
    audioRef,
    setActiveTab,
    setDragover,
    toggleTheme,
    handleFileSelect,
    validateFile,
    startRecording,
    stopRecording,
    handlePredict,
    clearFile,
    togglePlay,
    handleAudioEnd,
  }
}
