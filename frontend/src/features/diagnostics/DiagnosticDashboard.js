import Head from 'next/head'
import Link from 'next/link'
import Image from 'next/image'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mic,
  Square,
  FileAudio,
  Cpu,
  AlertCircle,
  Scan,
  Settings,
  Database,
  Terminal,
  ChevronRight,
  RefreshCcw,
  BarChart3,
  Clock,
  Sun,
  Moon,
} from 'lucide-react'
import { useDiagnosticSession } from './useDiagnosticSession'
import { ResultCard, StatisticsPanel, RecordsPanel, SettingsPanel } from './panels'

export default function DiagnosticDashboard() {
  const {
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
  } = useDiagnosticSession()

  return (
    <div className="app-wrapper">
      <Head>
        <title>Engine Diagnostic AI</title>
        <link rel="icon" href="/logo.png" />
      </Head>
      <div className="glow-orb orb-1" />
      <div className="glow-orb orb-2" />
      <div className="grid-overlay" />

      {previewUrl && <audio ref={audioRef} src={previewUrl} onEnded={handleAudioEnd} hidden />}

      <main className="main-layout">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-icons">
            <motion.button
              type="button"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className={`nav-item ${activeTab === 'terminal' ? 'active' : ''}`}
              title="Home"
              aria-label="Home"
              onClick={() => setActiveTab('terminal')}
            >
              <Terminal size={24} />
            </motion.button>

            <motion.button
              type="button"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className={`nav-item ${activeTab === 'analytics' ? 'active' : ''}`}
              title="Stats"
              aria-label="Stats"
              onClick={() => setActiveTab('analytics')}
            >
              <BarChart3 size={24} />
            </motion.button>

            <motion.button
              type="button"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className={`nav-item ${activeTab === 'database' ? 'active' : ''}`}
              title="Records"
              aria-label="Records"
              onClick={() => setActiveTab('database')}
            >
              <Database size={24} />
            </motion.button>

            <motion.button
              type="button"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className="nav-item"
              title={theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
              aria-label={theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
              onClick={toggleTheme}
            >
              {theme === 'dark' ? <Sun size={24} /> : <Moon size={24} />}
            </motion.button>

            <motion.button
              type="button"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
              id="settings-nav-item"
              title="Settings"
              aria-label="Settings"
              onClick={() => setActiveTab('settings')}
            >
              <Settings size={24} />
            </motion.button>
          </div>
        </aside>

        <section className="content-body">
          {activeTab === 'terminal' && (
            <motion.div
              className="terminal-grid"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <div className="visualizer-panel">
                <header
                  className="scan-header"
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-end',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                    <motion.div
                      initial={{ rotate: -10, opacity: 0 }}
                      animate={{ rotate: 0, opacity: 1 }}
                      style={{
                        width: '60px',
                        height: '60px',
                        background: 'rgba(0,242,255,0.1)',
                        borderRadius: '12px',
                        padding: '5px',
                        border: '1px solid var(--border)',
                      }}
                    >
                      <Image
                        src="/logo.png"
                        width={50}
                        height={50}
                        alt="Logo"
                        style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                      />
                    </motion.div>
                    <div>
                      <h1>Engine Sound Checker</h1>
                      <Link href="/hub">Open the Ethiopia car care hub</Link>
                      <div
                        className="mobile-hide"
                        style={{
                          display: 'flex',
                          gap: '1rem',
                          marginTop: '0.8rem',
                          color: 'var(--text-muted)',
                          fontSize: '0.9rem',
                          letterSpacing: '0.12em',
                          fontWeight: '500',
                        }}
                      >
                        <span>[ STATUS: {modelReady ? 'WORKING' : 'OFFLINE'} ]</span>
                        <span>[ VERSION: 2.1.0 ]</span>
                        <span style={{ color: 'var(--primary)' }}>[ SOUND FREQ: 16.0 kHz ]</span>
                      </div>
                    </div>
                  </div>
                  <div className="mobile-hide" style={{ textAlign: 'right' }}>
                    <div
                      style={{
                        fontSize: '0.8rem',
                        color: 'var(--text-muted)',
                        letterSpacing: '0.1em',
                      }}
                    >
                      PREDICTION SERVICE
                    </div>
                    <div
                      style={{
                        color: 'var(--primary)',
                        fontWeight: '800',
                        fontFamily: 'var(--font-orbitron)',
                        fontSize: '0.95rem',
                      }}
                    >
                      {modelReady ? 'MODEL READY' : 'UNAVAILABLE'}
                    </div>
                  </div>
                </header>

                <div
                  className={`visualizer-hero ${dragover ? 'dragover' : ''}`}
                  onDragOver={(e) => {
                    e.preventDefault()
                    setDragover(true)
                  }}
                  onDragLeave={() => setDragover(false)}
                  onDrop={(e) => {
                    e.preventDefault()
                    setDragover(false)
                    validateFile(e.dataTransfer.files[0])
                  }}
                >
                  {loading && <div className="scanner-beam" />}
                  <AnimatePresence mode="wait">
                    {!file ? (
                      <motion.div
                        key="empty"
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 1.1 }}
                        style={{ textAlign: 'center', cursor: 'pointer' }}
                        onClick={() => fileInputRef.current?.click()}
                      >
                        <div
                          style={{
                            position: 'relative',
                            display: 'inline-block',
                            marginBottom: '2.5rem',
                          }}
                        >
                          <div
                            className="status-ring"
                            style={{ width: '220px', height: '220px' }}
                          />
                          <motion.div
                            animate={{ opacity: [0.3, 0.6, 0.3] }}
                            transition={{ duration: 2, repeat: Infinity }}
                            style={{
                              position: 'absolute',
                              top: '50%',
                              left: '50%',
                              transform: 'translate(-50%, -50%)',
                            }}
                          >
                            <Scan size={80} color="var(--primary)" strokeWidth={1} />
                          </motion.div>
                        </div>
                        <div
                          style={{
                            fontFamily: 'var(--font-orbitron)',
                            fontSize: '1.25rem',
                            letterSpacing: '0.2em',
                            color: 'var(--primary)',
                          }}
                        >
                          CHOOSE SOUND FILE
                        </div>
                        <div
                          style={{
                            color: 'var(--text-muted)',
                            fontSize: '1rem',
                            marginTop: '1.2rem',
                            fontWeight: '500',
                          }}
                        >
                          Drag a sound file here or click to browse.
                        </div>
                      </motion.div>
                    ) : (
                      <motion.div
                        key="file"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        style={{ width: '80%', textAlign: 'center' }}
                      >
                        <div
                          style={{
                            marginBottom: '2.5rem',
                            display: 'flex',
                            justifyContent: 'center',
                            gap: '2rem',
                          }}
                        >
                          <div
                            style={{
                              width: '120px',
                              height: '120px',
                              background: 'rgba(0,242,255,0.03)',
                              borderRadius: '24px',
                              border: '1px solid var(--border)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}
                          >
                            <FileAudio size={48} color="var(--primary)" />
                          </div>
                          <div
                            style={{
                              textAlign: 'left',
                              display: 'flex',
                              flexDirection: 'column',
                              justifyContent: 'center',
                            }}
                          >
                            <div
                              style={{
                                fontFamily: 'var(--font-orbitron)',
                                fontSize: '1.1rem',
                                color: 'var(--primary)',
                                marginBottom: '0.5rem',
                              }}
                            >
                              SELECTED SOUND FILE
                            </div>
                            <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                              {file.name}
                            </div>
                            <div
                              style={{
                                fontSize: '0.8rem',
                                color: 'var(--text-muted)',
                                marginTop: '0.3rem',
                              }}
                            >
                              {(file.size / 1024).toFixed(1)} KB
                            </div>

                            <div style={{ display: 'flex', gap: '1.2rem', marginTop: '1.5rem' }}>
                              <motion.button
                                whileHover={{ scale: 1.05 }}
                                onClick={togglePlay}
                                style={{
                                  background: isPlaying ? 'rgba(0,242,255,0.2)' : 'var(--primary)',
                                  border: 'none',
                                  color: isPlaying ? 'var(--primary)' : '#000',
                                  padding: '0.6rem 1.2rem',
                                  borderRadius: '8px',
                                  cursor: 'pointer',
                                  fontSize: '0.85rem',
                                  fontWeight: 'bold',
                                  fontFamily: 'var(--font-orbitron)',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '0.5rem',
                                }}
                              >
                                {isPlaying ? (
                                  <Square size={14} fill="currentColor" />
                                ) : (
                                  <ChevronRight size={18} fill="currentColor" />
                                )}
                                {isPlaying ? 'PAUSE' : 'PLAY'}
                                {isPlaying && (
                                  <motion.div
                                    layoutId="play-glow"
                                    className="btn-glow-pulse"
                                    style={{
                                      position: 'absolute',
                                      inset: 0,
                                      borderRadius: '8px',
                                      border: '1px solid var(--primary)',
                                      pointerEvents: 'none',
                                    }}
                                  />
                                )}
                              </motion.button>

                              <motion.button
                                whileHover={{ scale: 1.05 }}
                                onClick={() => fileInputRef.current?.click()}
                                style={{
                                  background: 'rgba(255,255,255,0.05)',
                                  border: '1px solid var(--border)',
                                  color: 'var(--text)',
                                  padding: '0.6rem 1.2rem',
                                  borderRadius: '8px',
                                  cursor: 'pointer',
                                  fontSize: '0.85rem',
                                  fontWeight: 'bold',
                                  fontFamily: 'var(--font-orbitron)',
                                }}
                              >
                                CHANGE
                              </motion.button>

                              <motion.button
                                whileHover={{
                                  scale: 1.05,
                                  color: '#ff4444',
                                  borderColor: '#ff4444',
                                }}
                                onClick={clearFile}
                                style={{
                                  background: 'rgba(255,68,68,0.05)',
                                  border: '1px solid rgba(255,68,68,0.3)',
                                  color: 'rgba(255,68,68,0.8)',
                                  padding: '0.6rem 1.2rem',
                                  borderRadius: '8px',
                                  cursor: 'pointer',
                                  fontSize: '0.85rem',
                                  fontWeight: 'bold',
                                  fontFamily: 'var(--font-orbitron)',
                                }}
                              >
                                CLEAR
                              </motion.button>
                            </div>
                          </div>
                        </div>
                        <div
                          style={{
                            width: '100%',
                            height: '4px',
                            background: 'rgba(255,255,255,0.05)',
                            borderRadius: '2px',
                            position: 'relative',
                            overflow: 'hidden',
                          }}
                        >
                          <motion.div
                            initial={{ width: '0%' }}
                            animate={{ width: loading ? `${scanProgress}%` : '100%' }}
                            style={{
                              height: '100%',
                              background: 'var(--primary)',
                              boxShadow: '0 0 15px var(--primary)',
                            }}
                          />
                        </div>
                        <div
                          style={{
                            marginTop: '1.2rem',
                            display: 'flex',
                            justifyContent: 'space-between',
                            fontSize: '0.75rem',
                            color: 'var(--text-muted)',
                            fontFamily: 'var(--font-orbitron)',
                          }}
                        >
                          <span>0.0s</span>
                          <span>{loading ? 'WAITING FOR RESPONSE' : 'READY TO ANALYZE'}</span>
                          <span>{file.size} Bytes</span>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                  <input
                    type="file"
                    aria-label="Engine sound file"
                    accept="audio/*"
                    hidden
                    onChange={handleFileSelect}
                    ref={fileInputRef}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                  <div className="control-card">
                    <div className="hud-title">
                      <Mic size={16} /> Use Microphone
                    </div>
                    <button
                      className={`btn-cyber ${recording ? 'active' : ''}`}
                      onClick={recording ? stopRecording : startRecording}
                    >
                      {recording ? <Square size={18} fill="currentColor" /> : <Mic size={18} />}
                      {recording ? 'STOP RECORDING' : 'START RECORDING'}
                    </button>
                  </div>
                  <div className="control-card">
                    <div className="hud-title">
                      <Cpu size={16} /> AI Analysis
                    </div>
                    <button
                      className={`btn-cyber ${file && !loading ? 'active' : ''}`}
                      onClick={handlePredict}
                      disabled={!file || loading}
                      style={{
                        cursor: !file || loading ? 'not-allowed' : 'pointer',
                        opacity: !file || loading ? 0.5 : 1,
                      }}
                    >
                      {loading ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                          <RefreshCcw size={18} className="spin" />
                          <span>{statusMsg}...</span>
                        </div>
                      ) : (
                        'CHECK FOR FAULTS'
                      )}
                    </button>
                  </div>
                </div>
              </div>

              <div className="controls-panel">
                <ResultCard result={result} />
                <div className="control-card" style={{ flex: 1 }}>
                  <div className="hud-title">
                    <Clock size={16} /> Past Checks
                  </div>
                  <div
                    style={{
                      overflowY: 'auto',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '1.2rem',
                    }}
                  >
                    {history.length > 0 ? (
                      history.map((item) => (
                        <div
                          key={item.id}
                          style={{
                            padding: '1.2rem',
                            background: 'rgba(255,255,255,0.02)',
                            borderRadius: '14px',
                            border: '1px solid var(--border)',
                            display: 'flex',
                            justifyContent: 'space-between',
                          }}
                        >
                          <div>
                            <div style={{ fontSize: '1rem', fontWeight: '700' }}>{item.class}</div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                              {item.system}
                            </div>
                          </div>
                          <div
                            style={{
                              fontSize: '0.85rem',
                              color: 'var(--primary)',
                              fontWeight: '800',
                            }}
                          >
                            {item.confidence}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div style={{ padding: '3rem 0', textAlign: 'center', opacity: 0.3 }}>
                        <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                          No past checks found.
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'analytics' && (
            <StatisticsPanel history={history} modelReady={modelReady} />
          )}
          {activeTab === 'database' && <RecordsPanel history={history} />}
          {activeTab === 'settings' && (
            <SettingsPanel theme={theme} toggleTheme={toggleTheme} modelReady={modelReady} />
          )}

          {error && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              style={{
                position: 'fixed',
                bottom: '2rem',
                right: '2rem',
                padding: '1rem 2rem',
                background: 'rgba(255,0,0,0.1)',
                border: '1px solid rgba(255,0,0,0.2)',
                borderRadius: '12px',
                color: '#ff4444',
                fontSize: '1rem',
                zIndex: 100,
              }}
            >
              <AlertCircle size={18} /> {error}
            </motion.div>
          )}
        </section>
      </main>
    </div>
  )
}
