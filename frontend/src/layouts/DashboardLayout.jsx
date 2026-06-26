import React, { useEffect, useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { ShieldCheck, LogOut, LayoutDashboard, UploadCloud, History } from 'lucide-react';

export default function DashboardLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  useEffect(() => {
    const currentUser = localStorage.getItem('currentUser');
    if (currentUser) {
      setUser(JSON.parse(currentUser));
    } else {
      navigate('/');
    }
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('currentUser');
    navigate('/');
  };

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
    { name: 'Upload image', path: '/dashboard/upload', icon: <UploadCloud size={20} /> },
    { name: 'Detection History', path: '/dashboard/history', icon: <History size={20} /> },
  ];

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden font-sans text-gray-800 relative">
      {/* Sidebar */}
      <aside className="w-64 bg-[#2A3042] border-r border-[#2A3042] flex flex-col text-white z-20 print:hidden">
        <div className="p-6 border-b border-[#1E2331] flex items-center gap-3">
          <ShieldCheck className="text-white w-8 h-8" />
          <h2 className="text-lg font-bold tracking-wider text-white">FORGE<br/><span className="text-gray-300 text-sm">DETECT</span></h2>
        </div>
        
        <nav className="flex-1 mt-6">
          <ul className="space-y-2 px-4">
            {navItems.map((item) => (
              <li key={item.name}>
                <Link
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                    location.pathname === item.path || (item.path === '/dashboard' && location.pathname === '/dashboard/')
                      ? 'bg-white/10 text-white font-bold'
                      : 'hover:bg-white/5 text-gray-400 hover:text-gray-200'
                  }`}
                >
                  {item.icon}
                  <span className="font-medium">{item.name}</span>
                </Link>
              </li>
            ))}
          </ul>
        </nav>
        
        <div className="p-6 mt-auto">
          <div className="bg-[#1E2331] rounded-xl p-4 mb-4">
            <p className="text-xs text-gray-400">Logged in as</p>
            <p className="text-sm font-bold text-white truncate">{user?.name || 'User'}</p>
            <p className="text-xs text-gray-300 truncate">{user?.email}</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 bg-gray-100 print:bg-white print:block">
        {/* Top Navbar */}
        <header className="bg-white shadow-sm border-b border-gray-200 z-10 h-16 flex items-center justify-between px-8 print:hidden">
          <div className="flex items-center space-x-2">
            <div className="flex flex-col">
              <span className="text-sm font-extrabold leading-tight tracking-tight text-gray-800">PROTECT YOUR DIGITAL IDENTITY</span>
              <span className="text-xs text-gray-500 leading-tight">IMAGE FORGERY DETECTION</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-6 text-sm font-medium">
            <Link to="/dashboard/history" className="text-gray-500 hover:text-gray-800 transition-colors">History</Link>
            <Link to="#" className="text-gray-500 hover:text-gray-800 transition-colors">Resources</Link>
            
            <button 
              onClick={handleLogout}
              className="bg-red-600 text-white px-5 py-2 rounded-lg hover:bg-red-700 transition-all font-bold shadow-sm"
            >
              Logout
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto bg-transparent relative p-8 print:overflow-visible print:p-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
