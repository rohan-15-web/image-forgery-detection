import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, EyeOff, Eye, ShieldCheck } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleLogin = (e) => {
    e.preventDefault();
    if (!formData.email || !formData.password) {
      setError('Please enter both email and password');
      return;
    }

    const users = JSON.parse(localStorage.getItem('users') || '[]');
    const user = users.find(u => u.email === formData.email && u.password === formData.password);

    if (user) {
      localStorage.setItem('currentUser', JSON.stringify(user));
      navigate('/dashboard');
    } else {
      setError('Invalid email or password');
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl border border-gray-200 p-10 w-full max-w-md text-center">
        <div className="flex justify-center mb-6">
          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center border border-blue-200">
            <ShieldCheck className="text-[#2A3042] w-6 h-6" />
          </div>
        </div>
        <h2 className="text-2xl font-bold mb-2 text-gray-800">Image forgery detection</h2>
        <p className="text-gray-500 mb-8 text-sm">Login to your dashboard</p>
        
        {error && <div className="bg-red-100 border border-red-400 text-red-600 rounded-lg p-3 mb-6 text-sm">{error}</div>}

        <form onSubmit={handleLogin} className="space-y-5">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Mail className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="email"
              name="email"
              placeholder="Email Address"
              value={formData.email}
              onChange={handleChange}
              className="w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-300 text-gray-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#2A3042] focus:border-transparent transition-all placeholder-gray-400"
            />
          </div>
          
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type={showPassword ? 'text' : 'password'}
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              className="w-full pl-12 pr-12 py-3 bg-gray-50 border border-gray-300 text-gray-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#2A3042] focus:border-transparent transition-all placeholder-gray-400"
            />
            <div 
              className="absolute inset-y-0 right-0 pr-4 flex items-center cursor-pointer text-gray-400 hover:text-gray-600 transition-colors"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <Eye className="h-5 w-5" /> : <EyeOff className="h-5 w-5" />}
            </div>
          </div>
          
          <button
            type="submit"
            className="w-full bg-[#2A3042] text-white py-3 rounded-xl hover:bg-[#1E2331] transition-all font-bold shadow-md hover:shadow-lg mt-4"
          >
            Login
          </button>
        </form>
        
        <div className="mt-8 text-sm">
          <Link to="/register" className="text-gray-500 hover:text-gray-800 transition-colors">
            Create a New Account
          </Link>
        </div>
      </div>
    </div>
  );
}
