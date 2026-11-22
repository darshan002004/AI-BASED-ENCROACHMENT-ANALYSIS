import React, { useState, useEffect } from 'react';
import {
  Database,
  CheckCircle,
  XCircle,
  Edit3,
  HelpCircle,
  Download,
  RefreshCw,
  Filter,
  ShieldCheck,
  Check,
  X,
  FileText,
  AlertTriangle,
  Info,
  Layers,
  Cpu
} from 'lucide-react';
import { feedbackAPI } from '../../services/api';

export default function AIFeedbackPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('ALL');
  const [approvalFilter, setApprovalFilter] = useState('ALL');
  const [actionMessage, setActionMessage] = useState(null);
  const [processingId, setProcessingId] = useState(null);
  const [workflowInfo, setWorkflowInfo] = useState(null);
  const [showWorkflowModal, setShowWorkflowModal] = useState(false);

  useEffect(() => {
    fetchDataset();
    fetchWorkflowInfo();
  }, [actionFilter, approvalFilter]);

  const fetchDataset = async () => {
    setLoading(true);
    try {
      const params = {};
      if (actionFilter !== 'ALL') params.action = actionFilter;
      if (approvalFilter !== 'ALL') params.approval_status = approvalFilter;
      const res = await feedbackAPI.getDataset(params);
      setItems(res.data.items || []);
    } catch (err) {
      console.error('Error fetching feedback dataset:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchWorkflowInfo = async () => {
    try {
      const res = await feedbackAPI.getTrainingWorkflow();
      setWorkflowInfo(res.data);
    } catch (e) {
      console.warn('Could not load workflow guidelines:', e);
    }
  };

  const handleApprove = async (id) => {
    setProcessingId(id);
    try {
      await feedbackAPI.approve(id);
      setActionMessage({ type: 'success', text: `Sample ${id} approved for retraining dataset.` });
      fetchDataset();
    } catch (err) {
      setActionMessage({ type: 'error', text: err.response?.data?.detail || 'Approval failed.' });
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (id) => {
    const reason = window.prompt('Please provide a reason for excluding this sample from the retraining dataset:');
    if (!reason || !reason.trim()) return;

    setProcessingId(id);
    try {
      await feedbackAPI.reject(id, reason.trim());
      setActionMessage({ type: 'info', text: `Sample ${id} rejected and excluded from retraining pool.` });
      fetchDataset();
    } catch (err) {
      setActionMessage({ type: 'error', text: err.response?.data?.detail || 'Rejection failed.' });
    } finally {
      setProcessingId(null);
    }
  };

  const handleExport = (format) => {
    const exportUrl = feedbackAPI.getExportUrl(format, approvalFilter);
    window.open(exportUrl, '_blank');
  };

  const getActionBadge = (action) => {
    switch ((action || '').toUpperCase()) {
      case 'CONFIRM':
        return { label: 'Confirmed (True Pos)', icon: CheckCircle, cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
      case 'REJECT':
        return { label: 'Rejected (False Pos)', icon: XCircle, cls: 'bg-rose-50 text-rose-700 border-rose-200' };
      case 'MODIFY':
        return { label: 'Category Corrected', icon: Edit3, cls: 'bg-amber-50 text-amber-700 border-amber-200' };
      default:
        return { label: 'Needs Evidence', icon: HelpCircle, cls: 'bg-slate-100 text-slate-700 border-slate-200' };
    }
  };

  const getApprovalBadge = (status) => {
    switch ((status || 'APPROVED').toUpperCase()) {
      case 'APPROVED':
        return { label: 'Approved for Retraining', cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
      case 'REJECTED':
        return { label: 'Excluded / Rejected', cls: 'bg-rose-50 text-rose-700 border-rose-200' };
      default:
        return { label: 'Pending Admin Sign-Off', cls: 'bg-amber-50 text-amber-700 border-amber-200' };
    }
  };

  return (
    <div className="space-y-5 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200/90 shadow-2xs">
        <div>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="p-1 rounded-md bg-blue-50 text-blue-700 border border-blue-100">
              <Database className="w-4 h-4" />
            </span>
            <h1 className="text-base font-bold text-slate-900 tracking-tight">AI Feedback Dataset & Active Learning</h1>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-slate-100 text-slate-700 border border-slate-200">
              Baseline: YOLOv5n-ONNX-v1.0
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Curated ground-truth corrections submitted by field officers to eliminate future false positives and audit municipal computer vision performance.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setShowWorkflowModal(true)}
            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors border border-slate-200"
          >
            <Cpu className="w-3.5 h-3.5 text-slate-600" />
            <span>Retraining Guidelines</span>
          </button>
          <button
            onClick={fetchDataset}
            className="p-1.5 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 transition-colors"
            title="Refresh dataset"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => handleExport('jsonl')}
            className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-2xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSONL</span>
          </button>
          <button
            onClick={() => handleExport('csv')}
            className="px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Action toast message */}
      {actionMessage && (
        <div className={`p-3.5 rounded-lg border text-xs font-semibold flex items-center justify-between ${
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

      {/* Retraining Governance Policy Callout */}
      <div className="bg-slate-50 border border-slate-200/90 p-4 rounded-xl shadow-2xs space-y-1.5">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-slate-700" />
            <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Supervised Retraining Governance Policy
            </span>
          </div>
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-200/80 text-slate-700 border border-slate-300/80">
            No Automated Retraining • No Silent Replacement
          </span>
        </div>
        <p className="text-xs text-slate-600 leading-relaxed">
          Municipal policy strictly prohibits unmonitored model self-updates or silent replacement in production. Candidate model weights undergo structured supervised fine-tuning with a <strong>70% Train / 15% Validation / 15% Test</strong> stratified split and must demonstrate empirical superiority (<strong>mAP@0.5 ≥ 0.82</strong>) with authorized municipal sign-off before deployment.
        </p>
      </div>

      {/* Filter Tabs Section */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/90 shadow-2xs space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Action Filter */}
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              Review Decision Filter:
            </span>
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
              {['ALL', 'CONFIRM', 'MODIFY', 'REJECT', 'NEEDS_MORE_EVIDENCE'].map((f) => (
                <button
                  key={f}
                  onClick={() => setActionFilter(f)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all border ${
                    actionFilter === f
                      ? 'bg-slate-900 text-white border-slate-900 shadow-2xs'
                      : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  {f === 'ALL' ? 'All Decisions' : f.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Approval Filter */}
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
              Dataset Status:
            </span>
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
              {['ALL', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED'].map((s) => (
                <button
                  key={s}
                  onClick={() => setApprovalFilter(s)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all border ${
                    approvalFilter === s
                      ? 'bg-slate-900 text-white border-slate-900 shadow-2xs'
                      : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  {s === 'ALL' ? 'All Status' : s.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Dataset Table */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-2xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">
            <div className="animate-spin w-7 h-7 border-3 border-slate-700 border-t-transparent rounded-full mx-auto mb-3" />
            <p className="text-xs font-medium text-slate-600">Loading feedback dataset records...</p>
          </div>
        ) : items.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            No feedback entries found matching active filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="py-3 px-4">Case #</th>
                  <th className="py-3 px-4">Officer Action</th>
                  <th className="py-3 px-4">Original AI Label</th>
                  <th className="py-3 px-4">Corrected Label</th>
                  <th className="py-3 px-4">Review Reason / Notes</th>
                  <th className="py-3 px-4">Reviewer</th>
                  <th className="py-3 px-4">Dataset Status</th>
                  <th className="py-3 px-4 text-right">Admin Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((item) => {
                  const badge = getActionBadge(item.action);
                  const Icon = badge.icon;
                  const appBadge = getApprovalBadge(item.approval_status);
                  const isProcessing = processingId === item.id;

                  return (
                    <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-slate-900 whitespace-nowrap">
                        {item.incident_number || item.incident_id}
                        <span className="text-[10px] text-slate-400 block font-normal">
                          {item.id}
                        </span>
                      </td>

                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded font-semibold text-[11px] border ${badge.cls}`}>
                          <Icon className="w-3 h-3" />
                          <span>{badge.label}</span>
                        </span>
                      </td>

                      <td className="py-3 px-4 font-medium text-slate-700">
                        {item.original_ai_category}
                        <span className="text-[10px] text-slate-400 block">
                          Conf: {item.original_ai_confidence ? `${Math.round(item.original_ai_confidence * 100)}%` : 'N/A'}
                        </span>
                      </td>

                      <td className="py-3 px-4 font-semibold text-slate-900 whitespace-nowrap">
                        {item.corrected_category || item.original_ai_category}
                      </td>

                      <td className="py-3 px-4 text-slate-600 max-w-xs">
                        <span className="block truncate font-normal" title={item.notes}>
                          {item.notes || '—'}
                        </span>
                      </td>

                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className="font-semibold text-slate-900 block">{item.reviewer_name}</span>
                        <span className="text-[10px] text-slate-400 uppercase font-mono">{item.reviewer_role}</span>
                      </td>

                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${appBadge.cls}`}>
                          {appBadge.label}
                        </span>
                      </td>

                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          {item.approval_status !== 'APPROVED' && (
                            <button
                              onClick={() => handleApprove(item.id)}
                              disabled={isProcessing}
                              className="px-2.5 py-1 rounded bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-semibold text-[11px] border border-emerald-200 transition-colors"
                              title="Approve for retraining dataset"
                            >
                              Approve
                            </button>
                          )}
                          {item.approval_status !== 'REJECTED' && (
                            <button
                              onClick={() => handleReject(item.id)}
                              disabled={isProcessing}
                              className="px-2.5 py-1 rounded bg-rose-50 hover:bg-rose-100 text-rose-700 font-semibold text-[11px] border border-rose-200 transition-colors"
                              title="Reject / Exclude from retraining dataset"
                            >
                              Reject
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Retraining Guidelines Modal */}
      {showWorkflowModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-xl w-full p-6 shadow-xl border border-slate-200/90 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-slate-700" />
                <h3 className="text-sm font-bold text-slate-900">
                  Model Retraining & Validation Protocol
                </h3>
              </div>
              <button
                onClick={() => setShowWorkflowModal(false)}
                className="text-slate-400 hover:text-slate-600 font-semibold text-base w-7 h-7 flex items-center justify-center rounded-lg hover:bg-slate-100 transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs text-slate-600 leading-relaxed">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
                <span className="font-semibold text-slate-900 block">Dataset Partitioning Standard:</span>
                <p className="text-slate-700">
                  • <strong>70% Training Set:</strong> Used for supervised fine-tuning of convolutional backbone weights.<br />
                  • <strong>15% Validation Set:</strong> Hyperparameter tuning and early stopping.<br />
                  • <strong>15% Withheld Test Set:</strong> Evaluates generalization on unseen urban corridors.
                </p>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
                <span className="font-semibold text-slate-900 block">Performance Benchmark Metric:</span>
                <p>
                  Target benchmark: <strong>mAP@0.5 ≥ 0.82</strong> across all 5 municipal encroachment classes. Candidate model must demonstrate non-regression on high-severity pedestrian corridor blockages.
                </p>
              </div>

              <div className="space-y-1 pt-2">
                <span className="font-semibold text-slate-900 block">Governance Steps Before Production Deployment:</span>
                <ol className="list-decimal pl-5 space-y-1 text-slate-700">
                  <li>Officer Ground-Truth Collection in live municipal database.</li>
                  <li>Admin Data Sanitization & Export (PII stripped).</li>
                  <li>Offline fine-tuning on isolated GPU compute cluster.</li>
                  <li>Validation test against withheld 15% test benchmark.</li>
                  <li>Municipal commissioner and lead engineer formal sign-off.</li>
                  <li>Staged rollout with instant rollback capability.</li>
                </ol>
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-100">
              <button
                onClick={() => setShowWorkflowModal(false)}
                className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-lg transition-colors"
              >
                Close Protocol
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
