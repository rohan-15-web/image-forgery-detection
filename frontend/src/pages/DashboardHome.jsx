import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Image as ImageIcon, AlertTriangle, CheckCircle, Shield } from 'lucide-react';
import axios from 'axios';

const API = '';

export default function DashboardHome() {
  const [stats, setStats] = useState({
    total: 0,
    forged: 0,
    authentic: 0
  });

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await axios.get(`${API}/api/history`);
        const records = res.data;
        const total = records.length;
        const authentic = records.filter(r => r.prediction && r.prediction.toLowerCase() === 'authentic').length;
        const forged = total - authentic;
        setStats({ total, forged, authentic });
      } catch (err) {
        console.error('Failed to fetch history', err);
        // Fallback or read from localStorage if you wanted a purely frontend mock, but API is better
      }
    };
    fetchHistory();
  }, []);

  const statCards = [
    { title: 'Total Analyzed', value: stats.total, icon: <ImageIcon className="w-8 h-8 text-[#2A3042]" />, color: 'border-blue-200' },
    { title: 'Forged Detected', value: stats.forged, icon: <AlertTriangle className="w-8 h-8 text-red-400" />, color: 'border-red-500/30' },
    { title: 'Authentic Verified', value: stats.authentic, icon: <CheckCircle className="w-8 h-8 text-green-400" />, color: 'border-green-500/30' }
  ];

  return (
    <div className="p-2 animate-in fade-in duration-500">
      <div className="mb-10 text-center md:text-left">
        <h1 className="text-3xl font-extrabold text-gray-800 mb-2 flex items-center justify-center md:justify-start gap-3">
          <Shield className="text-[#2A3042] w-10 h-10" /> 
          ForgeDetect Overview
        </h1>
        <p className="text-gray-500">Monitor and analyze images for digital forgery in real-time.</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {statCards.map((stat, idx) => (
          <div key={idx} className={`bg-white backdrop-blur-md p-8 rounded-2xl shadow-lg border ${stat.color} flex items-center justify-between transition-transform hover:scale-105`}>
            <div>
              <p className="text-sm font-semibold text-gray-500 mb-1 uppercase tracking-wider">{stat.title}</p>
              <h3 className="text-4xl font-bold text-gray-800">{stat.value}</h3>
            </div>
            <div className="p-4 bg-gray-100 rounded-full border border-gray-200 shadow-inner">
              {stat.icon}
            </div>
          </div>
        ))}
      </div>

      <div className="flex flex-col items-center bg-white backdrop-blur-md rounded-2xl border border-[#2A3042]/20 p-10 text-center">
        <div className="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center mb-6 border border-blue-200">
          <Shield className="w-10 h-10 text-[#2A3042]" />
        </div>
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Protect Your Digital Identity</h2>
        <p className="text-gray-500 max-w-2xl mb-8">
          Defend against the rising threat of image forgeries with cutting-edge AI technology, designed for seamless integration and real-time accuracy.
        </p>
        <Link 
          to="/dashboard/upload"
          className="bg-[#2A3042] hover:bg-[#2A3042]-light text-white font-bold py-4 px-10 rounded-xl shadow-[0_0_20px_rgba(69,184,172,0.3)] hover:shadow-[0_0_30px_rgba(69,184,172,0.5)] transition-all flex items-center gap-2"
        >
          <ImageIcon className="w-5 h-5" />
          Analyze New Image
        </Link>
      </div>
    </div>
  );
}
