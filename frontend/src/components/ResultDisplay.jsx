import React from 'react';

export default function ResultDisplay({ result, originalImage }) {
  const backendUrl = "";
  const { forgery_type, confidence, all_scores, heatmap_url } = result;

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="p-4 bg-gray-900 rounded-lg border border-gray-300">
        <h3 className="text-sm text-gray-500 uppercase tracking-wider mb-1">Detected Category</h3>
        <div className="flex items-end gap-4">
          <span className="text-3xl font-bold text-blue-400">{forgery_type}</span>
          <span className="text-xl font-semibold text-green-400">{confidence}% Confidence</span>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-3 text-gray-300">Model Scores</h3>
        <div className="space-y-3">
          {Object.entries(all_scores).map(([key, score]) => (
            <div key={key}>
              <div className="flex justify-between text-sm mb-1">
                <span className="capitalize">{key.replace('_', ' ')}</span>
                <span>{score}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full" 
                  style={{ width: `${score}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-3 text-gray-300">Forgery Localization</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-lg overflow-hidden border border-gray-600">
            <p className="text-xs text-center py-1 bg-gray-700">Original</p>
            <img src={originalImage} alt="Original" className="w-full h-auto object-cover aspect-square" />
          </div>
          <div className="rounded-lg overflow-hidden border border-gray-600 relative">
            <p className="text-xs text-center py-1 bg-gray-700">Heatmap</p>
            <img 
              src={`${backendUrl}${heatmap_url}`} 
              alt="Heatmap" 
              className="w-full h-auto object-cover aspect-square" 
            />
          </div>
        </div>
      </div>
    </div>
  );
}
