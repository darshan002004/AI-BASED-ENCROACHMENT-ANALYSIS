import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  MapPin,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Play,
  FileCheck,
  Eye,
  Camera,
  Wifi,
  WifiOff,
  RefreshCw,
  UploadCloud,
  Save,
  MessageSquare,
  AlertCircle,
  AlertOctagon,
  Trash2,
  Check,
  RotateCcw,
  Lock,
  ArrowRight
} from 'lucide-react';
import { StatusBadge, SeverityBadge } from '../../components/StatusBadge';
import { incidentsAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';

const OFFLINE_QUEUE_KEY = 'encrowatch_officer_offline_queue';
const CACHED_ASSIGNMENTS_KEY = 'encrowatch_officer_cached_assignments';

export default function OfficerDashboard({ onConductInspection, onSelectIncident }) {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [incidents, setIncidents] = useState([]);
  const [stats, setStats] = useState({
    assigned: 0,
    inProgress: 0,
    resolved: 0
  });
  const [loading, setLoading] = useState(true);

  // Feature 1: Offline Architecture & Network State
  const [isOnline, setIsOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);
  const [simulateOffline, setSimulateOffline] = useState(false);
  const [offlineQueue, setOfflineQueue] = useState([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncFeedback, setSyncFeedback] = useState(null);
  const [isLoadedFromCache, setIsLoadedFromCache] = useState(false);
  const [isCacheExpired, setIsCacheExpired] = useState(false);

  // Conflict Resolution Modal State
  const [activeConflictItem, setActiveConflictItem] = useState(null);

  // Officer Review Queue State (Batch 3)
  const [activeTabMode, setActiveTabMode] = useState('patrol'); // 'patrol' | 'review-queue' | 'offline-queue'
  const [reviewQueue, setReviewQueue] = useState([]);
  const [reviewFilter, setReviewFilter] = useState('ALL');
  const [reviewStats, setReviewStats] = useState({ total_queued: 0, conflicting_evidence_count: 0, low_confidence_count: 0 });
  const [loadingReviewQueue, setLoadingReviewQueue] = useState(false);

  // Quick field update modal state
  const [activeModalIncident, setActiveModalIncident] = useState(null);
  const [fieldNote, setFieldNote] = useState('');
  const [fieldStatus, setFieldStatus] = useState('In Progress');

  // Load offline queue on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(OFFLINE_QUEUE_KEY);
      if (saved) {
        setOfflineQueue(JSON.parse(saved));
      }
    } catch (e) {
      console.warn('Failed to parse offline queue:', e);
    }

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const effectiveOffline = !isOnline || simulateOffline;

  // Save offline queue helper
  const saveQueue = (newQueue) => {
    setOfflineQueue(newQueue);
    try {
      localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(newQueue));
    } catch (e) {
      console.warn('Could not save queue to localStorage:', e);
    }
  };

  const loadIncidents = () => {
    setLoading(true);

    if (effectiveOffline) {
      // Load from cached non-sensitive assignments
      try {
        const cachedStr = localStorage.getItem(CACHED_ASSIGNMENTS_KEY);
        if (cachedStr) {
          const parsed = JSON.parse(cachedStr);
          const ageHours = (Date.now() - (parsed.timestamp || 0)) / (1000 * 60 * 60);
          if (ageHours > 24) {
            setIsCacheExpired(true);
          } else {
            setIsCacheExpired(false);
          }
          setIncidents(parsed.items || []);
          setIsLoadedFromCache(true);
        } else {
          setIncidents([]);
        }
      } catch (e) {
        console.warn('Error reading offline cached assignments:', e);
      }
      setLoading(false);
      return;
    }

    incidentsAPI.list({ limit: 50 })
      .then((res) => {
        const data = res.data || [];
        setIncidents(data);
        setIsLoadedFromCache(false);
        setIsCacheExpired(false);

        // Sanitize and cache non-sensitive assignments for offline access (Requirement 2 & 10)
        // Strips citizen reporter PII (email, phone, reporter_id) to protect citizen privacy offline!
        const sanitized = data.map(item => ({
          id: item.id || item._id,
          incident_number: item.incident_number,
          title: item.title,
          location_name: item.location_name,
          status: item.status,
          severity: item.severity,
          primary_encroachment_type: item.primary_encroachment_type,
          occupancy_percentage: item.occupancy_percentage,
          accessibility_score: item.accessibility_score,
          updated_at: item.updated_at,
          inspection_notes: item.inspection_notes,
          assigned_officer_name: item.assigned_officer_name,
          image_url: item.image_url,
          privacy_image_url: item.privacy_image_url,
          date_reported: item.date_reported
        }));

        try {
          localStorage.setItem(CACHED_ASSIGNMENTS_KEY, JSON.stringify({
            timestamp: Date.now(),
            items: sanitized
          }));
        } catch (e) {
          console.warn('Failed to cache assignments:', e);
        }

        // Compute dynamic stats from actual assigned incidents
        const assigned = data.filter(i => ['Assigned', 'Pending', 'Verified'].includes(i.status)).length;
        const inProgress = data.filter(i => i.status === 'In Progress').length;
        const resolved = data.filter(i => i.status === 'Resolved').length;
        setStats({ assigned, inProgress, resolved });
      })
      .catch((err) => {
        console.warn('Could not load officer incidents from server, trying offline cache:', err);
        try {
          const cachedStr = localStorage.getItem(CACHED_ASSIGNMENTS_KEY);
          if (cachedStr) {
            const parsed = JSON.parse(cachedStr);
            setIncidents(parsed.items || []);
            setIsLoadedFromCache(true);
          }
        } catch (e) {
          // ignore
        }
      })
      .finally(() => setLoading(false));
  };

  const loadReviewQueue = (filter = reviewFilter) => {
    if (effectiveOffline) return;
    setLoadingReviewQueue(true);
    incidentsAPI.getReviewQueue({ filter_type: filter })
      .then(res => {
        setReviewQueue(res.data.items || []);
        setReviewStats({
          total_queued: res.data.total_queued || 0,
          conflicting_evidence_count: res.data.conflicting_evidence_count || 0,
          low_confidence_count: res.data.low_confidence_count || 0
        });
      })
      .catch(err => {
        console.warn('Error fetching review queue:', err);
      })
      .finally(() => setLoadingReviewQueue(false));
  };

  useEffect(() => {
    loadIncidents();
    loadReviewQueue();
  }, [simulateOffline]);

  useEffect(() => {
    if (activeTabMode === 'review-queue') {
      loadReviewQueue(reviewFilter);
    }
  }, [activeTabMode, reviewFilter]);

  // Synchronize queued items with backend (Batch Sync Endpoint)
  const handleSyncQueue = async () => {
    if (offlineQueue.length === 0) return;
    if (effectiveOffline) {
      alert('Cannot sync while in offline mode. Please disable offline simulation or restore internet connection.');
      return;
    }

    setIsSyncing(true);
    setSyncFeedback(null);

    // Filter items that need syncing (exclude already synced)
    const pendingItems = offlineQueue.filter(item => item.syncStatus !== 'SYNCED');
    if (pendingItems.length === 0) {
      setIsSyncing(false);
      setSyncFeedback({ type: 'info', message: 'All items are already synchronized.' });
      return;
    }

    // Set waiting to sync status
    const updatedQueue = offlineQueue.map(item =>
      item.syncStatus !== 'SYNCED' ? { ...item, syncStatus: 'WAITING_TO_SYNC' } : item
    );
    saveQueue(updatedQueue);

    try {
      const batchPayload = {
        items: pendingItems.map(item => ({
          client_sync_id: item.client_sync_id,
          incident_id: item.incidentId,
          status: item.status,
          inspection_notes: item.notes,
          expected_updated_at: item.expected_updated_at,
          force_resolve_conflict: false,
          timestamp: item.timestamp
        }))
      };

      const res = await incidentsAPI.batchSync(batchPayload);
      const batchResults = res.data.results || [];
      const resultMap = new Map(batchResults.map(r => [r.client_sync_id, r]));

      let successCount = 0;
      let conflictCount = 0;
      let failedCount = 0;

      const nextQueue = offlineQueue.map(item => {
        const result = resultMap.get(item.client_sync_id);
        if (!result) return item;

        if (result.status === 'SYNCED' || result.status === 'ALREADY_SYNCED') {
          successCount++;
          return {
            ...item,
            syncStatus: 'SYNCED',
            errorMessage: null,
            conflictData: null
          };
        } else if (result.status === 'CONFLICT') {
          conflictCount++;
          return {
            ...item,
            syncStatus: 'CONFLICT',
            conflictData: result.server_incident,
            errorMessage: result.message
          };
        } else {
          failedCount++;
          return {
            ...item,
            syncStatus: 'SYNC_FAILED',
            errorMessage: result.message || 'Synchronization failed.'
          };
        }
      });

      saveQueue(nextQueue);
      loadIncidents();

      if (conflictCount > 0) {
        setSyncFeedback({
          type: 'error',
          message: `${conflictCount} update(s) have conflicting changes on the server. Please resolve conflicts before applying.`
        });
      } else if (failedCount > 0) {
        setSyncFeedback({
          type: 'error',
          message: `${failedCount} update(s) failed server validation. Review error reasons in the queue.`
        });
      } else {
        setSyncFeedback({
          type: 'success',
          message: `Successfully synchronized ${successCount} field update(s) to server.`
        });
      }
    } catch (err) {
      console.error('Batch sync network or auth error:', err);
      if (err.response?.status === 401) {
        // Session Expired
        const nextQueue = offlineQueue.map(item => ({
          ...item,
          syncStatus: 'SESSION_EXPIRED',
          errorMessage: 'Session expired. Please log in again to sync.'
        }));
        saveQueue(nextQueue);
        setSyncFeedback({
          type: 'error',
          message: t('sessionExpired')
        });
      } else {
        const nextQueue = offlineQueue.map(item => ({
          ...item,
          syncStatus: 'SYNC_FAILED',
          errorMessage: err.response?.data?.detail || err.message || 'Network error during sync'
        }));
        saveQueue(nextQueue);
        setSyncFeedback({
          type: 'error',
          message: 'Network error encountered during synchronization. Local drafts remain safely preserved.'
        });
      }
    } finally {
      setIsSyncing(false);
    }
  };

  // Conflict Resolution Action Handlers (Requirement 8)
  const handleAcceptServerVersion = (item) => {
    // Discard local draft in favor of server
    const nextQueue = offlineQueue.filter(q => q.client_sync_id !== item.client_sync_id);
    saveQueue(nextQueue);
    setActiveConflictItem(null);
    setSyncFeedback({
      type: 'info',
      message: `Accepted server state for incident ${item.incidentNumber}. Local draft discarded.`
    });
    loadIncidents();
  };

  const handleForceOverwriteServer = async (item) => {
    try {
      await incidentsAPI.update(item.incidentId, {
        status: item.status,
        inspection_notes: item.notes,
        force_resolve_conflict: true,
        client_sync_id: item.client_sync_id
      });

      const nextQueue = offlineQueue.filter(q => q.client_sync_id !== item.client_sync_id);
      saveQueue(nextQueue);
      setActiveConflictItem(null);
      setSyncFeedback({
        type: 'success',
        message: `Conflict resolved: Officer update forced and verified on server for ${item.incidentNumber}.`
      });
      loadIncidents();
    } catch (err) {
      console.error('Error resolving conflict:', err);
      alert('Failed to resolve conflict: ' + (err.response?.data?.detail || err.message));
    }
  };

  // Discard a single draft from queue
  const handleDiscardDraft = (clientSyncId) => {
    const nextQueue = offlineQueue.filter(q => q.client_sync_id !== clientSyncId);
    saveQueue(nextQueue);
  };

  // Clear all already synced items from queue
  const handleClearSynced = () => {
    const nextQueue = offlineQueue.filter(q => q.syncStatus !== 'SYNCED');
    saveQueue(nextQueue);
  };

  // Handle Quick Note / Field Inspection Submit
  const handleSaveFieldUpdate = async (e) => {
    e.preventDefault();
    if (!activeModalIncident) return;

    const incId = activeModalIncident.id || activeModalIncident._id;
    const clientSyncId = `sync_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;

    if (effectiveOffline) {
      // Requirement 3 & 5: Save draft locally, marked "SAVED_LOCALLY", do not report as server confirmed
      const queueItem = {
        id: `offline_${Date.now()}`,
        client_sync_id: clientSyncId,
        incidentId: incId,
        incidentNumber: activeModalIncident.incident_number || incId,
        incidentTitle: activeModalIncident.primary_encroachment_type || activeModalIncident.title,
        locationName: activeModalIncident.location_name,
        action: 'FIELD_NOTE',
        expected_updated_at: activeModalIncident.updated_at,
        status: fieldStatus,
        notes: fieldNote,
        syncStatus: 'SAVED_LOCALLY',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        createdAt: new Date().toISOString()
      };

      const nextQueue = [queueItem, ...offlineQueue];
      saveQueue(nextQueue);

      // Optimistically update incident in local view with indicator
      setIncidents(prev => prev.map(i => (i.id || i._id) === incId ? { ...i, status: fieldStatus, _offlinePending: true } : i));

      setSyncFeedback({
        type: 'info',
        message: `${t('savedLocally')}: Draft queued on device. Will synchronize when connected.`
      });
      setActiveModalIncident(null);
      setFieldNote('');
    } else {
      // Direct API update
      try {
        await incidentsAPI.update(incId, {
          status: fieldStatus,
          inspection_notes: fieldNote,
          client_sync_id: clientSyncId,
          expected_updated_at: activeModalIncident.updated_at
        });
        loadIncidents();
        setSyncFeedback({
          type: 'success',
          message: `Incident ${activeModalIncident.incident_number || incId} updated and verified on server.`
        });
        setActiveModalIncident(null);
        setFieldNote('');
      } catch (err) {
        console.error('API update failed:', err);
        if (err.response?.status === 409) {
          alert('Conflict detected: This incident was modified by another user. Please refresh.');
        } else {
          alert('Failed to update incident: ' + (err.response?.data?.detail || err.message));
        }
      }
    }
  };

  const handleStartInspection = async (inc) => {
    const incId = inc.id || inc._id;
    if (effectiveOffline) {
      const clientSyncId = `sync_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      const queueItem = {
        id: `offline_start_${Date.now()}`,
        client_sync_id: clientSyncId,
        incidentId: incId,
        incidentNumber: inc.incident_number || incId,
        incidentTitle: inc.primary_encroachment_type || inc.title,
        locationName: inc.location_name,
        action: 'UPDATE_STATUS',
        expected_updated_at: inc.updated_at,
        status: 'In Progress',
        notes: 'Officer commenced field inspection on-site.',
        syncStatus: 'SAVED_LOCALLY',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        createdAt: new Date().toISOString()
      };
      saveQueue([queueItem, ...offlineQueue]);
      setIncidents(prev => prev.map(i => (i.id || i._id) === incId ? { ...i, status: 'In Progress', _offlinePending: true } : i));
      if (onConductInspection) onConductInspection({ ...inc, status: 'In Progress' });
      return;
    }

    try {
      await incidentsAPI.update(incId, { status: 'In Progress', expected_updated_at: inc.updated_at });
      if (onConductInspection) {
        onConductInspection({ ...inc, status: 'In Progress' });
      }
    } catch (err) {
      console.warn('Update status error:', err);
      if (onConductInspection) onConductInspection(inc);
    }
  };

  // Status Badge Helper for Offline Queue Items
  const renderSyncBadge = (syncStatus) => {
    switch (syncStatus) {
      case 'SAVED_LOCALLY':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200 flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>{t('savedLocally')}</span>
          </span>
        );
      case 'WAITING_TO_SYNC':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 border border-blue-200 flex items-center gap-1">
            <RefreshCw className="w-3 h-3 animate-spin" />
            <span>{t('waitingToSync')}</span>
          </span>
        );
      case 'SYNCED':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1">
            <Check className="w-3 h-3" />
            <span>{t('synced')}</span>
          </span>
        );
      case 'CONFLICT':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 border border-rose-300 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            <span>{t('conflictDetected')}</span>
          </span>
        );
      case 'SESSION_EXPIRED':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-orange-100 text-orange-800 border border-orange-300 flex items-center gap-1">
            <Lock className="w-3 h-3" />
            <span>{t('sessionExpired')}</span>
          </span>
        );
      case 'SYNC_FAILED':
      default:
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-100 text-red-800 border border-red-200 flex items-center gap-1">
            <AlertOctagon className="w-3 h-3" />
            <span>{t('syncFailed')}</span>
          </span>
        );
    }
  };

  const pendingSyncCount = offlineQueue.filter(i => i.syncStatus !== 'SYNCED').length;

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-[#172033] tracking-tight">{t('officerDashboard')}</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Field patrol queue, on-site clearance inspections, and resilient offline synchronization
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <div className="flex items-center gap-2 px-3 py-1 bg-white border border-slate-200 rounded-lg shadow-2xs text-xs font-semibold text-slate-700">
            <span className={`w-2 h-2 rounded-full ${effectiveOffline ? 'bg-amber-500' : 'bg-emerald-500'}`} />
            <span>{effectiveOffline ? 'Offline Active' : 'Connected to Server'}</span>
          </div>
        </div>
      </div>

      {/* Feature 1: Resilient Offline Architecture Control Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs ${effectiveOffline ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'}`}>
              {effectiveOffline ? <WifiOff className="w-4 h-4" /> : <Wifi className="w-4 h-4" />}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-bold text-slate-900">
                  {effectiveOffline ? t('offlineMode') : t('onlineMode')}
                </span>
                {isLoadedFromCache && (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                    {t('cachedNotice')}
                  </span>
                )}
                {isCacheExpired && (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-red-50 text-red-700 border border-red-200">
                    {t('cacheExpiredNotice')}
                  </span>
                )}
                {pendingSyncCount > 0 && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500 text-white">
                    {pendingSyncCount} {t('syncPending')}
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {t('offlineDisclaimer')}
              </p>
            </div>
          </div>

          {/* Action buttons: Toggle Simulation & Sync */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSimulateOffline(!simulateOffline)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${
                simulateOffline
                  ? 'bg-amber-500 text-white border-amber-600 hover:bg-amber-600'
                  : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
              }`}
            >
              {simulateOffline ? 'Disable Sim' : t('simulateOffline')}
            </button>

            {offlineQueue.length > 0 && (
              <button
                onClick={handleSyncQueue}
                disabled={isSyncing || effectiveOffline}
                className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-2xs flex items-center gap-1.5 transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
                <span>{isSyncing ? 'Syncing...' : `${t('syncNow')} (${pendingSyncCount})`}</span>
              </button>
            )}
          </div>
        </div>

        {/* Sync feedback banner */}
        {syncFeedback && (
          <div className={`p-3 rounded-lg text-xs font-medium flex items-center justify-between border ${
            syncFeedback.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
              : syncFeedback.type === 'error'
              ? 'bg-red-50 text-red-800 border-red-200'
              : 'bg-blue-50 text-blue-800 border-blue-200'
          }`}>
            <span>{syncFeedback.message}</span>
            <button onClick={() => setSyncFeedback(null)} className="font-bold underline text-[11px] ml-2">
              Dismiss
            </button>
          </div>
        )}

        {/* Queued Items Drawer / History */}
        {offlineQueue.length > 0 && (
          <div className="bg-[#F5F7FA] rounded-lg p-3 border border-slate-200 text-xs space-y-2">
            <div className="font-bold text-slate-700 flex items-center justify-between">
              <span>Local Offline Queue ({offlineQueue.length} items):</span>
              <div className="flex items-center gap-2">
                {offlineQueue.some(i => i.syncStatus === 'SYNCED') && (
                  <button
                    onClick={handleClearSynced}
                    className="text-[10px] text-slate-500 hover:text-slate-800 underline font-semibold"
                  >
                    Clear Synced
                  </button>
                )}
                <span className="text-[11px] text-slate-500 font-normal">Stored locally</span>
              </div>
            </div>
            <div className="divide-y divide-slate-200 max-h-48 overflow-y-auto">
              {offlineQueue.map(item => (
                <div key={item.client_sync_id || item.id} className="py-2 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-1.5">
                      <span className="font-bold text-slate-800">{item.incidentTitle}</span>
                      <span className="text-slate-400 font-mono text-[10px]">({item.incidentNumber})</span>
                      <span className="text-blue-600 font-semibold text-[10px]">[{item.status}]</span>
                    </div>
                    {item.notes && (
                      <div className="text-slate-500 text-[11px] italic truncate max-w-md">
                        "{item.notes}"
                      </div>
                    )}
                    {item.errorMessage && (
                      <div className="text-red-600 text-[10px] font-semibold">
                        Error: {item.errorMessage}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    {renderSyncBadge(item.syncStatus)}

                    {/* Conflict Action Button */}
                    {item.syncStatus === 'CONFLICT' && (
                      <button
                        onClick={() => setActiveConflictItem(item)}
                        className="px-2 py-1 rounded bg-rose-600 hover:bg-rose-700 text-white font-bold text-[10px] shadow-xs"
                      >
                        {t('resolveConflict')}
                      </button>
                    )}

                    {/* Discard draft button */}
                    <button
                      onClick={() => handleDiscardDraft(item.client_sync_id)}
                      className="p-1 text-slate-400 hover:text-red-500"
                      title={t('discardDraft')}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 3 Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Assigned */}
        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-slate-900">{stats.assigned}</div>
            <div className="text-xs font-semibold text-slate-500 mt-0.5">{t('assigned')} Cases</div>
          </div>
          <div className="w-9 h-9 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100">
            <Clock className="w-4 h-4" />
          </div>
        </div>

        {/* In Progress */}
        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-amber-600">{stats.inProgress}</div>
            <div className="text-xs font-semibold text-slate-500 mt-0.5">{t('inProgress')} Inspection</div>
          </div>
          <div className="w-9 h-9 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center border border-amber-100">
            <Play className="w-4 h-4" />
          </div>
        </div>

        {/* Resolved */}
        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-[#059669]">{stats.resolved}</div>
            <div className="text-xs font-semibold text-slate-500 mt-0.5">{t('resolved')} Clearances</div>
          </div>
          <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
            <CheckCircle2 className="w-4 h-4" />
          </div>
        </div>
      </div>

      {/* Officer Mode Switcher */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2.5">
        <button
          onClick={() => setActiveTabMode('patrol')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-2 ${
            activeTabMode === 'patrol'
              ? 'bg-slate-900 text-white shadow-2xs'
              : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <Clock className="w-3.5 h-3.5" />
          <span>Assigned Field Patrol ({incidents.length})</span>
        </button>

        <button
          onClick={() => setActiveTabMode('review-queue')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-2 ${
            activeTabMode === 'review-queue'
              ? 'bg-slate-900 text-white shadow-2xs'
              : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>AI Human Review Queue ({reviewStats.total_queued})</span>
        </button>
      </div>

      {/* Main Content Area */}
      {activeTabMode === 'review-queue' ? (
        <div className="bg-white rounded-xl border border-slate-200/90 shadow-2xs p-5 sm:p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900 tracking-tight">AI Human Review Queue</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Incidents requiring human verification due to low AI confidence (&lt;60%) or conflicting evidence
              </p>
            </div>

            {/* Filter buttons */}
            <div className="flex items-center gap-1.5 flex-wrap">
              {[
                { id: 'ALL', label: 'All Queued' },
                { id: 'LOW_CONFIDENCE', label: 'Low Confidence' },
                { id: 'CONFLICTING', label: 'Conflicting Evidence' },
                { id: 'UNCERTAIN', label: 'Uncertain' }
              ].map(f => (
                <button
                  key={f.id}
                  onClick={() => setReviewFilter(f.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
                    reviewFilter === f.id
                      ? 'bg-slate-900 text-white border-slate-900 shadow-2xs'
                      : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {loadingReviewQueue ? (
            <div className="p-12 text-center text-slate-500">
              <div className="animate-spin w-7 h-7 border-3 border-slate-700 border-t-transparent rounded-full mx-auto mb-3" />
              <p className="text-xs font-medium text-slate-600">{t('loading')}</p>
            </div>
          ) : reviewQueue.length === 0 ? (
            <div className="p-12 text-center text-slate-400 text-xs">
              <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2 opacity-80" />
              <p className="font-semibold text-slate-700">Review Queue is Clear</p>
              <p className="mt-1 text-slate-500">All AI findings in this filter have been verified or have high model confidence.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {reviewQueue.map((item) => {
                const inc = item.incident;
                return (
                  <div
                    key={inc.id || inc._id}
                    className="py-3.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-slate-50/80 p-2.5 rounded-lg transition-colors group"
                  >
                    <div className="flex items-center gap-3.5 min-w-0">
                      <img
                        src={inc.privacy_image_url || inc.image_url || '/uploads/original/clear_street.jpg'}
                        alt={inc.title}
                        onError={(e) => { e.currentTarget.onerror = null; e.currentTarget.src = '/uploads/original/clear_street.jpg'; }}
                        className="w-12 h-12 rounded-lg object-cover border border-slate-200 shrink-0 bg-slate-100"
                      />

                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="text-xs font-bold text-slate-900 group-hover:text-blue-700 transition-colors truncate">
                            {inc.primary_encroachment_type || inc.title}
                          </h3>
                          <span className="font-mono text-[11px] text-slate-400">
                            {inc.incident_number}
                          </span>
                        </div>

                        <div className="text-[11px] text-slate-500 flex items-center gap-1.5 mt-0.5">
                          <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                          <span className="truncate">{inc.location_name || 'Location'}</span>
                        </div>

                        {/* Review reason warning pills */}
                        <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
                          {item.review_reasons?.map((r, idx) => (
                            <span
                              key={idx}
                              className={`text-[10px] font-medium px-2 py-0.5 rounded border ${
                                r.includes('Conflicting')
                                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                                  : r.includes('Low')
                                  ? 'bg-amber-50 text-amber-700 border-amber-200'
                                  : 'bg-slate-100 text-slate-700 border-slate-200'
                              }`}
                            >
                              {r}
                            </span>
                          ))}
                          <SeverityBadge severity={inc.severity} />
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                      <button
                        onClick={() => onSelectIncident && onSelectIncident(inc)}
                        className="px-3.5 py-1.5 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg shadow-2xs transition-colors flex items-center gap-1.5"
                      >
                        <ShieldCheck className="w-3.5 h-3.5" />
                        <span>Review AI Finding</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        /* Patrol List */
        <div className="bg-white rounded-xl border border-slate-200/90 shadow-2xs p-5 sm:p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-900 tracking-tight">Assigned Inspection Queue</h2>
              <p className="text-xs text-slate-500 mt-0.5">Field operations and scheduled corridor audits</p>
            </div>
            <span className="text-xs text-slate-500 font-medium px-2.5 py-1 bg-slate-100 rounded-md border border-slate-200">{incidents.length} tasks</span>
          </div>

          {incidents.length > 0 ? (
            <div className="divide-y divide-slate-100">
            {incidents.map((inc) => {
              const isAssigned = inc.status === 'Assigned' || inc.status === 'Pending' || inc.status === 'Verified';
              const isInProgress = inc.status === 'In Progress';
              const queuedItem = offlineQueue.find(q => q.incidentId === (inc.id || inc._id));

              return (
                <div
                  key={inc.id || inc._id}
                  className="py-3.5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-slate-50/80 p-2.5 rounded-lg transition-colors group"
                >
                  {/* Left: Thumbnail & Details */}
                  <div className="flex items-center gap-3.5 min-w-0">
                    <img
                      src={inc.privacy_image_url || inc.image_url || '/uploads/original/clear_street.jpg'}
                      alt={inc.title}
                      onError={(e) => { e.currentTarget.onerror = null; e.currentTarget.src = '/uploads/original/clear_street.jpg'; }}
                      className="w-12 h-12 rounded-lg object-cover border border-slate-200 shrink-0 bg-slate-100"
                    />

                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-xs font-bold text-slate-900 group-hover:text-blue-700 transition-colors truncate">
                          {inc.primary_encroachment_type || inc.title}
                        </h3>
                        <span className="font-mono text-[11px] text-slate-400">
                          {inc.incident_number}
                        </span>
                        {queuedItem && renderSyncBadge(queuedItem.syncStatus)}
                      </div>
                      <div className="text-[11px] text-slate-500 flex items-center gap-1.5 mt-0.5">
                        <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span className="truncate">{inc.location_name || 'Corridor Location'}</span>
                      </div>

                      <div className="flex items-center gap-2 mt-1.5">
                        <SeverityBadge severity={inc.severity} />
                        <StatusBadge status={inc.status} />
                      </div>
                    </div>
                  </div>

                  {/* Right: Actions [Start], [Update], [Field Note], [View] */}
                  <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                    {isAssigned && (
                      <button
                        onClick={() => handleStartInspection(inc)}
                        className="px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-2xs transition-colors"
                      >
                        Start
                      </button>
                    )}

                    {isInProgress && (
                      <button
                        onClick={() => onConductInspection && onConductInspection(inc)}
                        className="px-3 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-2xs transition-colors flex items-center gap-1.5"
                      >
                        <Camera className="w-3.5 h-3.5" />
                        <span>Update</span>
                      </button>
                    )}

                    {/* Offline Quick Note Button */}
                    <button
                      onClick={() => {
                        setActiveModalIncident(inc);
                        setFieldStatus(inc.status || 'In Progress');
                        setFieldNote(inc.inspection_notes || '');
                      }}
                      className="px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-lg transition-colors flex items-center gap-1.5"
                      title="Log Field Note / Offline Action"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span className="hidden md:inline">Log Note</span>
                    </button>

                    <button
                      onClick={() => onSelectIncident && onSelectIncident(inc)}
                      className="px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent hover:border-slate-200 rounded-lg transition-colors"
                    >
                      {t('viewDetails')}
                    </button>
                  </div>
                </div>
              );
            })}
            </div>
          ) : (
            <div className="p-12 text-center text-slate-400 text-xs">
              <CheckCircle2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="font-semibold text-slate-700">No assigned incidents in your jurisdiction</p>
              <p className="mt-1 text-slate-500">You have no pending field patrols or on-site inspections at this time.</p>
            </div>
          )}
        </div>
      )}

      {/* Field Inspection / Offline Note Modal */}
      {activeModalIncident && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-slate-200/90 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                  {effectiveOffline ? 'Queue Field Update (Offline Draft)' : t('quickInspectionNote')}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {activeModalIncident.primary_encroachment_type} • {activeModalIncident.location_name}
                </p>
              </div>
              <button
                onClick={() => setActiveModalIncident(null)}
                className="text-slate-400 hover:text-slate-600 font-semibold text-base w-7 h-7 flex items-center justify-center rounded-lg hover:bg-slate-100 transition-colors"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveFieldUpdate} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Status Transition</label>
                <select
                  value={fieldStatus}
                  onChange={(e) => setFieldStatus(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                >
                  <option value="In Progress">{t('inProgress')}</option>
                  <option value="Resolved">{t('resolved')}</option>
                  <option value="Assigned">{t('assigned')}</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Field Observations & Notes</label>
                <textarea
                  rows="3"
                  value={fieldNote}
                  onChange={(e) => setFieldNote(e.target.value)}
                  placeholder={t('fieldNotesPlaceholder')}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs font-normal focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setActiveModalIncident(null)}
                  className="px-3.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  {t('cancel')}
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg flex items-center gap-1.5 shadow-2xs transition-colors"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>{effectiveOffline ? 'Save Draft Locally' : t('save')}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Feature 1: Conflict Resolution Modal (Requirement 8) */}
      {activeConflictItem && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{t('conflictDetected')}</h3>
                  <p className="text-xs text-slate-500">{activeConflictItem.incidentNumber} • {activeConflictItem.locationName}</p>
                </div>
              </div>
              <button
                onClick={() => setActiveConflictItem(null)}
                className="text-slate-400 hover:text-slate-600 font-semibold text-base w-7 h-7 flex items-center justify-center rounded-lg hover:bg-slate-100 transition-colors"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              This incident was modified on the server by another municipal officer or administrator while your device was offline. Please compare versions and select a resolution strategy:
            </p>

            {/* Side by side versions */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              {/* Server State */}
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
                <div className="font-semibold text-blue-700 uppercase text-[10px] tracking-wider">Server Version</div>
                <div>Status: <strong className="text-slate-900">{activeConflictItem.conflictData?.status || 'Unknown'}</strong></div>
                {activeConflictItem.conflictData?.assigned_officer_name && (
                  <div>By: <span className="text-slate-700">{activeConflictItem.conflictData.assigned_officer_name}</span></div>
                )}
                {activeConflictItem.conflictData?.inspection_notes && (
                  <div className="text-[11px] text-slate-600 italic">"{activeConflictItem.conflictData.inspection_notes}"</div>
                )}
                <div className="text-[10px] text-slate-400">Last updated: {activeConflictItem.conflictData?.updated_at || 'Recent'}</div>
              </div>

              {/* Officer Local Draft */}
              <div className="p-3 rounded-lg bg-amber-50/50 border border-amber-200 space-y-1.5">
                <div className="font-semibold text-amber-800 uppercase text-[10px] tracking-wider">Your Offline Draft</div>
                <div>Status: <strong className="text-slate-900">{activeConflictItem.status}</strong></div>
                {activeConflictItem.notes && (
                  <div className="text-[11px] text-slate-700 italic">"{activeConflictItem.notes}"</div>
                )}
                <div className="text-[10px] text-slate-500">Recorded: {activeConflictItem.timestamp}</div>
              </div>
            </div>

            {/* Conflict Actions */}
            <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => handleAcceptServerVersion(activeConflictItem)}
                className="flex-1 py-2 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
              >
                {t('acceptServer')}
              </button>

              <button
                onClick={() => handleForceOverwriteServer(activeConflictItem)}
                className="flex-1 py-2 px-3 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors"
              >
                {t('overwriteServer')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
