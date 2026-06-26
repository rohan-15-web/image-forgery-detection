import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

export default function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRegister = (e) => {
    e.preventDefault();
    if (!formData.name || !formData.email || !formData.password) {
      setError('All fields are required');
      return;
    }
    
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      return;
    }
    
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    // Save to localStorage to mock a database
    const users = JSON.parse(localStorage.getItem('users') || '[]');
    if (users.find(u => u.email === formData.email)) {
      setError('Email already registered');
      return;
    }
    
    users.push(formData);
    localStorage.setItem('users', JSON.stringify(users));
    localStorage.setItem('currentUser', JSON.stringify(formData));
    
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white backdrop-blur-md rounded-2xl shadow-xl border border-gray-200 p-10 w-full max-w-md text-center">
        <div className="flex justify-center mb-6">
          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center border border-blue-200">
            <div className="w-6 h-6 bg-[#2A3042] rounded-full animate-pulse"></div>
          </div>
        </div>
        <h2 className="text-2xl font-bold mb-2 text-gray-800">Create Account</h2>
        <p className="text-gray-500 mb-8 text-sm">Join to detect image forgeries</p>
        
        {error && <div className="bg-red-500/10 border border-red-500 text-red-500 rounded-lg p-3 mb-6 text-sm">{error}</div>}

        <form onSubmit={handleRegister} className="space-y-5">
          <input
            type="text"
            name="name"
            placeholder="Full Name"
            value={formData.name}
            onChange={handleChange}
            className="w-full px-5 py-3 bg-gray-100 border border-gray-300 text-gray-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent transition-all placeholder-gray-500"
          />
          
          <input
            type="email"
            name="email"
            placeholder="Email Address"
            value={formData.email}
            onChange={handleChange}
            className="w-full px-5 py-3 bg-gray-100 border border-gray-300 text-gray-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent transition-all placeholder-gray-500"
          />
          
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleChange}
            className="w-full px-5 py-3 bg-gray-100 border border-gray-300 text-gray-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-teal focus:border-transparent transition-all placeholder-gray-500"
          />
          
          <button
            type="submit"
            className="w-full bg-[#2A3042] text-white py-3 rounded-xl hover:bg-[#2A3042]-light transition-all font-bold shadow-[0_0_20px_rgba(69,184,172,0.3)] hover:shadow-[0_0_25px_rgba(69,184,172,0.5)] mt-4"
          >
            Register
          </button>
        </form>
        
        <div className="mt-8 text-sm">
          <Link to="/" className="text-gray-500 hover:text-[#2A3042] transition-colors">
            Already have an account? <span className="text-[#2A3042] font-medium">Login</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
