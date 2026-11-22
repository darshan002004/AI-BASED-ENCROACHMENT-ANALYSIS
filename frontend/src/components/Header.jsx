import React, { useState } from 'react';
import { Search, Bell, Menu, Check, LogOut, ChevronDown, Globe, Shield } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';
import { useLanguage } from '../context/LanguageContext';

export default function Header({ onSearch, onSelectIncident, onToggleMobileMenu, pageTitle }) {
  const { user, role, logout } = useAuth();
  const { notifications, unreadCount, markAllRead } = useNotification();
  const { lang, changeLanguage, t } = useLanguage();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
    if (onSearch) onSearch(e.target.value);
  };

  const getRolePill = () => {
    switch (role) {
      case 'admin':
        return { label: 'Admin View', dot: 'bg-blue-600', text: 'text-blue-700', bg: 'bg-blue-50 border-blue-200' };
      case 'officer':
        return { label: 'Officer View', dot: 'bg-emerald-600', text: 'text-emerald-700', bg: 'bg-emerald-50 border-emerald-200' };
      case 'citizen':
      default:
        return { label: 'Citizen View', dot: 'bg-purple-600', text: 'text-purple-700', bg: 'bg-purple-50 border-purple-200' };
    }
  };

  const rolePill = getRolePill();

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30 shadow-xs">
      {/* Left: Mobile Toggle & Page Title / Breadcrumb */}
      <div className="flex items-center gap-3 sm:gap-4 flex-1 max-w-xl">
        <button
          onClick={onToggleMobileMenu}
          className="lg:hidden text-slate-500 hover:text-slate-800 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {pageTitle && (
          <div className="hidden sm:flex items-center gap-2 text-xs font-semibold text-slate-500">
            <span>EncroWatch</span>
            <span>/</span>
            <span className="text-slate-900 font-bold">{pageTitle}</span>
          </div>
        )}

        {/* Global Search */}
        <div className="relative w-full max-w-xs ml-2">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search cases or locations..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="w-full bg-[#F5F7FA] text-xs text-slate-800 pl-8 pr-3 py-1.5 rounded-lg border border-transparent focus:border-slate-300 focus:bg-white focus:outline-none transition-all placeholder:text-slate-400 font-medium"
          />
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2.5 sm:gap-3">
        {/* Language Selector */}
        <div className="flex items-center bg-[#F5F7FA] border border-slate-200 rounded-lg px-2 py-1 text-xs">
          <Globe className="w-3.5 h-3.5 text-slate-500 mr-1.5 shrink-0" />
          <select
            value={lang}
            onChange={(e) => changeLanguage(e.target.value)}
            className="bg-transparent text-slate-700 font-bold focus:outline-none cursor-pointer text-xs"
          >
            <option value="en">EN</option>
            <option value="kn">ಕನ್ನಡ</option>
            <option value="hi">हिन्दी</option>
          </select>
        </div>

        {/* Role View Pill */}
        <div className={`hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-bold border ${rolePill.bg} ${rolePill.text}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${rolePill.dot}`} />
          <span>{rolePill.label}</span>
        </div>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-3.5 h-3.5 bg-red-600 text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                {unreadCount}
              </span>
            )}
          </button>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 sm:w-88 bg-white rounded-xl shadow-lg border border-slate-200 p-3.5 z-50 animate-scale-in">
              <div className="flex items-center justify-between pb-2.5 border-b border-slate-100">
                <div className="font-bold text-slate-800 text-xs">Notifications</div>
                <button
                  onClick={markAllRead}
                  className="text-[11px] text-blue-600 font-semibold hover:underline flex items-center gap-1"
                >
                  <Check className="w-3 h-3" /> Mark all read
                </button>
              </div>

              <div className="divide-y divide-slate-100 max-h-64 overflow-y-auto mt-1">
                {notifications.length === 0 ? (
                  <div className="py-6 text-center text-xs text-slate-400">No new notifications</div>
                ) : (
                  notifications.map((n) => {
                    const isUnread = n.is_read === false || n.read === false;
                    return (
                      <div
                        key={n.id}
                        onClick={() => {
                          if (n.markRead) n.markRead(n.id);
                          if (n.incident_id && onSelectIncident) {
                            onSelectIncident(n.incident_id);
                            setShowNotifications(false);
                          }
                        }}
                        className={`p-2.5 text-xs rounded-lg hover:bg-slate-50 transition-colors cursor-pointer ${
                          isUnread ? 'bg-blue-50/50 font-medium' : ''
                        }`}
                      >
                        <div className="font-semibold text-slate-800 flex items-center justify-between">
                          <span>{n.title}</span>
                          <span className="text-[10px] text-slate-400 font-normal">
                            {n.created_at ? new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : (n.time || 'Just now')}
                          </span>
                        </div>
                        <p className="text-slate-500 mt-0.5 leading-relaxed text-[11px]">{n.message}</p>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Menu */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 p-1 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <div className="w-7 h-7 rounded-lg bg-slate-900 text-white font-bold text-xs flex items-center justify-center">
              {(user?.full_name || role || 'U').charAt(0).toUpperCase()}
            </div>
            <span className="hidden lg:block text-xs font-semibold text-slate-800 truncate max-w-[110px]">
              {user?.full_name || role}
            </span>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 hidden lg:block" />
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-52 bg-white rounded-xl shadow-lg border border-slate-200 p-2 z-50">
              <div className="p-2.5 border-b border-slate-100">
                <div className="font-bold text-slate-800 text-xs truncate">{user?.full_name || 'Active User'}</div>
                <div className="text-[11px] text-slate-400 truncate">{user?.email || `${role}@encrowatch.ai`}</div>
                <div className="mt-1 inline-block px-1.5 py-0.2 rounded text-[10px] font-bold bg-slate-100 text-slate-700 capitalize">
                  {role} Role
                </div>
              </div>

              <div className="p-1 mt-1">
                <button
                  onClick={logout}
                  className="w-full flex items-center gap-2 px-2.5 py-1.5 text-xs text-red-600 hover:bg-red-50 rounded-lg font-semibold transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
