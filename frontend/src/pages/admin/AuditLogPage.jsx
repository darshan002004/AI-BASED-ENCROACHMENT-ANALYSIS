import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ClipboardList, Search, Filter, ShieldCheck, User, Calendar,
  RefreshCw, CheckCircle2, AlertTriangle, Hash, Lock
} from 'lucide-react';
import { auditAPI } from '../../services/api';

export default function AuditLogPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('ALL');
  const [outcomeFilter, setOutcomeFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  // Cryptographic Chain Verification state
  const [verifying, setVerifying] = useState(false);
  const [chainResult, setChainResult] = useState(null);

  useEffect(() => {
    fetchLogs();
  }, [actionFilter, outcomeFilter]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = {};
      if (actionFilter !== 'ALL') params.action = actionFilter;
      if (outcomeFilter !== 'ALL') params.outcome = outcomeFilter;
      const res = await auditAPI.getLogs(params);
      setLogs(res.data.items || []);
    } catch (err) {
      console.error('Error fetching audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyChain = async () => {
    setVerifying(true);
    try {
      const res = await auditAPI.verifyIntegrity();
      setChainResult(res.data);
    } catch (err) {
      alert('Integrity check failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setVerifying(false);
    }
  };

  const filteredLogs = logs.filter(log => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      (log.user_name || '').toLowerCase().includes(term) ||
      (log.action || '').toLowerCase().includes(term) ||
      (log.target_id || '').toLowerCase().includes(term) ||
      (log.outcome || '').toLowerCase().includes(term) ||
      JSON.stringify(log.details || {}).toLowerCase().includes(term)
    );
  });

  const getActionBadge = (action) => {
    const act = (action || '').toUpperCase();
    if (act.includes('CREATE') || act.includes('PROMOTED')) return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    if (act.includes('VERIFY') || act.includes('EVALUATED')) return 'bg-purple-50 text-purple-700 border-purple-200';
    if (act.includes('MERGE') || act.includes('ROLLBACK')) return 'bg-amber-50 text-amber-700 border-amber-200';
    if (act.includes('DENIED') || act.includes('FAILED')) return 'bg-red-50 text-red-700 border-red-200';
    if (act.includes('INSPECT') || act.includes('SYNC')) return 'bg-blue-50 text-blue-700 border-blue-200';
    return 'bg-slate-50 text-slate-700 border-slate-200';
  };

  const getOutcomeBadge = (outcome) => {
    const oc = (outcome || 'SUCCESS').toUpperCase();
    if (oc === 'SUCCESS') return 'bg-emerald-100 text-emerald-800';
    if (oc === 'DENIED') return 'bg-amber-100 text-amber-800';
    if (oc === 'FAILED') return 'bg-red-100 text-red-800';
    return 'bg-slate-100 text-slate-700';
  };

  return (
    <div className="space-y-5 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200/90 shadow-2xs">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1 rounded-md bg-slate-100 text-slate-800 border border-slate-200">
              <ClipboardList className="w-4 h-4" />
            </span>
            <h1 className="text-base font-bold text-slate-900 tracking-tight">System Audit Trail & Cryptographic Governance</h1>
          </div>
          <p className="text-xs text-slate-500">
            Immutable, append-only log of logins, reviews, model lifecycle transitions, and dispatches protected by SHA-256 hash chaining.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleVerifyChain}
            disabled={verifying}
            className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all shadow-2xs"
          >
            <Lock className={`w-3.5 h-3.5 ${verifying ? 'animate-spin' : ''}`} />
            <span>{verifying ? 'Verifying Chain...' : 'Verify Cryptographic Chain'}</span>
          </button>

          <button
            onClick={fetchLogs}
            className="p-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition-colors"
            title="Refresh Audit"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Cryptographic Chain Integrity Banner */}
      {chainResult && (
        <div className={`p-4 rounded-xl border transition-all ${
          chainResult.is_valid
            ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
            : 'bg-rose-50 border-rose-200 text-rose-900'
        }`}>
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              {chainResult.is_valid ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-rose-600 mt-0.5 shrink-0" />
              )}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider">
                  {chainResult.is_valid ? 'Cryptographic Audit Chain Intact' : 'Audit Chain Tampering Detected!'}
                </h3>
                <p className="text-xs mt-0.5">
                  Verified {chainResult.total_records_checked} contiguous audit records from genesis.
                  All SHA-256 links and record hashes are strictly matching.
                </p>
                <div className="mt-1.5 text-[11px] font-mono opacity-80 flex items-center gap-2">
                  <Hash className="w-3 h-3" />
                  <span>Chain Head: {chainResult.chain_head_hash ? chainResult.chain_head_hash.substring(0, 32) + '...' : 'Genesis'}</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => setChainResult(null)}
              className="text-xs font-semibold opacity-60 hover:opacity-100"
            >
              Dismiss
            </button>
          </div>
          <div className="mt-2.5 pt-2.5 border-t border-emerald-200/60 text-[10px] text-emerald-700/90">
            {chainResult.disclaimer}
          </div>
        </div>
      )}

      {/* Toolbar & Filters */}
      <div className="bg-white p-3.5 rounded-xl border border-slate-200/90 shadow-2xs flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search actor, action, target..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          {/* Action Filter */}
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-200 bg-white text-slate-700 focus:outline-none"
          >
            <option value="ALL">All Actions</option>
            <option value="INCIDENT_CREATE">Incident Create</option>
            <option value="AI_VERIFY">AI Review</option>
            <option value="STATUS_CHANGE">Status Change</option>
            <option value="OFFLINE_SYNC_SUCCESS">Offline Sync</option>
            <option value="CONFLICT_RESOLVED">Conflict Resolved</option>
            <option value="RAW_EVIDENCE_ACCESS">Raw Evidence Access</option>
            <option value="MODEL_PROMOTED">Model Promoted</option>
            <option value="MODEL_ROLLBACK">Model Rollback</option>
            <option value="PERMISSION_DENIED">Permission Denied</option>
          </select>

          {/* Outcome Filter */}
          <select
            value={outcomeFilter}
            onChange={(e) => setOutcomeFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-200 bg-white text-slate-700 focus:outline-none"
          >
            <option value="ALL">All Outcomes</option>
            <option value="SUCCESS">Success</option>
            <option value="DENIED">Denied</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">
            <div className="animate-spin w-8 h-8 border-4 border-slate-900 border-t-transparent rounded-full mx-auto mb-3" />
            <p className="text-sm">Loading audit events from MongoDB...</p>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            No audit log entries matching your current filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Outcome</th>
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Resource</th>
                  <th className="py-3 px-4">Integrity Hash</th>
                  <th className="py-3 px-4">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredLogs.map((log) => {
                  let timeFormatted = log.timestamp;
                  try {
                    timeFormatted = new Date(log.timestamp).toLocaleString();
                  } catch (e) {}

                  return (
                    <tr key={log.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-500 whitespace-nowrap">
                        {timeFormatted}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2.5 py-0.5 rounded-full font-bold text-[10px] border ${getActionBadge(log.action)}`}>
                          {log.action}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded-md font-bold text-[10px] uppercase ${getOutcomeBadge(log.outcome)}`}>
                          {log.outcome || 'SUCCESS'}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-900 whitespace-nowrap">
                        {log.user_name || 'System'}
                      </td>
                      <td className="py-3 px-4 capitalize font-semibold text-slate-600">
                        {log.user_role}
                      </td>
                      <td className="py-3 px-4 font-mono font-medium text-blue-600">
                        {log.target_id || '—'}
                      </td>
                      <td className="py-3 px-4 font-mono text-[10px] text-slate-400 truncate max-w-[100px]" title={log.record_hash}>
                        {log.record_hash ? log.record_hash.substring(0, 10) + '...' : 'legacy'}
                      </td>
                      <td className="py-3 px-4 text-slate-700 max-w-xs truncate" title={JSON.stringify(log.details)}>
                        {JSON.stringify(log.details)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
