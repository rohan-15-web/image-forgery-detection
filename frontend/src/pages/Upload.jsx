import React, { useState } from 'react';
import { Upload as UploadIcon, Image as ImageIcon, Loader2, Download, AlertCircle, ShieldCheck } from 'lucide-react';
import { analyzeImage } from '../services/api';

export default function Upload() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [originalImage, setOriginalImage] = useState(null);

  const handleFile = (selectedFile) => {
    if (selectedFile && selectedFile.type.startsWith('image/')) {
      setFile(selectedFile);
      setOriginalImage(URL.createObjectURL(selectedFile));
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    handleFile(droppedFile);
  };

  const onAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const data = await analyzeImage(file);
      setResult(data);
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    const backendUrl = "";
    const isAuthentic = result.forgery_type === 'Authentic';
    
    return (
      <div className="flex justify-center items-start min-h-[calc(100vh-64px)] p-4 print:p-0 print:block">
        <div className="bg-white backdrop-blur-md rounded-2xl shadow-xl border border-gray-200 p-8 w-full max-w-5xl print:bg-white print:text-black print:shadow-none print:border-none print:p-0">
          <div className="flex items-center justify-between mb-8 pb-6 border-b border-gray-200 print:border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 print:text-black flex items-center gap-3">
              {isAuthentic ? <ShieldCheck className="text-green-500 print:text-green-600 w-8 h-8" /> : <AlertCircle className="text-red-500 print:text-red-600 w-8 h-8" />}
              Detection Report
            </h2>
            <span className={`px-4 py-1.5 rounded-full text-sm font-bold tracking-wider ${isAuthentic ? 'bg-green-500/20 text-green-400 border border-green-500/30 print:text-green-700 print:border-green-600' : 'bg-red-500/20 text-red-400 border border-red-500/30 print:text-red-700 print:border-red-600'}`}>
              {isAuthentic ? 'VERIFIED AUTHENTIC' : 'FORGERY DETECTED'}
            </span>
          </div>
          
          <div className="flex flex-col md:flex-row print:flex-col gap-10 print:gap-6">
            <div className="flex-1 space-y-6 print:space-y-4">
              <div className="bg-gray-100 rounded-xl p-5 border border-gray-200 print:bg-gray-50 print:border-gray-200">
                <p className="text-xs text-[#2A3042] print:text-gray-500 font-semibold uppercase mb-1">Image name</p>
                <p className="font-medium text-gray-800 print:text-black break-all">{file?.name}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-100 rounded-xl p-5 border border-gray-200 print:bg-gray-50 print:border-gray-200">
                  <p className="text-xs text-[#2A3042] print:text-gray-500 font-semibold uppercase mb-1">Confidence</p>
                  <p className="font-bold text-2xl text-gray-800 print:text-black">{result.confidence}%</p>
                </div>
                
                <div className="bg-gray-100 rounded-xl p-5 border border-gray-200 print:bg-gray-50 print:border-gray-200">
                  <p className="text-xs text-[#2A3042] print:text-gray-500 font-semibold uppercase mb-1">Forgery Type</p>
                  <p className="font-bold text-lg text-gray-800 print:text-black">{result.forgery_type}</p>
                </div>
              </div>

              <div className="bg-gray-100 rounded-xl p-5 border border-gray-200 print:bg-gray-50 print:border-gray-200">
                <p className="text-xs text-[#2A3042] print:text-gray-500 font-semibold uppercase mb-1">Analysis Date</p>
                <p className="font-medium text-gray-800 print:text-black">{new Date().toLocaleString()}</p>
              </div>
              
              <div className="pt-6 flex gap-4 print:hidden">
                <button 
                  onClick={() => window.print()}
                  className="flex-1 flex items-center justify-center gap-2 bg-[#2A3042] hover:bg-[#2A3042]-light text-white font-bold py-3 px-6 rounded-xl shadow-[0_0_20px_rgba(69,184,172,0.2)] transition-all"
                >
                  <Download size={18} />
                  Download Report
                </button>
                <button 
                  onClick={() => {setResult(null); setFile(null); setOriginalImage(null);}}
                  className="flex-1 flex items-center justify-center gap-2 bg-transparent border border-gray-600 hover:border-white text-gray-300 hover:text-gray-800 font-bold py-3 px-6 rounded-xl transition-all"
                >
                  Analyze Another
                </button>
              </div>
            </div>
            
            <div className="flex-[1.5] grid grid-cols-1 md:grid-cols-2 print:grid-cols-2 gap-6 print:gap-4 print:items-start">
              <div className="flex flex-col">
                <p className="text-sm text-gray-500 print:text-gray-600 mb-3 font-medium flex items-center gap-2">
                  <ImageIcon size={16} /> Original Input
                </p>
                <div className="border border-gray-200 print:border-gray-300 rounded-xl overflow-hidden bg-gray-100/50 print:bg-transparent flex-1 flex items-center justify-center min-h-[250px] print:min-h-0">
                  <img src={originalImage} alt="Original" className="max-w-full max-h-[350px] print:max-h-[300px] object-contain" />
                </div>
              </div>
              {result.forgery_type !== 'Authentic' && (result.heatmap_image_url || result.heatmap_url) && (
                <div className="flex flex-col">
                  <p className="text-sm text-gray-500 print:text-gray-600 mb-3 font-medium flex items-center gap-2">
                    <AlertCircle size={16} /> Analysis Heatmap
                  </p>
                  <div className="border border-gray-200 print:border-gray-300 rounded-xl overflow-hidden bg-gray-100/50 print:bg-transparent flex-1 flex items-center justify-center min-h-[250px] print:min-h-0">
                    <img src={`${backendUrl}${result.heatmap_image_url || result.heatmap_url}`} alt="Heatmap" className="max-w-full max-h-[350px] print:max-h-[300px] object-contain" />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[calc(100vh-64px)] p-4">
        <div className="bg-white backdrop-blur-md rounded-2xl shadow-[0_0_40px_rgba(69,184,172,0.1)] border border-blue-200 p-12 text-center w-full max-w-md">
          <div className="relative w-24 h-24 mx-auto mb-8">
            <div className="absolute inset-0 border-4 border-gray-200 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-[#2A3042] rounded-full border-t-transparent animate-spin"></div>
            <ShieldCheck className="absolute inset-0 m-auto text-[#2A3042] w-8 h-8 animate-pulse" />
          </div>
          <h2 className="text-2xl font-bold mb-3 text-gray-800 tracking-wide">Processing Image</h2>
          <p className="text-sm text-gray-500">Our deep learning models are analyzing patterns, compression artifacts, and noise discrepancies...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-center items-center min-h-[calc(100vh-64px)] p-4">
      <div className="bg-white backdrop-blur-md rounded-2xl shadow-[0_0_40px_rgba(0,0,0,0.3)] border border-gray-200 p-10 w-full max-w-2xl text-center">
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center border border-blue-200">
            <UploadIcon className="w-8 h-8 text-[#2A3042]" />
          </div>
        </div>
        <h2 className="text-2xl font-bold mb-2 text-gray-800">Upload Image for Analysis</h2>
        <p className="text-gray-500 mb-8">Detect advanced splicing, copy-move, and face-retouching forgeries.</p>
        
        <div 
          onDrop={onDrop}
          onDragOver={(e) => e.preventDefault()}
          className="border-2 border-dashed border-gray-300 rounded-2xl p-12 mb-8 bg-gray-100 hover:bg-gray-900 transition-colors cursor-pointer"
        >
          {file ? (
            <div className="flex flex-col items-center">
              <div className="relative">
                <img src={originalImage} alt="Preview" className="w-32 h-32 object-cover rounded-xl mb-4 border border-gray-300 shadow-lg" />
                <button 
                  onClick={(e) => { e.stopPropagation(); setFile(null); setOriginalImage(null); }}
                  className="absolute -top-3 -right-3 bg-red-500 text-gray-800 rounded-full w-8 h-8 flex items-center justify-center hover:bg-red-600 shadow-md"
                >
                  ✕
                </button>
              </div>
              <p className="text-lg font-medium text-gray-800 truncate max-w-[250px]">{file.name}</p>
              <p className="text-sm text-[#2A3042] mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <ImageIcon className="w-14 h-14 text-gray-600 mb-4" />
              <p className="text-lg font-medium text-gray-800">Drag & Drop your image here</p>
              <p className="text-sm text-gray-500 mt-2 mb-6">Supported formats: JPEG, PNG, WEBP</p>
              <input 
                type="file" 
                accept="image/*" 
                className="hidden" 
                id="file-upload" 
                onChange={(e) => handleFile(e.target.files[0])}
              />
              <label 
                htmlFor="file-upload" 
                className="border border-[#2A3042] text-[#2A3042] hover:bg-blue-50 px-8 py-3 rounded-xl cursor-pointer transition-all font-bold shadow-[0_0_15px_rgba(69,184,172,0.1)]"
              >
                Browse Files
              </label>
            </div>
          )}
        </div>

        <button 
          onClick={onAnalyze}
          disabled={!file}
          className={`w-full py-4 rounded-xl font-bold shadow-[0_0_20px_rgba(69,184,172,0.2)] transition-all flex justify-center items-center gap-2 ${
            file 
              ? 'bg-[#2A3042] hover:bg-[#2A3042]-light text-white' 
              : 'bg-gray-800 text-gray-500 cursor-not-allowed border border-gray-300 shadow-none'
          }`}
        >
          <ShieldCheck size={20} />
          {file ? 'Run Detection Analysis' : 'Select an image to continue'}
        </button>
      </div>
    </div>
  );
}
