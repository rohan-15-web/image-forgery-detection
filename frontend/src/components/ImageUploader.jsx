import React, { useCallback } from 'react';

export default function ImageUploader({ onUpload, loading }) {
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    if (loading) return;
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) onUpload(file);
  }, [loading, onUpload]);

  const handleChange = (e) => {
    if (loading) return;
    const file = e.target.files[0];
    if (file) onUpload(file);
  };

  return (
    <div 
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      className={`border-2 border-dashed rounded-xl p-10 text-center transition-all ${
        loading ? 'border-gray-600 bg-gray-900/50 cursor-not-allowed' : 'border-blue-500 hover:border-blue-400 hover:bg-gray-800/80 cursor-pointer'
      }`}
    >
      <input 
        type="file" 
        accept="image/png, image/jpeg, image/jpg" 
        onChange={handleChange} 
        className="hidden" 
        id="image-upload" 
        disabled={loading}
      />
      <label htmlFor="image-upload" className={loading ? 'cursor-not-allowed' : 'cursor-pointer'}>
        <div className="mx-auto flex justify-center mb-4">
          <svg className="w-16 h-16 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
        </div>
        <p className="text-lg text-gray-300 font-semibold mb-2">Drag & Drop your image here</p>
        <p className="text-sm text-gray-500">or click to browse (JPG, PNG)</p>
      </label>
    </div>
  );
}
