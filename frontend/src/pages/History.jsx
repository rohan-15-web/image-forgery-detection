import React from 'react';
import { Image as ImageIcon } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function History() {
  const historyData = [
    { id: 1, name: 'img1.jpg', date: '6/1/2026', result: 'Forged' },
    { id: 2, name: 'img2.jpg', date: '7/1/2026', result: 'Genuine' },
    { id: 3, name: 'img3.jpg', date: '7/1/2026', result: 'Forged' }
  ];

  return (
    <div className="p-8">
      <div className="bg-white rounded-t-lg overflow-hidden shadow">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-[#2B2D66] text-gray-800">
              <th className="py-4 px-6 font-medium border-r border-[#3b3d8c]">Image</th>
              <th className="py-4 px-6 font-medium border-r border-[#3b3d8c]">Date</th>
              <th className="py-4 px-6 font-medium border-r border-[#3b3d8c]">Result</th>
              <th className="py-4 px-6 font-medium">Action</th>
            </tr>
          </thead>
          <tbody>
            {historyData.map((item, index) => (
              <tr key={item.id} className="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                <td className="py-4 px-6 flex items-center gap-3">
                  <div className="w-8 h-8 bg-gray-200 rounded flex items-center justify-center">
                    <ImageIcon className="w-5 h-5 text-gray-700" />
                  </div>
                  <span className="font-mono text-sm">{item.name}</span>
                </td>
                <td className="py-4 px-6 text-sm">{item.date}</td>
                <td className="py-4 px-6 text-sm">{item.result}</td>
                <td className="py-4 px-6 text-sm">
                  <Link to="#" className="underline hover:text-blue-600">View</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
