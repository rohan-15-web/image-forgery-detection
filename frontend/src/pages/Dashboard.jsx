import React, { useState } from 'react';
import ImageUploader from '../components/ImageUploader';
import ResultDisplay from '../components/ResultDisplay';
import { analyzeImage } from '../services/api';

export default function Dashboard() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [originalImage, setOriginalImage] = useState(null);

  const handleUpload = async (file) => {
    setLoading(true);
    setError(null);
    setResult(null);
    
    const imageUrl = URL.createObjectURL(file);
    setOriginalImage(imageUrl);

    try {
      const data = await analyzeImage(file);
      setResult(data);
    } catch (err) {
      setError(err.message || 'An error occurred during analysis');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-8">
      <header className="mb-12 text-center">
        <h1 className="text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600 mb-4">
          Image Forgery Detection
        </h1>
        <p className="text-gray-500">Advanced AI system detecting Copy-Move, Splicing, and Retouching forgeries.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-gray-800 rounded-xl p-6 shadow-2xl border border-gray-300">
          <h2 className="text-xl font-bold mb-6 border-b border-gray-300 pb-2">Upload Analysis Image</h2>
          <ImageUploader onUpload={handleUpload} loading={loading} />
        </div>
        
        <div className="bg-gray-800 rounded-xl p-6 shadow-2xl border border-gray-300">
          <h2 className="text-xl font-bold mb-6 border-b border-gray-300 pb-2">Analysis Results</h2>
          {error && <div className="bg-red-900/50 border border-red-500 text-red-200 p-4 rounded-lg">{error}</div>}
          {!result && !loading && !error && (
            <div className="h-64 flex items-center justify-center text-gray-500 border-2 border-dashed border-gray-300 rounded-lg">
              Upload an image to see results
            </div>
          )}
          {loading && (
            <div className="h-64 flex flex-col items-center justify-center text-blue-400">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
              <p>Analyzing image through ensemble models...</p>
            </div>
          )}
          {result && !loading && (
            <ResultDisplay result={result} originalImage={originalImage} />
          )}
        </div>
      </div>
    </div>
  );
}
