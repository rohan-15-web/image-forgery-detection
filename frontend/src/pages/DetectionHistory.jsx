import { useEffect, useState } from 'react'
import { ImageIcon, X, Download, AlertTriangle, CheckCircle, Clock, ShieldCheck } from 'lucide-react'
import axios from 'axios'

const API = ''

export default function DetectionHistory() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await axios.get(`${API}/api/history`)
        setRecords(res.data)
      } catch (err) {
        console.error('Failed to fetch history', err)
      } finally {
        setLoading(false)
      }
    }
    fetchHistory()
  }, [])

  const badgeClass = (pred) => {
    if (!pred) return 'bg-gray-800 text-gray-300 border border-gray-300'
    const l = pred.toLowerCase()
    if (l === 'authentic') return 'bg-green-500/20 text-green-400 border border-green-500/30'
    return 'bg-red-500/20 text-red-400 border border-red-500/30'
  }

  return (
    <div className="max-w-6xl mx-auto p-4 animate-in fade-in duration-500">
      <div className="mb-10 text-center md:text-left">
        <h1 className="text-3xl font-extrabold text-gray-800 mb-2 flex items-center justify-center md:justify-start gap-3">
          <Clock className="text-[#2A3042] w-8 h-8" /> 
          Detection History
        </h1>
        <p className="text-gray-500">All previously analyzed images and their detailed results.</p>
      </div>

      <div className="bg-white backdrop-blur-md rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
        <div className="p-6 border-b border-gray-200 flex justify-between items-center bg-gray-100/50">
          <h3 className="text-lg font-bold text-gray-800">Upload Image History</h3>
          <span className="text-sm text-[#2A3042] font-semibold px-3 py-1 bg-blue-50 rounded-full">{records.length} records</span>
        </div>

        {loading ? (
          <div className="p-20 flex flex-col items-center justify-center">
            <div className="w-12 h-12 border-4 border-gray-200 border-t-brand-teal rounded-full animate-spin mb-4"></div>
            <p className="text-gray-500">Loading history...</p>
          </div>
        ) : records.length === 0 ? (
          <div className="p-20 flex flex-col items-center justify-center text-center">
            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center border border-gray-200 mb-6">
              <ImageIcon className="w-10 h-10 text-gray-600" />
            </div>
            <p className="text-xl font-bold text-gray-800 mb-2">No images analyzed yet.</p>
            <p className="text-gray-500">Upload an image to get started with forgery detection.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-100/80 text-gray-500 text-sm uppercase tracking-wider">
                  <th className="p-4 font-semibold border-b border-gray-200">Image</th>
                  <th className="p-4 font-semibold border-b border-gray-200">Date</th>
                  <th className="p-4 font-semibold border-b border-gray-200">Result</th>
                  <th className="p-4 font-semibold border-b border-gray-200">Action</th>
                </tr>
              </thead>
              <tbody>
                {records.map(r => (
                  <tr key={r.id} className="border-b border-gray-200/50 hover:bg-gray-100/30 transition-colors">
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center border border-gray-200 shrink-0">
                          <ImageIcon size={18} className="text-[#2A3042]" />
                        </div>
                        <span className="font-medium text-gray-200 truncate max-w-[200px]" title={r.filename}>{r.filename}</span>
                      </div>
                    </td>
                    <td className="p-4 text-gray-500 whitespace-nowrap">{r.upload_date}</td>
                    <td className="p-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider inline-flex items-center gap-1 ${badgeClass(r.prediction)}`}>
                        {r.prediction?.toLowerCase() === 'authentic' ? <CheckCircle size={12} /> : <AlertTriangle size={12} />}
                        {r.prediction}
                      </span>
                    </td>
                    <td className="p-4">
                      <button
                        className="text-[#2A3042] hover:text-gray-800 font-medium text-sm transition-colors px-4 py-2 border border-blue-200 hover:bg-[#2A3042] hover:border-[#2A3042] rounded-lg"
                        onClick={() => setSelected(r)}
                      >
                        View Report
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* REPORT MODAL */}
      {selected && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setSelected(null)}>
          <div className="bg-white border border-gray-300 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="sticky top-0 bg-white/95 backdrop-blur z-10 border-b border-gray-200 p-6 flex justify-between items-center">
              <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                <ShieldCheck className="text-[#2A3042]" /> Image Forgery Detection Report
              </h3>
              <button className="text-gray-500 hover:text-gray-800 hover:bg-gray-800 p-2 rounded-full transition-colors" onClick={() => setSelected(null)}>
                <X size={24} />
              </button>
            </div>

            <div className="p-6">
              {selected.original_image_url && (
                <div className="mb-6 rounded-xl overflow-hidden border border-gray-200 bg-gray-100 max-h-64 flex justify-center">
                  <img
                    className="max-w-full max-h-64 object-contain"
                    src={`${API}${selected.original_image_url}`}
                    alt="Original"
                  />
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="bg-gray-100/50 p-4 rounded-xl border border-gray-200">
                  <label className="text-xs text-gray-500 uppercase font-semibold mb-1 block">Image Name</label>
                  <span className="text-gray-800 font-medium truncate block" title={selected.filename}>{selected.filename}</span>
                </div>
                <div className="bg-gray-100/50 p-4 rounded-xl border border-gray-200">
                  <label className="text-xs text-gray-500 uppercase font-semibold mb-1 block">Detection Result</label>
                  <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider ${badgeClass(selected.prediction)}`}>{selected.prediction}</span>
                </div>
                <div className="bg-gray-100/50 p-4 rounded-xl border border-gray-200">
                  <label className="text-xs text-gray-500 uppercase font-semibold mb-1 block">Confidence Score</label>
                  <span className="text-gray-800 font-bold text-lg">{selected.confidence}%</span>
                </div>
                <div className="bg-gray-100/50 p-4 rounded-xl border border-gray-200">
                  <label className="text-xs text-gray-500 uppercase font-semibold mb-1 block">Analysis Date</label>
                  <span className="text-gray-300 text-sm">{selected.upload_date}</span>
                </div>
              </div>

              {selected.prediction !== 'AUTHENTIC' && selected.heatmap_image_url && (
                <div className="mb-8">
                  <p className="text-xs text-[#2A3042] uppercase font-bold tracking-wider mb-3 flex items-center gap-2">
                    <AlertTriangle size={14} /> Forgery Heatmap
                  </p>
                  <div className="rounded-xl overflow-hidden border border-red-500/30 bg-gray-100 max-h-80 flex justify-center shadow-[0_0_20px_rgba(239,68,68,0.1)]">
                    <img
                      className="max-w-full max-h-80 object-contain"
                      src={`${API}${selected.heatmap_image_url}`}
                      alt="Heatmap"
                    />
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
                <button
                  className="px-6 py-2 rounded-lg font-medium text-gray-300 hover:text-gray-800 border border-gray-300 hover:bg-gray-800 transition-colors"
                  onClick={() => setSelected(null)}
                >
                  Close
                </button>
                {selected.heatmap_image_url && (
                  <a
                    className="flex items-center gap-2 px-6 py-2 rounded-lg font-bold bg-[#2A3042] hover:bg-[#2A3042]-light text-white shadow-[0_0_15px_rgba(69,184,172,0.3)] transition-all"
                    href={`${API}${selected.heatmap_image_url}`}
                    download
                  >
                    <Download size={16} /> Download Report
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
