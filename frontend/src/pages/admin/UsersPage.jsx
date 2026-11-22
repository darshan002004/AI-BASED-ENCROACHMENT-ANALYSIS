import React, { useState, useEffect } from 'react';
import {
  Users,
  Shield,
  UserCheck,
  Smartphone,
  Plus,
  Mail,
  Phone,
  MapPin,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  RefreshCw,
  Search,
  Building2,
  Briefcase,
  BadgeCheck,
  Power,
  Check,
  X,
  Info,
  Eye,
  Calendar
} from 'lucide-react';
import { authAPI } from '../../services/api';
import { parseApiError } from '../../utils/errorParser';

export default function UsersPage({ filterRole }) {
  const [activeTab, setActiveTab] = useState(() => {
    return filterRole === 'officer' ? 'pending' : 'all';
  });

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [actionMessage, setActionMessage] = useState(null);
  const [processingId, setProcessingId] = useState(null);

  // Rejection modal state
  const [rejectingUser, setRejectingUser] = useState(null);
  const [rejectReason, setRejectReason] = useState('');

  // Detailed profile modal state
  const [viewingUser, setViewingUser] = useState(null);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await authAPI.getUsers();
      setUsers(res.data || []);
    } catch (err) {
      console.warn('Could not load user directory:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    if (filterRole === 'officer' && activeTab === 'all') {
      setActiveTab('pending');
    }
  }, [filterRole]);

  // Derived datasets
  const allOfficers = users.filter(u => u.role === 'officer');
  const pendingOfficers = allOfficers.filter(u => u.approval_status === 'pending_approval');
  const approvedOfficers = allOfficers.filter(u => (u.approval_status === 'approved' || (!u.approval_status && u.role === 'officer')) && u.is_active !== false);
  const deactivatedOfficers = allOfficers.filter(u => (u.approval_status === 'approved' || (!u.approval_status && u.role === 'officer')) && u.is_active === false);
  const rejectedOfficers = allOfficers.filter(u => u.approval_status === 'rejected');

  // Filter current tab items by search term
  const getTabItems = () => {
    let source = [];
    if (activeTab === 'pending') source = pendingOfficers;
    else if (activeTab === 'approved') source = approvedOfficers;
    else if (activeTab === 'deactivated') source = deactivatedOfficers;
    else if (activeTab === 'rejected') source = rejectedOfficers;
    else source = users;

    if (!searchTerm.trim()) return source;
    const term = searchTerm.toLowerCase();
    return source.filter(u =>
      (u.full_name || '').toLowerCase().includes(term) ||
      (u.email || '').toLowerCase().includes(term) ||
      (u.badge_id || u.employee_id || '').toLowerCase().includes(term) ||
      (u.department || '').toLowerCase().includes(term) ||
      (u.assigned_area || '').toLowerCase().includes(term)
    );
  };

  const handleApprove = async (userId, officerName) => {
    setProcessingId(userId);
    setActionMessage(null);
    try {
      await authAPI.approveOfficer(userId);
      setActionMessage({
        type: 'success',
        text: `Officer ${officerName} has been approved. Account activated with field officer permissions.`
      });
      await fetchUsers();
    } catch (err) {
      setActionMessage({
        type: 'error',
        text: parseApiError(err, 'Failed to approve officer application.')
      });
    } finally {
      setProcessingId(null);
    }
  };

  const handleOpenRejectModal = (user) => {
    setRejectingUser(user);
    setRejectReason('Application credentials could not be verified with municipal records.');
  };

  const handleConfirmReject = async () => {
    if (!rejectingUser) return;
    setProcessingId(rejectingUser.id);
    setActionMessage(null);
    try {
      await authAPI.rejectOfficer(rejectingUser.id, rejectReason.trim());
      setActionMessage({
        type: 'info',
        text: `Officer application for ${rejectingUser.full_name} has been rejected.`
      });
      setRejectingUser(null);
      setRejectReason('');
      await fetchUsers();
    } catch (err) {
      setActionMessage({
        type: 'error',
        text: parseApiError(err, 'Failed to reject officer application.')
      });
    } finally {
      setProcessingId(null);
    }
  };

  const handleToggleActive = async (userId, officerName, currentStatus) => {
    setProcessingId(userId);
    setActionMessage(null);
    try {
      await authAPI.toggleOfficerActive(userId);
      setActionMessage({
        type: 'success',
        text: `Officer ${officerName} account status changed to ${currentStatus ? 'Deactivated' : 'Active'}.`
      });
      await fetchUsers();
    } catch (err) {
      setActionMessage({
        type: 'error',
        text: parseApiError(err, 'Failed to update account active status.')
      });
    } finally {
      setProcessingId(null);
    }
  };

  const currentItems = getTabItems();

  return (
    <div className="space-y-5 max-w-7xl mx-auto pb-16">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-semibold tracking-wider text-slate-500 uppercase">Municipal Administration</span>
            <span className="text-slate-300">•</span>
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200/80">
              <Shield className="w-3 h-3 text-blue-600" />
              RBAC &amp; Identity Governance
            </span>
          </div>
          <h1 className="text-base font-bold text-slate-900 tracking-tight mt-1">
            User Directory &amp; Officer Management
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Review pending officer registration applications, manage municipal field rosters, and audit user permissions
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={fetchUsers}
            className="p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition-colors shadow-2xs"
            title="Refresh directory"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 5 Summary Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div
          onClick={() => setActiveTab('pending')}
          className={`bg-white rounded-xl p-3.5 border transition-all cursor-pointer shadow-2xs ${
            activeTab === 'pending'
              ? 'border-amber-500 ring-1 ring-amber-500'
              : 'border-slate-200/90 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="text-xl font-bold text-amber-600 tracking-tight">{pendingOfficers.length}</div>
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center border border-amber-100">
              <Clock className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-xs font-semibold text-slate-900 mt-1">Pending Review</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Awaiting Admin Approval</div>
        </div>

        <div
          onClick={() => setActiveTab('approved')}
          className={`bg-white rounded-xl p-3.5 border transition-all cursor-pointer shadow-2xs ${
            activeTab === 'approved'
              ? 'border-emerald-500 ring-1 ring-emerald-500'
              : 'border-slate-200/90 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="text-xl font-bold text-emerald-600 tracking-tight">{approvedOfficers.length}</div>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-100">
              <UserCheck className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-xs font-semibold text-slate-900 mt-1">Approved Officers</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Active Field Operations</div>
        </div>

        <div
          onClick={() => setActiveTab('deactivated')}
          className={`bg-white rounded-xl p-3.5 border transition-all cursor-pointer shadow-2xs ${
            activeTab === 'deactivated'
              ? 'border-slate-700 ring-1 ring-slate-700'
              : 'border-slate-200/90 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="text-xl font-bold text-slate-700 tracking-tight">{deactivatedOfficers.length}</div>
            <div className="w-8 h-8 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center border border-slate-200">
              <Power className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-xs font-semibold text-slate-900 mt-1">Deactivated Officers</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Suspended Permissions</div>
        </div>

        <div
          onClick={() => setActiveTab('rejected')}
          className={`bg-white rounded-xl p-3.5 border transition-all cursor-pointer shadow-2xs ${
            activeTab === 'rejected'
              ? 'border-rose-500 ring-1 ring-rose-500'
              : 'border-slate-200/90 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="text-xl font-bold text-slate-900 tracking-tight">{rejectedOfficers.length}</div>
            <div className="w-8 h-8 rounded-lg bg-rose-50 text-rose-700 flex items-center justify-center border border-rose-100">
              <XCircle className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-xs font-semibold text-slate-900 mt-1">Rejected Applications</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Declined Requests</div>
        </div>

        <div
          onClick={() => setActiveTab('all')}
          className={`bg-white rounded-xl p-3.5 border transition-all cursor-pointer shadow-2xs col-span-2 sm:col-span-1 ${
            activeTab === 'all'
              ? 'border-slate-800 ring-1 ring-slate-800'
              : 'border-slate-200/90 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="text-xl font-bold text-slate-900 tracking-tight">{users.length}</div>
            <div className="w-8 h-8 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center border border-slate-200">
              <Users className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="text-xs font-semibold text-slate-900 mt-1">Total System Users</div>
          <div className="text-[10px] text-slate-500 mt-0.5">All Registered Personas</div>
        </div>
      </div>

      {/* Action Notification Banner */}
      {actionMessage && (
        <div className={`p-3.5 rounded-lg border text-xs font-medium flex items-center justify-between ${
          actionMessage.type === 'success'
            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
            : actionMessage.type === 'info'
            ? 'bg-blue-50 text-blue-800 border-blue-200'
            : 'bg-rose-50 text-rose-800 border-rose-200'
        }`}>
          <span>{actionMessage.text}</span>
          <button onClick={() => setActionMessage(null)} className="font-semibold underline text-[11px] ml-4">
            Dismiss
          </button>
        </div>
      )}

      {/* Filter Tabs & Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-3.5 shadow-2xs space-y-3">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          {/* Subtabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0">
            <button
              onClick={() => setActiveTab('pending')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 border whitespace-nowrap ${
                activeTab === 'pending'
                  ? 'bg-amber-500 text-white border-amber-500 shadow-2xs'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              <span>Pending Applications</span>
              {pendingOfficers.length > 0 && (
                <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                  activeTab === 'pending' ? 'bg-amber-600 text-white' : 'bg-amber-100 text-amber-800'
                }`}>
                  {pendingOfficers.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('approved')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 border whitespace-nowrap ${
                activeTab === 'approved'
                  ? 'bg-slate-900 text-white border-slate-900 shadow-2xs'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span>Approved Officers ({approvedOfficers.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('deactivated')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 border whitespace-nowrap ${
                activeTab === 'deactivated'
                  ? 'bg-slate-900 text-white border-slate-900 shadow-2xs'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <Power className="w-3.5 h-3.5" />
              <span>Deactivated ({deactivatedOfficers.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('rejected')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 border whitespace-nowrap ${
                activeTab === 'rejected'
                  ? 'bg-slate-900 text-white border-slate-900 shadow-2xs'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Rejected ({rejectedOfficers.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('all')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 border whitespace-nowrap ${
                activeTab === 'all'
                  ? 'bg-slate-900 text-white border-slate-900 shadow-2xs'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span>All Users ({users.length})</span>
            </button>
          </div>

          {/* Search Box */}
          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by name, email, ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Content Section */}
      {loading ? (
        <div className="p-12 text-center text-slate-500 bg-white rounded-xl border border-slate-200/90 shadow-2xs">
          <div className="animate-spin w-7 h-7 border-3 border-slate-700 border-t-transparent rounded-full mx-auto mb-3" />
          <p className="text-xs font-medium text-slate-600">Loading records from municipal database...</p>
        </div>
      ) : currentItems.length === 0 ? (
        <div className="p-12 text-center text-slate-400 bg-white rounded-xl border border-slate-200/90 shadow-2xs">
          <UserCheck className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <p className="font-semibold text-slate-700 text-sm">
            {activeTab === 'pending'
              ? 'No pending officer registration applications.'
              : activeTab === 'approved'
              ? 'No approved officers found.'
              : activeTab === 'deactivated'
              ? 'No deactivated officers.'
              : activeTab === 'rejected'
              ? 'No rejected applications.'
              : 'No users found matching current filters.'}
          </p>
          <p className="text-xs mt-1 text-slate-500">
            {activeTab === 'pending'
              ? 'All officer registration requests have been reviewed.'
              : activeTab === 'deactivated'
              ? 'All approved officer accounts are currently active in field operations.'
              : 'Records will appear as users register or change categories.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {activeTab === 'pending' ? (
            /* Pending Applications Detailed Cards */
            <div className="grid grid-cols-1 gap-3.5">
              {currentItems.map((u) => {
                const isProcessing = processingId === u.id;
                return (
                  <div
                    key={u.id}
                    className="bg-white rounded-xl p-5 border border-amber-200/80 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="flex items-start gap-3.5 min-w-0">
                      <img
                        src={u.avatar_url || 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=120&auto=format&fit=crop&q=80'}
                        alt={u.full_name}
                        onError={(e) => { e.currentTarget.onerror = null; e.currentTarget.src = 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=120&auto=format&fit=crop&q=80'; }}
                        className="w-12 h-12 rounded-xl object-cover border border-slate-200 shrink-0 bg-slate-100"
                      />
                      <div className="space-y-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="text-sm font-bold text-slate-900 truncate">{u.full_name}</h3>
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                            Awaiting Administrator Approval
                          </span>
                        </div>

                        <div className="flex items-center gap-3 text-xs text-slate-500 flex-wrap">
                          <span className="flex items-center gap-1">
                            <Mail className="w-3.5 h-3.5 text-slate-400" />
                            {u.email}
                          </span>
                          {u.phone && (
                            <span className="flex items-center gap-1">
                              <Phone className="w-3.5 h-3.5 text-slate-400" />
                              {u.phone}
                            </span>
                          )}
                          <span className="flex items-center gap-1 font-mono text-[11px] text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                            <BadgeCheck className="w-3.5 h-3.5 text-blue-600" />
                            ID: {u.badge_id || u.employee_id || 'N/A'}
                          </span>
                        </div>

                        <div className="flex items-center gap-3 text-xs text-slate-600 pt-1 flex-wrap">
                          {u.department && (
                            <span className="flex items-center gap-1">
                              <Building2 className="w-3.5 h-3.5 text-slate-400" />
                              <strong>Dept:</strong> {u.department}
                            </span>
                          )}
                          {u.designation && (
                            <span className="flex items-center gap-1">
                              <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                              <strong>Post:</strong> {u.designation}
                            </span>
                          )}
                          {u.assigned_area && (
                            <span className="flex items-center gap-1">
                              <MapPin className="w-3.5 h-3.5 text-slate-400" />
                              <strong>Zone:</strong> {u.assigned_area}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Action Buttons: [View Details], [Approve], [Reject] */}
                    <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
                      <button
                        onClick={() => setViewingUser(u)}
                        className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>View Details</span>
                      </button>

                      <button
                        onClick={() => handleApprove(u.id, u.full_name)}
                        disabled={isProcessing}
                        className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-2xs flex items-center gap-1.5 transition-colors disabled:opacity-50"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Approve Officer</span>
                      </button>

                      <button
                        onClick={() => handleOpenRejectModal(u)}
                        disabled={isProcessing}
                        className="px-3.5 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
                      >
                        <X className="w-3.5 h-3.5" />
                        <span>Reject</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            /* Grid layout for Approved, Rejected, and All Users */
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {currentItems.map((u) => {
                const isOfficer = u.role === 'officer';
                const isApproved = u.approval_status === 'approved' || (!u.approval_status && isOfficer);
                const isRejected = u.approval_status === 'rejected';
                const isPending = u.approval_status === 'pending_approval';
                const isActive = u.is_active !== false;
                const isProcessing = processingId === u.id;

                return (
                  <div
                    key={u.id}
                    className="bg-white rounded-xl p-4 border border-slate-200/90 shadow-2xs flex flex-col justify-between space-y-3"
                  >
                    <div className="flex items-start gap-3">
                      <img
                        src={u.avatar_url || 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=120&auto=format&fit=crop&q=80'}
                        alt={u.full_name}
                        onError={(e) => { e.currentTarget.onerror = null; e.currentTarget.src = 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=120&auto=format&fit=crop&q=80'; }}
                        className="w-10 h-10 rounded-full object-cover ring-1 ring-slate-200 shrink-0 bg-slate-100"
                      />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between gap-1">
                          <div className="font-bold text-slate-900 text-xs truncate">{u.full_name}</div>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${
                            u.role === 'admin'
                              ? 'bg-slate-100 text-slate-800 border border-slate-200'
                              : u.role === 'officer'
                              ? 'bg-blue-50 text-blue-700 border border-blue-200'
                              : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          }`}>
                            {u.role}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-500 truncate mt-0.5">{u.email}</div>
                      </div>
                    </div>

                    {/* Officer Status Details */}
                    {isOfficer && (
                      <div className="space-y-1 text-[11px] text-slate-600 border-t border-slate-100 pt-2.5">
                        <div className="flex items-center justify-between">
                          <span className="text-slate-400">Employee ID:</span>
                          <span className="font-mono font-semibold text-slate-800">{u.badge_id || u.employee_id || 'N/A'}</span>
                        </div>
                        {u.department && (
                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">Department:</span>
                            <span className="font-medium text-slate-800 truncate max-w-[170px]" title={u.department}>{u.department}</span>
                          </div>
                        )}
                        {u.assigned_area && (
                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">Zone:</span>
                            <span className="font-medium text-slate-800 truncate max-w-[170px]" title={u.assigned_area}>{u.assigned_area}</span>
                          </div>
                        )}
                        <div className="flex items-center justify-between pt-1">
                          <span className="text-slate-400">Status:</span>
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                            isApproved
                              ? isActive
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : 'bg-slate-100 text-slate-600 border border-slate-200'
                              : isPending
                              ? 'bg-amber-50 text-amber-700 border border-amber-200'
                              : 'bg-rose-50 text-rose-700 border border-rose-200'
                          }`}>
                            {isApproved ? (isActive ? 'Active' : 'Deactivated') : (isPending ? 'Pending Approval' : 'Rejected')}
                          </span>
                        </div>

                        {/* Rejection reason callout if rejected */}
                        {isRejected && u.rejection_reason && (
                          <div className="mt-2 p-2 rounded bg-rose-50 border border-rose-200 text-rose-800 text-[10px] leading-relaxed">
                            <strong>Reason:</strong> {u.rejection_reason}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Citizen Details */}
                    {!isOfficer && (
                      <div className="space-y-1 text-[11px] text-slate-600 border-t border-slate-100 pt-2.5">
                        {u.phone && (
                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">Phone:</span>
                            <span className="font-medium text-slate-800">{u.phone}</span>
                          </div>
                        )}
                        {u.address && (
                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">Address:</span>
                            <span className="font-medium text-slate-800 truncate max-w-[170px]">{u.address}</span>
                          </div>
                        )}
                        <div className="flex items-center justify-between">
                          <span className="text-slate-400">Registered:</span>
                          <span className="font-medium text-slate-600">{u.created_at ? u.created_at.split('T')[0] : 'Active'}</span>
                        </div>
                      </div>
                    )}

                    {/* Card Actions */}
                    <div className="pt-2 border-t border-slate-100 flex items-center justify-between gap-1.5">
                      <button
                        onClick={() => setViewingUser(u)}
                        className="px-2.5 py-1 rounded bg-slate-50 hover:bg-slate-100 text-slate-700 font-semibold text-[11px] border border-slate-200 transition-colors flex items-center gap-1"
                      >
                        <Eye className="w-3 h-3 text-slate-500" />
                        <span>View Details</span>
                      </button>

                      {isOfficer && (
                        <div className="flex items-center gap-1.5">
                          {isPending && (
                            <>
                              <button
                                onClick={() => handleApprove(u.id, u.full_name)}
                                disabled={isProcessing}
                                className="px-2.5 py-1 rounded bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-semibold text-[11px] border border-emerald-200 transition-colors"
                              >
                                Approve
                              </button>
                              <button
                                onClick={() => handleOpenRejectModal(u)}
                                disabled={isProcessing}
                                className="px-2.5 py-1 rounded bg-rose-50 hover:bg-rose-100 text-rose-700 font-semibold text-[11px] border border-rose-200 transition-colors"
                              >
                                Reject
                              </button>
                            </>
                          )}

                          {isApproved && (
                            <button
                              onClick={() => handleToggleActive(u.id, u.full_name, isActive)}
                              disabled={isProcessing}
                              className={`px-2.5 py-1 rounded font-semibold text-[11px] border transition-colors flex items-center gap-1 ${
                                isActive
                                  ? 'bg-slate-100 hover:bg-rose-50 hover:text-rose-700 text-slate-700 border-slate-200'
                                  : 'bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border-emerald-200'
                              }`}
                            >
                              <Power className="w-3 h-3" />
                              <span>{isActive ? 'Deactivate' : 'Activate'}</span>
                            </button>
                          )}

                          {isRejected && (
                            <button
                              onClick={() => handleApprove(u.id, u.full_name)}
                              disabled={isProcessing}
                              className="px-2.5 py-1 rounded bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-semibold text-[11px] border border-emerald-200 transition-colors"
                            >
                              Reconsider &amp; Approve
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Officer Rejection Dialog Modal */}
      {rejectingUser && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-5 shadow-xl border border-slate-200/90 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-600" />
                <h3 className="text-sm font-bold text-slate-900">Reject Officer Application</h3>
              </div>
              <button
                onClick={() => setRejectingUser(null)}
                className="text-slate-400 hover:text-slate-600 w-6 h-6 flex items-center justify-center rounded-lg hover:bg-slate-100"
              >
                ✕
              </button>
            </div>

            <div className="text-xs text-slate-600 space-y-1">
              <div>Applicant: <strong className="text-slate-900">{rejectingUser.full_name}</strong></div>
              <div>Official Email: <strong className="text-slate-900">{rejectingUser.email}</strong></div>
              <div>Employee ID: <strong className="text-slate-900">{rejectingUser.badge_id || rejectingUser.employee_id}</strong></div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 block">
                Administrative Rejection Reason (Mandatory):
              </label>
              <textarea
                rows="3"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="State the reason for rejecting this officer registration..."
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setRejectingUser(null)}
                className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmReject}
                className="px-3.5 py-1.5 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-lg shadow-2xs transition-colors flex items-center gap-1.5"
              >
                <X className="w-3.5 h-3.5" />
                <span>Confirm Rejection</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Comprehensive Officer/User View Details Modal */}
      {viewingUser && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200/90 space-y-5 animate-scale-in">
            <div className="flex items-start justify-between border-b border-slate-100 pb-3.5">
              <div className="flex items-center gap-3">
                <img
                  src={viewingUser.avatar_url || 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=120&auto=format&fit=crop&q=80'}
                  alt={viewingUser.full_name}
                  className="w-12 h-12 rounded-xl object-cover border border-slate-200 bg-slate-100"
                />
                <div>
                  <h3 className="text-base font-bold text-slate-900">{viewingUser.full_name}</h3>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                      viewingUser.role === 'admin'
                        ? 'bg-slate-100 text-slate-800 border border-slate-200'
                        : viewingUser.role === 'officer'
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    }`}>
                      {viewingUser.role}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                      viewingUser.approval_status === 'approved' || (!viewingUser.approval_status && viewingUser.role === 'officer')
                        ? viewingUser.is_active !== false
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-slate-100 text-slate-600 border border-slate-200'
                        : viewingUser.approval_status === 'pending_approval'
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-rose-50 text-rose-700 border border-rose-200'
                    }`}>
                      {viewingUser.approval_status === 'approved' || (!viewingUser.approval_status && viewingUser.role === 'officer')
                        ? (viewingUser.is_active !== false ? 'Active Account' : 'Deactivated Account')
                        : viewingUser.approval_status === 'pending_approval'
                        ? 'Awaiting Approval'
                        : 'Application Rejected'}
                    </span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setViewingUser(null)}
                className="text-slate-400 hover:text-slate-700 text-sm font-bold w-7 h-7 flex items-center justify-center rounded-lg hover:bg-slate-100"
              >
                ✕
              </button>
            </div>

            {/* Profile Grid */}
            <div className="grid grid-cols-2 gap-3 text-xs bg-slate-50 p-4 rounded-xl border border-slate-100">
              <div>
                <span className="text-slate-400 block text-[11px]">Email Address</span>
                <span className="font-semibold text-slate-900 break-all">{viewingUser.email}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Mobile Number</span>
                <span className="font-semibold text-slate-900">{viewingUser.phone || '—'}</span>
              </div>
              {viewingUser.role === 'officer' && (
                <>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Employee / Badge ID</span>
                    <span className="font-mono font-bold text-slate-900">{viewingUser.badge_id || viewingUser.employee_id || '—'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Department</span>
                    <span className="font-semibold text-slate-900">{viewingUser.department || 'Encroachment Removal Squad'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Designation</span>
                    <span className="font-semibold text-slate-900">{viewingUser.designation || 'Ward Enforcement Officer'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Assigned Zone / Ward</span>
                    <span className="font-semibold text-slate-900">{viewingUser.assigned_area || 'Central Operations'}</span>
                  </div>
                </>
              )}
              {viewingUser.address && (
                <div className="col-span-2">
                  <span className="text-slate-400 block text-[11px]">Address</span>
                  <span className="font-semibold text-slate-900">{viewingUser.address}</span>
                </div>
              )}
              <div>
                <span className="text-slate-400 block text-[11px]">Registration Date</span>
                <span className="font-semibold text-slate-700">{viewingUser.created_at ? viewingUser.created_at.split('T')[0] : 'Standard'}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">System ID</span>
                <span className="font-mono text-[11px] text-slate-600">{viewingUser.id || viewingUser._id}</span>
              </div>
            </div>

            {/* Review History / Rejection Notice */}
            {viewingUser.reviewed_by && (
              <div className="p-3 rounded-lg bg-blue-50/70 border border-blue-200 text-xs text-blue-900 space-y-1">
                <div className="font-semibold flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-blue-700" />
                  <span>Administrative Review Record</span>
                </div>
                <div className="text-[11px] text-blue-800">
                  Reviewed by <strong>{viewingUser.reviewed_by}</strong> on {viewingUser.reviewed_at ? viewingUser.reviewed_at.split('T')[0] : 'Recent'}.
                </div>
              </div>
            )}

            {viewingUser.rejection_reason && (
              <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-900 space-y-1">
                <div className="font-semibold flex items-center gap-1.5 text-rose-800">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                  <span>Documented Rejection Reason</span>
                </div>
                <div className="text-[11px] text-rose-800">{viewingUser.rejection_reason}</div>
              </div>
            )}

            {/* Modal Actions */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setViewingUser(null)}
                className="px-3.5 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                Close
              </button>

              {viewingUser.role === 'officer' && (
                <div className="flex items-center gap-2">
                  {viewingUser.approval_status === 'pending_approval' && (
                    <>
                      <button
                        onClick={() => {
                          const target = viewingUser;
                          setViewingUser(null);
                          handleOpenRejectModal(target);
                        }}
                        className="px-3.5 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                      >
                        <X className="w-3.5 h-3.5" />
                        <span>Reject</span>
                      </button>
                      <button
                        onClick={async () => {
                          const targetId = viewingUser.id;
                          const targetName = viewingUser.full_name;
                          setViewingUser(null);
                          await handleApprove(targetId, targetName);
                        }}
                        className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-2xs flex items-center gap-1.5 transition-colors"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>Approve Officer</span>
                      </button>
                    </>
                  )}

                  {(viewingUser.approval_status === 'approved' || (!viewingUser.approval_status && viewingUser.role === 'officer')) && (
                    <button
                      onClick={async () => {
                        const targetId = viewingUser.id;
                        const targetName = viewingUser.full_name;
                        const curr = viewingUser.is_active !== false;
                        setViewingUser(null);
                        await handleToggleActive(targetId, targetName, curr);
                      }}
                      className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold border flex items-center gap-1.5 transition-colors ${
                        viewingUser.is_active !== false
                          ? 'bg-rose-50 hover:bg-rose-100 text-rose-700 border-rose-200'
                          : 'bg-emerald-600 hover:bg-emerald-700 text-white border-emerald-600'
                      }`}
                    >
                      <Power className="w-3.5 h-3.5" />
                      <span>{viewingUser.is_active !== false ? 'Deactivate Account' : 'Activate Account'}</span>
                    </button>
                  )}

                  {viewingUser.approval_status === 'rejected' && (
                    <button
                      onClick={async () => {
                        const targetId = viewingUser.id;
                        const targetName = viewingUser.full_name;
                        setViewingUser(null);
                        await handleApprove(targetId, targetName);
                      }}
                      className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-2xs flex items-center gap-1.5 transition-colors"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Reconsider &amp; Approve</span>
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
