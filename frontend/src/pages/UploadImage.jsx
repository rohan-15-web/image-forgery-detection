import { useState, useRef } from 'react'
import { Upload, AlertTriangle, CheckCircle, RefreshCw, Download } from 'lucide-react'
import axios from 'axios'

const API = ''

export default function UploadImage() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const fileRef = useRef()

  const handleFile = (f) => {
    if (!f) return
    setFile(f)
    setResult(null)
    setError('')
    const reader = new FileReader()
    reader.onload = e => setPreview(e.target.result)
    reader.readAsDataURL(f)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  const handleAnalyze = async () => {
    if (!file) return
    setAnalyzing(true)
    setError('')
    setResult(null)

    const formData = new FormData()
    formData.append('image', file)

    try {
      const res = await axios.post(`${API}/api/predict`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      setResult(res.data)
    } catch (err) {
      if (err.code === 'ERR_NETWORK' || !err.response) {
        setError('Could not connect to the backend server. Please ensure the Python backend is running on port 5000.')
      } else {
        setError(err.response?.data?.error || 'Analysis failed. Please try again.')
      }
    } finally {
      setAnalyzing(false)
    }
  }

  const handleReset = () => {
    setFile(null)
    setPreview(null)
    setResult(null)
    setError('')
  }

  const predClass = (p) => {
    if (!p) return ''
    const l = p.toLowerCase()
    if (l === 'authentic') return 'authentic'
    if (l === 'forged') return 'forged'
    return l.replace('-', '-')
  }

  const fillClass = (p) => {
    if (!p) return 'fill-other'
    const l = p.toLowerCase()
    if (l === 'authentic') return 'fill-authentic'
    if (l === 'forged' || l.includes('move') || l.includes('splicing') || l.includes('ai')) return 'fill-forged'
    return 'fill-other'
  }

  return (
    <div className="page-container">
      <h1 className="page-title">Upload Image for Forgery Detection</h1>
      <p className="page-subtitle">Upload an image to analyze it for signs of forgery using AI</p>

      {!result && (
        <div className="upload-card">
          {!file ? (
            <div
              className={`upload-area${dragOver ? ' drag-over' : ''}`}
              onDragOver={e => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current.click()}
            >
              <div className="upload-icon">
                <Upload size={32} color="white" />
              </div>
              <h3>Drag & Drop your image here</h3>
              <p>or click to browse from your computer</p>
              <div className="upload-formats">
                {['JPG', 'PNG', 'JPEG', 'BMP', 'TIFF'].map(f => (
                  <span className="format-tag" key={f}>{f}</span>
                ))}
              </div>
              <input
                ref={fileRef}
                id="file-input"
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={e => handleFile(e.target.files[0])}
              />
            </div>
          ) : (
            <>
              {analyzing ? (
                <div className="analyzing-overlay">
                  <div className="spinner-ring" />
                  <p className="analyzing-text">Analyzing Image...</p>
                  <p className="analyzing-sub">Running AI-powered forgery detection</p>
                </div>
              ) : (
                <>
                  <div className="preview-container">
                    <img src={preview} alt="Preview" />
                  </div>
                  {error && <div className="alert alert-error" style={{ margin: '12px 0' }}>{error}</div>}
                  <div className="upload-actions">
                    <button id="analyze-btn" className="btn-analyze" onClick={handleAnalyze}>
                      Analyze Image
                    </button>
                    <button className="btn btn-outline" onClick={handleReset}>
                      <RefreshCw size={15} /> Change Image
                    </button>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      )}

      {result && (
        <div className="result-card">
          <div className="result-badge-wrap">
            <span className={`result-badge ${predClass(result.prediction)}`}>
              {result.prediction === 'AUTHENTIC'
                ? <CheckCircle size={18} />
                : <AlertTriangle size={18} />
              }
              {result.prediction}
            </span>
          </div>

          <div className="confidence-bar-wrap">
            <div className="confidence-label">
              <span>Confidence Score</span>
              <span style={{ fontWeight: 700 }}>{result.confidence}%</span>
            </div>
            <div className="confidence-bar">
              <div
                className={`confidence-fill ${fillClass(result.prediction)}`}
                style={{ width: `${result.confidence}%` }}
              />
            </div>
          </div>

          <div className="result-images">
            <div className="result-image-box">
              <h4>Original Image</h4>
              {result.original_image_url
                ? <img src={`${API}${result.original_image_url}`} alt="Original" />
                : <img src={preview} alt="Original" />
              }
            </div>
            <div className="result-image-box">
              <h4>Forgery Heatmap</h4>
              {result.heatmap_image_url
                ? <img src={`${API}${result.heatmap_image_url}`} alt="Heatmap" />
                : <div className="no-heatmap">No forgery detected — image appears authentic</div>
              }
            </div>
          </div>

          <div className="result-actions">
            <button id="analyze-new-btn" className="btn-analyze" onClick={handleReset}>
              Analyze New Image
            </button>
            {result.heatmap_image_url && (
              <a
                id="download-report-btn"
                className="btn btn-outline"
                href={`${API}${result.heatmap_image_url}`}
                download
              >
                <Download size={15} /> Download Report
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
