import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Download,
  MapPin,
  Calendar,
  Clock,
  ShieldCheck,
  User,
  AlertTriangle,
  CheckCircle2,
  Send,
  Sparkles,
  Eye,
  EyeOff,
  Check,
  X,
  Edit2,
  HelpCircle,
  TrendingUp,
  Layers,
  ChevronRight,
  Flame,
  Gauge,
  Camera,
  ShieldAlert,
  MessageSquare,
  RotateCcw,
  FileCheck,
  XCircle
} from 'lucide-react';
import axios from 'axios';
import { StatusBadge, SeverityBadge } from '../../components/StatusBadge';
import BeforeAfterCompare from '../../components/BeforeAfterCompare';
import { incidentsAPI, reportsAPI, authAPI, feedbackAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

export default function IncidentDetailPage({ incidentId, onBack }) {
  const { role, user } = useAuth();
  const [incident, setIncident] = useState(null);
  const [officers, setOfficers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [showPrivacyView, setShowPrivacyView] = useState(true);
  const [selectedEvidenceIdx, setSelectedEvidenceIdx] = useState(0);

  // Human-in-the-loop verification modal state
  const [showModifyModal, setShowModifyModal] = useState(false);
  const [modCategory, setModCategory] = useState('');
  const [modNotes, setModNotes] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [showEvidenceRequestModal, setShowEvidenceRequestModal] = useState(false);
  const [evidenceRequestReason, setEvidenceRequestReason] = useState('');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [reviewFeedbackMsg, setReviewFeedbackMsg] = useState(null);
  const [isEditingVerification, setIsEditingVerification] = useState(false);

  // Priority override modal state
  const [showPriorityModal, setShowPriorityModal] = useState(false);
  const [newPriorityScore, setNewPriorityScore] = useState(75);
  const [newPriorityRank, setNewPriorityRank] = useState('Urgent');
  const [newPriorityAction, setNewPriorityAction] = useState('Immediate Dispatch');

  // Batch 2: Duplicate Intelligence State
  const [possibleDuplicates, setPossibleDuplicates] = useState(null);
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [selectedDuplicate, setSelectedDuplicate] = useState(null);
  const [mergingDuplicate, setMergingDuplicate] = useState(false);

  // Batch 2: Historical Risk Forecast State
  const [riskForecast, setRiskForecast] = useState(null);

  // Batch 2: Evidence Upload State
  const [showAddEvidenceModal, setShowAddEvidenceModal] = useState(false);
  const [evidenceFile, setEvidenceFile] = useState(null);
  const [evidenceCaption, setEvidenceCaption] = useState('Secondary Perspective');
  const [uploadingEvidence, setUploadingEvidence] = useState(false);

  // Batch 5.5: Resolution Verification & Reopening State
  const [showResolutionSubmitModal, setShowResolutionSubmitModal] = useState(false);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [resolutionAfterFile, setResolutionAfterFile] = useState(null);
  const [submittingResolution, setSubmittingResolution] = useState(false);

  const [showResolutionReviewModal, setShowResolutionReviewModal] = useState(false);
  const [resolutionReviewDecision, setResolutionReviewDecision] = useState('ACCEPT');
  const [resolutionReviewNotes, setResolutionReviewNotes] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);

  const [showReopenModal, setShowReopenModal] = useState(false);
  const [reopenReasonText, setReopenReasonText] = useState('');
  const [submittingReopen, setSubmittingReopen] = useState(false);

  const fetchIncident = async () => {
    if (!incidentId) {
      setLoading(false);
      return;
    }
    try {
      const res = await incidentsAPI.getById(incidentId);
      setIncident(res.data);
      if (res.data.privacy_protected) {
        setShowPrivacyView(true);
      }
      setModCategory(res.data.primary_encroachment_type || 'Street Vendor');
      setNewPriorityScore(res.data.priority_score || 70);
      setNewPriorityRank(res.data.priority_rank || 'Urgent');
      setNewPriorityAction(res.data.priority_action || 'Immediate Dispatch');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!incidentId) {
      setLoading(false);
      return;
    }
    fetchIncident();
    authAPI.getOfficers().then(r => setOfficers(r.data || [])).catch(console.error);
    incidentsAPI.getPossibleDuplicates(incidentId).then(r => setPossibleDuplicates(r.data)).catch(console.warn);
    incidentsAPI.getRiskForecast(incidentId).then(r => setRiskForecast(r.data)).catch(console.warn);
  }, [incidentId]);

  const handleStatusChange = async (newStatus) => {
    if (!incident) return;
    try {
      const res = await incidentsAPI.update(incident.id, { status: newStatus });
      setIncident(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAssignOfficer = async (offId) => {
    const off = officers.find(o => o.id === offId);
    try {
      const res = await incidentsAPI.update(incident.id, {
        assigned_officer_id: offId,
        assigned_officer_name: off?.full_name || 'Field Officer',
        status: 'Assigned'
      });
      setIncident(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRunAIVerification = async () => {
    if (!incident) return;
    setIsVerifying(true);
    try {
      const res = await incidentsAPI.verifyResolution(incident.id);
      setIncident(res.data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to verify resolution. Ensure officer has uploaded inspection photo.');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleSubmitResolution = async (e) => {
    e.preventDefault();
    if (!incident) return;
    if (!resolutionNotes.trim() || resolutionNotes.trim().length < 10) {
      alert('Resolution notes must be at least 10 characters detailing field clearance actions.');
      return;
    }
    if (!resolutionAfterFile && (!incident.after_images || incident.after_images.length === 0)) {
      alert('An after-clearance verification photo is mandatory.');
      return;
    }
    try {
      setSubmittingResolution(true);
      const afterUrl = resolutionAfterFile ? URL.createObjectURL(resolutionAfterFile) : (incident.image_url || '/uploads/original/clear_street.jpg');
      const res = await incidentsAPI.submitResolution(incident.id, {
        resolution_notes: resolutionNotes.trim(),
        after_image_url: afterUrl
      });
      setIncident(res.data);
      setShowResolutionSubmitModal(false);
      setResolutionNotes('');
      setResolutionAfterFile(null);
      alert('Formal clearance resolution submitted. Awaiting supervisor signoff.');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to submit clearance resolution.');
    } finally {
      setSubmittingResolution(false);
    }
  };

  const handleReviewResolution = async (decision) => {
    if (!incident) return;
    if (decision === 'REJECT' && (!resolutionReviewNotes || !resolutionReviewNotes.trim())) {
      alert('A documented justification reason is mandatory when rejecting a resolution.');
      return;
    }
    try {
      setSubmittingReview(true);
      const res = await incidentsAPI.reviewResolution(incident.id, {
        decision,
        reason: resolutionReviewNotes.trim() || undefined,
        notes: resolutionReviewNotes.trim() || undefined,
      });
      setIncident(res.data);
      setShowResolutionReviewModal(false);
      setResolutionReviewNotes('');
      alert(`Resolution ${decision === 'ACCEPT' ? 'verified and accepted' : 'rejected and returned to investigation'}.`);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to review resolution.');
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleReopenIncident = async (e) => {
    e.preventDefault();
    if (!incident) return;
    if (!reopenReasonText.trim() || reopenReasonText.trim().length < 5) {
      alert('A detailed justification is mandatory to reopen a resolved incident.');
      return;
    }
    try {
      setSubmittingReopen(true);
      const res = await incidentsAPI.reopen(incident.id, {
        reason: reopenReasonText.trim(),
      });
      setIncident(res.data);
      setShowReopenModal(false);
      setReopenReasonText('');
      alert('Incident has been reopened and returned to active municipal queue.');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to reopen incident.');
    } finally {
      setSubmittingReopen(false);
    }
  };

  const handleFeedbackAction = async (actionType, corrected = null, notes = '') => {
    if (!incident) return;

    const trimmedNotes = (notes || '').trim();
    if ((actionType === 'REJECT' || actionType === 'MODIFY') && !trimmedNotes) {
      alert(`A valid reason is mandatory when ${actionType.toLowerCase()}ing an AI detection finding.`);
      return;
    }

    if (actionType === 'MODIFY' && !(corrected || '').trim()) {
      alert('A corrected category must be selected.');
      return;
    }

    setSubmittingFeedback(true);
    setReviewFeedbackMsg(null);
    try {
      const payload = {
        incident_id: incident.id,
        action: actionType,
        original_ai_category: incident.original_ai_category || incident.primary_encroachment_type,
        original_ai_confidence: incident.confidence,
        corrected_category: corrected ? corrected.trim() : null,
        notes: trimmedNotes
      };
      await feedbackAPI.verify(payload);
      setShowModifyModal(false);
      setShowRejectModal(false);
      setShowEvidenceRequestModal(false);
      setIsEditingVerification(false);
      setReviewFeedbackMsg({
        type: 'success',
        text: `Official human review decision (${actionType}) recorded successfully!`
      });
      fetchIncident();
    } catch (err) {
      setReviewFeedbackMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Error recording review verification.'
      });
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const handleOverridePriority = async () => {
    try {
      const res = await axios.post(
        `/api/incidents/${incident.id}/override-priority?priority_score=${newPriorityScore}&priority_rank=${encodeURIComponent(newPriorityRank)}&priority_action=${encodeURIComponent(newPriorityAction)}`
      );
      setIncident(res.data);
      setShowPriorityModal(false);
    } catch (e) {
      alert('Error updating priority.');
    }
  };

  const handleMergeDuplicate = async (masterId) => {
    if (!masterId) return;
    setMergingDuplicate(true);
    try {
      await incidentsAPI.mergeDuplicate(incident.id, masterId);
      setShowDuplicateModal(false);
      fetchIncident();
      alert('Successfully merged duplicate report into master incident.');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to merge duplicate.');
    } finally {
      setMergingDuplicate(false);
    }
  };

  const handleKeepSeparate = async () => {
    try {
      await incidentsAPI.keepSeparate(incident.id, 'Admin verified case is distinct and physically independent');
      setPossibleDuplicates(prev => prev ? { ...prev, duplicate_dismissed: true, candidates: [] } : null);
      fetchIncident();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to dismiss duplicate alert.');
    }
  };

  const handleAddEvidence = async () => {
    if (!evidenceFile) {
      alert('Please select an image file first.');
      return;
    }
    setUploadingEvidence(true);
    const fd = new FormData();
    fd.append('file', evidenceFile);
    try {
      const res = await incidentsAPI.addEvidence(incident.id, fd, evidenceCaption);
      setIncident(res.data);
      setShowAddEvidenceModal(false);
      setEvidenceFile(null);
      alert('Evidence attached successfully with separate AI perspective analysis!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to attach evidence.');
    } finally {
      setUploadingEvidence(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400">
        Loading incident details...
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="p-12 text-center text-slate-400 space-y-3">
        <p className="font-bold text-slate-700 text-sm">No Incident Selected or Found</p>
        <p className="text-xs">Please select an incident from the Incident Queue to view details.</p>
        {onBack && (
          <button
            onClick={onBack}
            className="px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700 transition-colors"
          >
            Return to Incidents
          </button>
        )}
      </div>
    );
  }

  const isAuthorizedForRaw = role === 'admin' || role === 'officer' || (user?.id && user?.id === incident.reporter_id);

  // Active displayed image (supports multi-image gallery switcher)
  const evidenceList = incident.evidence_images && incident.evidence_images.length > 0
    ? incident.evidence_images
    : [{ id: 'main', image_url: incident.image_url, caption: 'Primary Photo' }];

  const currentDisplayImage = (showPrivacyView && incident.privacy_image_url) || !isAuthorizedForRaw
    ? (evidenceList[selectedEvidenceIdx]?.privacy_image_url || incident.privacy_image_url || evidenceList[selectedEvidenceIdx]?.image_url || incident.image_url)
    : (evidenceList[selectedEvidenceIdx]?.image_url || incident.image_url);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Top Header & Dossier Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors shadow-xs"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight font-mono">
                {incident.incident_number}
              </h1>
              <SeverityBadge severity={incident.severity} />
              <StatusBadge status={incident.status} />
              {incident.privacy_protected && (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" />
                  <span>Privacy Protected</span>
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">{incident.title}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => window.open(reportsAPI.getIncidentPDFUrl(incident.id), '_blank')}
            className="px-4 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            Download PDF Dossier
          </button>
        </div>
      </div>

      {/* Top Banner: Duplicate Consolidated Case */}
      {incident.is_duplicate_merged && (
        <div className="p-4 rounded-2xl bg-blue-50 border border-blue-200 text-xs flex items-center justify-between text-blue-900 shadow-xs">
          <div className="flex items-center gap-2.5">
            <Layers className="w-5 h-5 text-blue-600 shrink-0" />
            <div>
              <span className="font-extrabold text-sm block">Consolidated Duplicate Report</span>
              <span className="opacity-90">
                This incident report has been merged into master ticket <strong>{incident.merged_with_master_id}</strong>. Supporting evidence and citizen records are consolidated.
              </span>
            </div>
          </div>
          <button
            onClick={() => onBack()}
            className="px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shrink-0 transition-colors shadow-xs"
          >
            Return to Incidents
          </button>
        </div>
      )}

      {/* Top Banner: Inconsistent Evidence Alert */}
      {incident.evidence_inconsistency_flag && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-300 text-xs flex items-start gap-3 text-amber-900 shadow-xs">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-extrabold text-sm block">⚠️ Conflicting Evidence Perspectives Detected</span>
            <p className="opacity-90 leading-relaxed">
              {incident.evidence_inconsistency_reason || 'Evidence photos exhibit contradictory classifications across perspectives. Automatic decision withheld; municipal officer visual inspection required.'}
            </p>
            <span className="inline-block px-2 py-0.5 rounded bg-amber-200/80 font-bold text-[10px] text-amber-900">
              Verification Status: Needs Human Review
            </span>
          </div>
        </div>
      )}

      {/* Top Banner: Supervisory SLA Escalation Alert */}
      {incident.is_escalated && (
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-950 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0" />
            <div>
              <span className="font-extrabold text-sm block text-amber-900">
                ⚠️ Case Escalated to Supervisory Municipal Authority (Level {incident.escalation_level || 1})
              </span>
              <p className="text-amber-800 mt-0.5">
                Resolution SLA breached or approaching critical deadline. High-priority municipal intervention mandated.
              </p>
            </div>
          </div>
          <span className="px-3 py-1 bg-amber-600 text-white rounded-xl text-xs font-bold shrink-0">
            ESCALATED
          </span>
        </div>
      )}

      {/* Top Banner: Reopened Case Notice */}
      {incident.status === 'Reopened' && (
        <div className="p-4 rounded-2xl bg-purple-50 border border-purple-200 text-purple-950 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-3">
            <RotateCcw className="w-5 h-5 text-purple-600 shrink-0" />
            <div>
              <span className="font-extrabold text-sm block text-purple-900">
                🔄 Incident Case Reopened
              </span>
              <p className="text-purple-800 mt-0.5">
                Justification: {incident.reopen_reason || 'Previous resolution did not satisfy municipal or citizen clearance standards.'}
              </p>
            </div>
          </div>
          <span className="px-3 py-1 bg-purple-600 text-white rounded-xl text-xs font-bold shrink-0">
            REOPENED
          </span>
        </div>
      )}

      {/* Top Banner: Potential Duplicates Detected */}
      {possibleDuplicates?.candidates?.length > 0 && !incident.duplicate_dismissed && !incident.is_duplicate_merged && (
        <div className="p-4 rounded-2xl bg-purple-50 border border-purple-200 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-purple-900 shadow-xs">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-5 h-5 text-purple-600 shrink-0" />
            <div>
              <span className="font-extrabold text-sm block">
                Potential Duplicate Incident Detected ({possibleDuplicates.candidates.length} match{possibleDuplicates.candidates.length > 1 ? 'es' : ''})
              </span>
              <span className="opacity-90">
                Spatial &amp; temporal correlation found existing active reports within 60m matching this obstruction.
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0 self-end sm:self-auto">
            <button
              onClick={() => {
                setSelectedDuplicate(possibleDuplicates.candidates[0]);
                setShowDuplicateModal(true);
              }}
              className="px-3.5 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs transition-colors shadow-xs"
            >
              Compare &amp; Merge
            </button>
            <button
              onClick={handleKeepSeparate}
              className="px-3 py-1.5 rounded-xl bg-white border border-purple-300 hover:bg-purple-100 text-purple-800 font-bold text-xs transition-colors shadow-xs"
            >
              Keep Separate
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Visual Evidence, XAI Checklist, Timeline (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Visual Evidence Card with Privacy Toggle & Multi-Image Gallery */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <h2 className="text-sm font-bold text-slate-900">
                Visual Evidence &amp; Multi-Image Perspective
              </h2>

              <div className="flex items-center gap-2 flex-wrap">
                <button
                  onClick={() => setShowAddEvidenceModal(true)}
                  className="px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition-all shadow-xs"
                >
                  <Camera className="w-3.5 h-3.5 text-emerald-600" />
                  <span>+ Attach Photo</span>
                </button>

                {/* Privacy Protection Toggle (Batch 3 Feature 2) */}
                {incident.privacy_image_url && (
                  isAuthorizedForRaw ? (
                    <button
                      onClick={() => setShowPrivacyView(!showPrivacyView)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all border ${
                        showPrivacyView
                          ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                          : 'bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200'
                      }`}
                      title={showPrivacyView ? 'Switch to unredacted raw evidence (Officer/Admin access logged)' : 'Switch to privacy-protected view'}
                    >
                      {showPrivacyView ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                      <span>{showPrivacyView ? 'Privacy-Redacted View' : 'Original Raw Evidence (Authorized)'}</span>
                    </button>
                  ) : (
                    <span className="px-2.5 py-1 rounded-xl text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                      <span>Privacy Redacted View (Public)</span>
                    </span>
                  )
                )}
              </div>
            </div>

            {/* Main Stage Image */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <div className="text-xs font-semibold text-slate-500 mb-1.5 flex items-center justify-between">
                  <span>Inspection Photo</span>
                  {showPrivacyView && (
                    <span className="text-[10px] text-blue-600 font-bold">Faces & Plates Redacted</span>
                  )}
                </div>
                <div className="rounded-xl overflow-hidden border border-slate-200 bg-slate-100 relative">
                  <img
                    src={currentDisplayImage}
                    alt="Current perspective"
                    onError={(e) => { e.currentTarget.onerror = null; e.currentTarget.src = '/uploads/original/clear_street.jpg'; }}
                    className="w-full h-56 object-cover"
                  />
                  {showPrivacyView && (
                    <div className="absolute top-2 right-2 px-2 py-0.5 rounded-md bg-blue-900/80 text-white text-[10px] font-bold">
                      Privacy Redacted
                    </div>
                  )}
                </div>
              </div>

              <div>
                <div className="text-xs font-semibold text-slate-500 mb-1.5">AI Segmentation Overlay</div>
                <div className="rounded-xl overflow-hidden border border-slate-200 bg-slate-900">
                  <img
                    src={incident.annotated_image_url || incident.image_url}
                    alt="Annotated"
                    onError={(e) => { e.currentTarget.onerror = null; e.currentTarget.src = '/uploads/original/clear_street.jpg'; }}
                    className="w-full h-56 object-cover"
                  />
                </div>
              </div>
            </div>

            {/* Multi-Image Gallery Thumbnails (Upgrade 7) */}
            {evidenceList.length > 1 && (
              <div className="pt-2">
                <span className="text-xs font-semibold text-slate-500 block mb-2">
                  Evidence Photos ({evidenceList.length} Perspectives Attached):
                </span>
                <div className="flex gap-2 overflow-x-auto pb-1">
                  {evidenceList.map((ev, idx) => (
                    <button
                      key={ev.id || idx}
                      onClick={() => setSelectedEvidenceIdx(idx)}
                      className={`relative rounded-lg overflow-hidden border-2 shrink-0 transition-all ${
                        selectedEvidenceIdx === idx ? 'border-blue-600 ring-2 ring-blue-500/30' : 'border-slate-200 opacity-70 hover:opacity-100'
                      }`}
                    >
                      <img
                        src={ev.image_url}
                        alt=""
                        onError={(e) => { e.currentTarget.onerror = null; e.currentTarget.src = '/uploads/original/clear_street.jpg'; }}
                        className="w-16 h-12 object-cover"
                      />
                      <span className="absolute bottom-0 inset-x-0 bg-black/60 text-white text-[9px] truncate px-1 text-center">
                        {ev.caption || `Photo ${idx + 1}`}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Legend */}
            <div className="flex items-center gap-4 text-xs pt-2 border-t border-slate-100">
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-emerald-500" />
                <span className="text-slate-600">Footpath ROI</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-blue-500" />
                <span className="text-slate-600">Road</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-red-500" />
                <span className="text-slate-600">Encroachment Bounding Box</span>
              </div>
            </div>
          </div>

          {/* Advanced Accessibility & Corridor Analysis Card (Batch 1) */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Gauge className="w-4 h-4 text-emerald-600" />
                <span>Footpath Accessibility &amp; Corridor Intelligence</span>
              </h2>
              <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                EncroWatch Accessibility Score
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
                <span className="text-slate-400 block text-[10px] font-bold uppercase">Accessibility</span>
                <span className="text-xl font-black text-slate-900">{incident.accessibility_score ?? 100} / 100</span>
                <span className="block text-[11px] font-bold text-emerald-700">{incident.accessibility_category || 'Good'}</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
                <span className="text-slate-400 block text-[10px] font-bold uppercase">Occupancy</span>
                <span className="text-xl font-black text-slate-900">{incident.occupancy_percentage ?? 0}%</span>
                <span className="block text-[11px] text-slate-500">Corridor obstructed</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
                <span className="text-slate-400 block text-[10px] font-bold uppercase">Path Continuity</span>
                <span className="text-sm font-black text-slate-900 block truncate">{incident.path_continuity || 'CLEAR'}</span>
                <span className="block text-[11px] text-slate-500">{incident.path_continuity_reason || 'Accessible passage'}</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
                <span className="text-slate-400 block text-[10px] font-bold uppercase">Obstruction Impact</span>
                <span className={`text-sm font-black block ${
                  (incident.obstruction_impact || 'LOW') === 'HIGH' ? 'text-red-600' : ((incident.obstruction_impact || 'LOW') === 'MEDIUM' ? 'text-amber-600' : 'text-emerald-600')
                }`}>
                  {incident.obstruction_impact || 'LOW'}
                </span>
                <span className="block text-[11px] text-slate-500">
                  {incident.remaining_pedestrian_region_pct ? `${incident.remaining_pedestrian_region_pct}% free` : 'Clear passage'}
                </span>
              </div>
            </div>

            {incident.persistence_sec && (
              <div className="p-3 rounded-xl bg-purple-50/70 border border-purple-200 text-xs flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-purple-600" />
                  <span className="font-bold text-purple-900">
                    Temporal Persistence: {incident.persistence_sec}s
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-200 text-purple-900">
                  Tracking Prototype
                </span>
              </div>
            )}
          </div>

          {/* Explainable AI: "WHY WAS THIS FLAGGED?" (Upgrades 1 & 13) */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-600" />
                <span>Explainable AI — Why Was This Flagged?</span>
              </h2>
              <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
                {incident.probability_status || 'Potential Encroachment'}
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              EncroWatch AI applies multi-factor reasoning combining object detection, spatial overlap, corridor continuity, and historical recurrence.
            </p>

            <div className="space-y-2">
              {(incident.why_flagged || [
                { label: `${incident.primary_encroachment_type} Detected`, detail: `Classified with ${Math.round((incident.confidence || 0.85) * 100)}% model confidence.`, status: 'flagged' },
                { label: `Footpath Corridor Occupancy: ${incident.occupancy_percentage}%`, detail: 'Exceeds standard 30% obstruction threshold.', status: 'flagged' },
                { label: `Pedestrian Path Continuity: ${incident.path_continuity || 'PARTIALLY BLOCKED'}`, detail: incident.path_continuity_reason || 'Constricted walking route.', status: 'warning' }
              ]).map((chk, i) => (
                <div
                  key={i}
                  className={`p-3 rounded-xl border flex items-start gap-2.5 text-xs ${
                    chk.status === 'flagged'
                      ? 'bg-red-50/60 border-red-200 text-red-900'
                      : (chk.status === 'warning' ? 'bg-amber-50/60 border-amber-200 text-amber-900' : 'bg-emerald-50/60 border-emerald-200 text-emerald-900')
                  }`}
                >
                  <span className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 mt-0.5 font-bold text-[10px] ${
                    chk.status === 'flagged' ? 'bg-red-600 text-white' : (chk.status === 'warning' ? 'bg-amber-500 text-white' : 'bg-emerald-600 text-white')
                  }`}>
                    {chk.status === 'safe' ? '✓' : '!'}
                  </span>
                  <div>
                    <span className="font-bold block">{chk.label}</span>
                    <span className="text-[11px] opacity-80">{chk.detail}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Before & After AI Resolution Verification Section */}
          {(incident.status === 'Resolved' || incident.inspection_image_url) && (
            <BeforeAfterCompare
              beforeUrl={incident.image_url}
              afterUrl={incident.inspection_image_url}
              comparisonUrl={incident.ai_verification?.comparison_image_url}
              verificationData={incident.ai_verification}
              onRunVerification={handleRunAIVerification}
              isVerifying={isVerifying}
            />
          )}

          {/* Incident Lifecycle Timeline (Upgrade 15) */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-600" />
              <span>Incident Lifecycle Timeline</span>
            </h2>

            <div className="relative pl-6 space-y-4 border-l-2 border-slate-100 ml-2">
              {(incident.timeline || [
                { title: 'AI Encroachment Identified', description: 'Automated YOLOv5n-ONNX detection completed', actor_name: 'AI Engine', timestamp: incident.date_reported },
                { title: 'Citizen Report Submitted', description: `Report filed by ${incident.reporter_name}`, actor_name: incident.reporter_name, timestamp: incident.date_reported }
              ]).map((ev, i) => (
                <div key={i} className="relative">
                  <div className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full bg-blue-600 border-2 border-white ring-2 ring-blue-100" />
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-slate-900">{ev.title}</span>
                    <span className="text-[10px] text-slate-400 font-mono">{ev.timestamp}</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-0.5">{ev.description}</p>
                  <span className="text-[10px] font-semibold text-slate-400">Actor: {ev.actor_name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Dynamic Risk, AI Priority Queue, HITL Feedback, Actions (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Dynamic Encroachment Risk Score Card (Upgrade 5) */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <Flame className="w-4 h-4 text-red-500" />
                <span>Dynamic Encroachment Risk Score</span>
              </h2>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                (incident.risk_score || 70) >= 70 ? 'bg-red-100 text-red-700' : ((incident.risk_score || 50) >= 40 ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700')
              }`}>
                {incident.risk_level || 'HIGH'} RISK
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-500 block">Overall Risk Index</span>
                <span className="text-3xl font-extrabold text-slate-900">{incident.risk_score || 75}/100</span>
                <span className="text-xs text-slate-500 block mt-0.5">Calculated from 4 measurable factors</span>
              </div>
              <div className="w-16 h-16 rounded-full border-4 border-red-500 flex items-center justify-center bg-white shadow-xs font-black text-red-600 text-base">
                {incident.risk_score || 75}
              </div>
            </div>

            {/* Factor Points Breakdown */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-400 block text-[10px]">Object Impact</span>
                <span className="font-bold text-slate-800">
                  {incident.risk_factors?.object_impact?.points ?? 26} / 30 pts
                </span>
                <span className="text-[10px] text-slate-400 block truncate">
                  {incident.risk_factors?.object_impact?.detail || incident.primary_encroachment_type}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-400 block text-[10px]">Footpath Overlap</span>
                <span className="font-bold text-slate-800">
                  {incident.risk_factors?.footpath_overlap?.points ?? 18} / 25 pts
                </span>
                <span className="text-[10px] text-slate-400 block truncate">
                  {incident.occupancy_percentage}% corridor area
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-400 block text-[10px]">Temporal Persistence</span>
                <span className="font-bold text-slate-800">
                  {incident.risk_factors?.persistence?.points ?? 10} / 20 pts
                </span>
                <span className="text-[10px] text-slate-400 block truncate">
                  {incident.persistence_sec ? `${incident.persistence_sec}s stationary` : 'Photo capture'}
                </span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-slate-400 block text-[10px]">Accessibility Impact</span>
                <span className="font-bold text-slate-800">
                  {incident.risk_factors?.accessibility_impact?.points ?? 21} / 25 pts
                </span>
                <span className="text-[10px] text-slate-400 block truncate">
                  {incident.accessibility_score}/100 walkability
                </span>
              </div>
            </div>
          </div>

          {/* AI Recommended Action Queue & Priority (Upgrade 11) */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <Gauge className="w-4 h-4 text-blue-600" />
                <span>AI Recommended Priority Queue</span>
              </h2>
              {role === 'admin' && (
                <button
                  onClick={() => setShowPriorityModal(true)}
                  className="text-xs text-blue-600 font-bold hover:underline flex items-center gap-1"
                >
                  <Edit2 className="w-3 h-3" /> Override
                </button>
              )}
            </div>

            <div className="p-4 rounded-xl bg-blue-50/70 border border-blue-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-blue-900">Priority Score:</span>
                <span className="text-base font-extrabold text-blue-950">{incident.priority_score || 85}/100</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-blue-900">Dispatch Tier:</span>
                <span className="px-2 py-0.5 rounded-md text-xs font-bold bg-blue-600 text-white">
                  {incident.priority_rank || 'Urgent'}
                </span>
              </div>
              <div className="pt-2 border-t border-blue-200/70">
                <span className="text-[11px] text-blue-700 block font-semibold">Recommended Civic Action:</span>
                <span className="text-xs font-bold text-blue-900">{incident.priority_action || 'Immediate Dispatch — Field Officer Intervention'}</span>
              </div>
            </div>
          </div>

          {/* Human-in-the-Loop AI Feedback Controls (Batch 3 Upgrades) */}
          {(role === 'admin' || role === 'officer') && (
            <div className="bg-white rounded-2xl p-6 border border-purple-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-purple-600" />
                  <span>Human-in-the-Loop AI Verification</span>
                </h2>
                <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${
                  incident.human_verification_status === 'CONFIRMED'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : incident.human_verification_status === 'REJECTED'
                    ? 'bg-red-50 text-red-700 border-red-200'
                    : incident.human_verification_status === 'MODIFIED'
                    ? 'bg-amber-50 text-amber-700 border-amber-200'
                    : 'bg-purple-50 text-purple-700 border-purple-200'
                }`}>
                  {incident.human_verification_status || 'PENDING REVIEW'}
                </span>
              </div>

              {/* Toast feedback message */}
              {reviewFeedbackMsg && (
                <div className={`p-3 rounded-xl text-xs font-semibold border ${
                  reviewFeedbackMsg.type === 'success'
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                    : 'bg-red-50 text-red-800 border-red-200'
                }`}>
                  {reviewFeedbackMsg.text}
                </div>
              )}

              {/* Verified Decision Display vs Pending Decision Controls */}
              {incident.human_verification_status && incident.human_verification_status !== 'PENDING_REVIEW' && !isEditingVerification ? (
                <div className="p-4 rounded-xl bg-purple-50/50 border border-purple-100 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-purple-950">Official Human Review Recorded</span>
                    <button
                      onClick={() => setIsEditingVerification(true)}
                      className="text-xs text-purple-700 hover:text-purple-900 font-bold underline"
                    >
                      Revise Finding
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2.5 bg-white rounded-lg border border-purple-100">
                      <span className="text-[10px] font-bold text-slate-400 block uppercase">Original AI Detection</span>
                      <span className="font-semibold text-slate-700">
                        {incident.original_ai_category || incident.primary_encroachment_type}
                      </span>
                      <span className="text-[10px] text-slate-400 block">
                        Conf: {incident.confidence ? `${Math.round(incident.confidence * 100)}%` : 'N/A'}
                      </span>
                    </div>

                    <div className="p-2.5 bg-white rounded-lg border border-purple-100">
                      <span className="text-[10px] font-bold text-slate-400 block uppercase">Human Verified Finding</span>
                      <span className="font-bold text-purple-700">
                        {incident.human_verified_category || incident.primary_encroachment_type}
                      </span>
                      <span className="text-[10px] text-emerald-700 font-semibold block">
                        Status: {incident.human_verification_status}
                      </span>
                    </div>
                  </div>

                  {incident.human_review_reason && (
                    <div className="text-xs bg-white p-2.5 rounded-lg border border-purple-100">
                      <span className="text-[10px] font-bold text-slate-400 block uppercase mb-0.5">Reviewer Justification:</span>
                      <p className="text-slate-700 font-medium italic">"{incident.human_review_reason}"</p>
                    </div>
                  )}

                  <div className="text-[11px] text-slate-500 pt-1 flex items-center justify-between">
                    <span>Reviewer: <strong>{incident.reviewed_by_name || 'Officer'}</strong></span>
                    <span>Date: {incident.reviewed_at ? new Date(incident.reviewed_at).toLocaleDateString() : 'Recorded'}</span>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-xs text-slate-500">
                    Review the AI detection label <strong>"{incident.original_ai_category || incident.primary_encroachment_type}"</strong> to confirm or correct for municipal vision dataset:
                  </p>

                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => handleFeedbackAction('CONFIRM', null, 'Confirmed by officer')}
                      disabled={submittingFeedback}
                      className="p-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-colors shadow-xs disabled:opacity-50"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Confirm AI Finding</span>
                    </button>

                    <button
                      onClick={() => setShowModifyModal(true)}
                      disabled={submittingFeedback}
                      className="p-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-colors shadow-xs disabled:opacity-50"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                      <span>Modify Category</span>
                    </button>

                    <button
                      onClick={() => {
                        setRejectReason('');
                        setShowRejectModal(true);
                      }}
                      disabled={submittingFeedback}
                      className="p-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-colors shadow-xs disabled:opacity-50"
                    >
                      <X className="w-3.5 h-3.5" />
                      <span>Reject (False Pos)</span>
                    </button>

                    <button
                      onClick={() => {
                        setEvidenceRequestReason('');
                        setShowEvidenceRequestModal(true);
                      }}
                      disabled={submittingFeedback}
                      className="p-2.5 rounded-xl bg-slate-600 hover:bg-slate-700 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-colors shadow-xs disabled:opacity-50"
                    >
                      <HelpCircle className="w-3.5 h-3.5" />
                      <span>Request Evidence</span>
                    </button>
                  </div>

                  {isEditingVerification && (
                    <div className="flex justify-end pt-1">
                      <button
                        onClick={() => setIsEditingVerification(false)}
                        className="text-xs text-slate-500 hover:text-slate-800 font-semibold"
                      >
                        Cancel Revision
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Batch 2: Duplicate Incident Intelligence Card */}
          {possibleDuplicates?.candidates?.length > 0 && !incident.duplicate_dismissed && !incident.is_duplicate_merged && (
            <div className="bg-purple-50/60 rounded-2xl p-6 border border-purple-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-purple-950 flex items-center gap-1.5">
                  <Layers className="w-4 h-4 text-purple-600" />
                  <span>Duplicate Incident Intelligence</span>
                </h2>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-200 text-purple-900">
                  {possibleDuplicates.candidates.length} Match{possibleDuplicates.candidates.length > 1 ? 'es' : ''} Found
                </span>
              </div>

              <p className="text-xs text-purple-900/80 leading-relaxed">
                Spatial, temporal, and category correlation identified potential duplicate submissions for this obstruction.
              </p>

              <div className="space-y-3">
                {possibleDuplicates.candidates.slice(0, 2).map((cand) => (
                  <div key={cand.id} className="p-3 bg-white rounded-xl border border-purple-200 text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-slate-800">{cand.incident_number}</span>
                      <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 font-bold text-[10px]">
                        Match Score: {cand.similarity_score}%
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <img
                        src={cand.image_url}
                        alt=""
                        className="w-12 h-10 object-cover rounded-md border border-slate-200 shrink-0"
                      />
                      <div className="space-y-0.5 min-w-0">
                        <span className="font-bold text-slate-800 block truncate">{cand.title}</span>
                        <span className="text-[10px] text-slate-500 block truncate">
                          {cand.distance_meters !== null ? `${cand.distance_meters}m away` : 'Address match'} • {cand.time_diff_hours !== null ? `${cand.time_diff_hours}h apart` : ''}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center justify-end gap-2 pt-1 border-t border-slate-100">
                      <button
                        onClick={() => {
                          setSelectedDuplicate(cand);
                          setShowDuplicateModal(true);
                        }}
                        className="px-2.5 py-1 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-bold text-[10px] transition-colors"
                      >
                        Compare &amp; Merge
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-between pt-1">
                <span className="text-[10px] text-purple-700/80 italic">
                  * Similarity is an explainable heuristic, not a probability.
                </span>
                <button
                  onClick={handleKeepSeparate}
                  className="text-xs text-purple-700 hover:text-purple-900 font-bold underline"
                >
                  Keep All Separate
                </button>
              </div>
            </div>
          )}

          {/* Batch 2: Historical Reoccurrence Risk Forecast Card */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4 text-indigo-600" />
                <span>Historical Reoccurrence Forecast (14-Day)</span>
              </h2>
              {riskForecast?.has_sufficient_data ? (
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                  riskForecast.forecast_risk_level === 'HIGH' || riskForecast.forecast_risk_level === 'VERY_HIGH'
                    ? 'bg-red-100 text-red-700'
                    : (riskForecast.forecast_risk_level === 'MODERATE' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700')
                }`}>
                  {riskForecast.forecast_risk_level} RECURRENCE
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-600">
                  Data Collecting
                </span>
              )}
            </div>

            {riskForecast?.has_sufficient_data ? (
              <div className="space-y-3">
                <div className="p-3.5 rounded-xl bg-indigo-50/60 border border-indigo-100 flex items-center justify-between">
                  <div>
                    <span className="text-[11px] text-indigo-800 font-semibold block">Forecast Horizon</span>
                    <span className="text-sm font-extrabold text-indigo-950">{riskForecast.forecast_period}</span>
                    <span className="text-[10px] text-indigo-700 block mt-0.5">
                      Based on {riskForecast.cluster_size} historical incidents in 150m radius
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-[11px] text-indigo-800 font-semibold block">Recurrence Index</span>
                    <span className="text-2xl font-black text-indigo-950">{riskForecast.forecast_score}/100</span>
                  </div>
                </div>

                {/* 4 Factor Breakdown */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="text-slate-400 block text-[10px]">Cluster Density</span>
                    <span className="font-bold text-slate-800">
                      {riskForecast.contributing_factors?.cluster_density?.points ?? 0} / 30 pts
                    </span>
                    <span className="text-[10px] text-slate-400 block truncate">
                      {riskForecast.cluster_size} reports in sector
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="text-slate-400 block text-[10px]">High Severity Prop.</span>
                    <span className="font-bold text-slate-800">
                      {riskForecast.contributing_factors?.high_severity_proportion?.points ?? 0} / 25 pts
                    </span>
                    <span className="text-[10px] text-slate-400 block truncate">
                      {riskForecast.high_severity_count} high severity
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="text-slate-400 block text-[10px]">Temporal Cluster</span>
                    <span className="font-bold text-slate-800">
                      {riskForecast.contributing_factors?.temporal_concentration?.points ?? 0} / 25 pts
                    </span>
                    <span className="text-[10px] text-slate-400 block truncate">
                      Window: {riskForecast.peak_recurrence_window || 'General'}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="text-slate-400 block text-[10px]">Resolution Lag</span>
                    <span className="font-bold text-slate-800">
                      {riskForecast.contributing_factors?.resolution_lag?.points ?? 0} / 20 pts
                    </span>
                    <span className="text-[10px] text-slate-400 block truncate">
                      {riskForecast.historical_resolution_rate_pct}% resolved
                    </span>
                  </div>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-[11px] space-y-1">
                  <div className="flex items-center justify-between text-slate-600">
                    <span className="font-medium">Baseline Benchmark:</span>
                    <span className="font-bold text-slate-800">{riskForecast.baseline_comparison || 'Ward Average'}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-600">
                    <span className="font-medium">Peak Risk Window:</span>
                    <span className="font-bold text-slate-800">{riskForecast.peak_recurrence_window || 'Weekday Mornings'}</span>
                  </div>
                </div>

                <p className="text-[10px] text-slate-400 italic leading-tight">
                  * Note: {riskForecast.limitations || 'Forecast is an estimate based on spatial patterns; external enforcement or physical changes will alter recurrence.'}
                </p>
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-600 space-y-1.5">
                <span className="font-bold block text-slate-800">Data Sufficiency Notice</span>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  {riskForecast?.reason || 'Insufficient historical incident records (minimum 3 records required in 150m spatial cluster) to generate calibrated statistical forecast. Civic data collection in progress.'}
                </p>
              </div>
            )}
          </div>

          {/* Workflow & Status Management */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-slate-900">Incident Dispatch & SLA Lifecycle</h2>

            {/* SLA Status Widget */}
            {incident.sla_status && (
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-600 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-indigo-600" /> SLA Target Status
                  </span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    incident.sla_status.overall_status === 'COMPLETED'
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : incident.sla_status.overall_status === 'OVERDUE'
                      ? 'bg-red-50 text-red-700 border border-red-200'
                      : incident.sla_status.overall_status === 'APPROACHING_DEADLINE'
                      ? 'bg-amber-50 text-amber-700 border border-amber-200'
                      : 'bg-blue-50 text-blue-700 border border-blue-200'
                  }`}>
                    {incident.sla_status.overall_status}
                  </span>
                </div>
                {incident.sla_status.resolution_milestone && (
                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                    <span>Resolution Deadline:</span>
                    <span className="font-mono font-bold text-slate-700">
                      {incident.sla_status.resolution_milestone.time_remaining_minutes !== null
                        ? `${Math.max(0, Math.round(incident.sla_status.resolution_milestone.time_remaining_minutes / 60))}h remaining`
                        : 'Completed'}
                    </span>
                  </div>
                )}
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700">Update Incident Status</label>
              <select
                value={incident.status}
                onChange={(e) => handleStatusChange(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 text-xs p-2.5 rounded-xl font-medium focus:outline-none"
              >
                <option value="Pending">Pending</option>
                <option value="Under Review">Under Review</option>
                <option value="Verified">Verified</option>
                <option value="Assigned">Assigned</option>
                <option value="In Progress">In Progress</option>
                <option value="Under Investigation">Under Investigation</option>
                <option value="Awaiting Evidence">Awaiting Evidence</option>
                <option value="Resolved - Pending Verification">Resolved - Pending Verification</option>
                <option value="Resolved - Verified">Resolved - Verified</option>
                <option value="Resolved">Resolved</option>
                <option value="Reopened">Reopened</option>
                <option value="Rejected">Rejected</option>
                <option value="Closed">Closed</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700">Assigned Field Officer</label>
              <select
                value={incident.assigned_officer_id || ''}
                onChange={(e) => handleAssignOfficer(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 text-xs p-2.5 rounded-xl font-medium focus:outline-none"
              >
                <option value="">Unassigned</option>
                {officers.map((off) => (
                  <option key={off.id} value={off.id}>
                    {off.full_name} ({off.badge_id || 'Officer'}) — {off.assigned_area || 'Ward'}
                  </option>
                ))}
              </select>
            </div>

            {/* Batch 5.5 Action Buttons */}
            <div className="space-y-2 pt-2 border-t border-slate-100">
              {['In Progress', 'Under Investigation', 'Assigned'].includes(incident.status) && (
                <button
                  onClick={() => setShowResolutionSubmitModal(true)}
                  className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-xs transition-colors"
                >
                  <FileCheck className="w-4 h-4" />
                  <span>Submit Clearance Resolution</span>
                </button>
              )}

              {incident.status === 'Resolved - Pending Verification' && role === 'admin' && (
                <button
                  onClick={() => setShowResolutionReviewModal(true)}
                  className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-xs transition-colors"
                >
                  <ShieldCheck className="w-4 h-4" />
                  <span>Supervisory Verification Review</span>
                </button>
              )}

              {['Resolved - Verified', 'Resolved', 'Closed'].includes(incident.status) && role === 'admin' && (
                <button
                  onClick={() => setShowReopenModal(true)}
                  className="w-full py-2.5 px-4 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-xs transition-colors"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>Reopen Incident Case</span>
                </button>
              )}

              {incident.inspection_image_url && incident.status !== 'Resolved' && (
                <button
                  onClick={handleRunAIVerification}
                  disabled={isVerifying}
                  className="w-full py-2.5 px-4 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition-colors"
                >
                  <Sparkles className="w-4 h-4" />
                  {isVerifying ? 'Running AI Verification...' : 'Execute Before/After AI Verification'}
                </button>
              )}
            </div>

            {/* Citizen Comments & Updates */}
            {incident.citizen_comments && incident.citizen_comments.length > 0 && (
              <div className="pt-3 border-t border-slate-100 space-y-2">
                <h3 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                  <MessageSquare className="w-3.5 h-3.5 text-blue-600" />
                  <span>Citizen Updates ({incident.citizen_comments.length})</span>
                </h3>
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {incident.citizen_comments.map((c, i) => (
                    <div key={i} className="p-2 bg-slate-50 rounded-lg text-[11px] text-slate-600">
                      <div className="flex justify-between font-bold text-slate-800">
                        <span>{c.author_name || 'Reporting Citizen'}</span>
                        <span className="text-[10px] text-slate-400 font-normal">
                          {new Date(c.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <p className="mt-0.5 text-slate-600">{c.comment}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* HITL Modify Category Modal */}
      {showModifyModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-slate-900">Modify AI Encroachment Category</h3>
            <p className="text-xs text-slate-500">
              Select the correct urban category to store in the <code>ai_feedback_dataset</code> for model fine-tuning:
            </p>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Corrected Category</label>
              <select
                value={modCategory}
                onChange={(e) => setModCategory(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-slate-200 text-xs bg-slate-50 font-semibold"
              >
                <option value="Vehicle">Vehicle (Car / Two-Wheeler / Truck)</option>
                <option value="Street Vendor">Street Vendor / Hawkers Stall</option>
                <option value="Construction Material">Construction Material / Debris</option>
                <option value="Shop Extension">Permanent Shop Extension</option>
                <option value="Signboard">Commercial Signboard / A-Frame</option>
                <option value="Street Object">Other Street Object / Furniture</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Officer Justification / Notes</label>
              <textarea
                value={modNotes}
                onChange={(e) => setModNotes(e.target.value)}
                placeholder="Explain the physical characteristics observed during inspection..."
                className="w-full p-2.5 rounded-xl border border-slate-200 text-xs h-20"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowModifyModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                onClick={() => handleFeedbackAction('MODIFY', modCategory, modNotes)}
                disabled={submittingFeedback}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-amber-600 hover:bg-amber-700 text-white"
              >
                {submittingFeedback ? 'Saving Correction...' : 'Submit Human Correction'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* HITL Reject Modal (Mandatory Reason Required) */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <XCircle className="w-5 h-5 text-red-600" />
                <span>Reject AI Finding (False Positive)</span>
              </h3>
              <button onClick={() => setShowRejectModal(false)} className="text-slate-400 hover:text-slate-600 font-bold">
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              You are rejecting the AI classification of <strong>"{incident.original_ai_category || incident.primary_encroachment_type}"</strong>. A clear justification is mandatory for municipal audit and model fine-tuning.
            </p>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Reason for Rejection <span className="text-red-500">* (Mandatory)</span>
              </label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="E.g., Legitimate municipal utility box, authorized outdoor dining permit, or temporary delivery stop..."
                className="w-full p-2.5 rounded-xl border border-slate-200 text-xs h-24 focus:outline-none focus:border-red-500 bg-slate-50"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowRejectModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                onClick={() => handleFeedbackAction('REJECT', null, rejectReason)}
                disabled={submittingFeedback || !rejectReason.trim()}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white shadow-xs"
              >
                {submittingFeedback ? 'Rejecting Finding...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* HITL Request More Evidence Modal */}
      {showEvidenceRequestModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <HelpCircle className="w-5 h-5 text-slate-600" />
                <span>Request Additional Visual Evidence</span>
              </h3>
              <button onClick={() => setShowEvidenceRequestModal(false)} className="text-slate-400 hover:text-slate-600 font-bold">
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Flag this case as needing additional photo perspectives or clearer angles before an official determination can be made.
            </p>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Requested Evidence Details
              </label>
              <textarea
                value={evidenceRequestReason}
                onChange={(e) => setEvidenceRequestReason(e.target.value)}
                placeholder="E.g., Low lighting occludes curb; need close-up of shop boundary or side angle showing corridor clearance..."
                className="w-full p-2.5 rounded-xl border border-slate-200 text-xs h-24 focus:outline-none focus:border-slate-500 bg-slate-50"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowEvidenceRequestModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                onClick={() => handleFeedbackAction('NEEDS_MORE_EVIDENCE', null, evidenceRequestReason || 'Additional visual angles requested')}
                disabled={submittingFeedback}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-900 text-white shadow-xs"
              >
                {submittingFeedback ? 'Submitting...' : 'Submit Evidence Request'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Priority Override Modal */}
      {showPriorityModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-slate-900">Administrator Priority Override</h3>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Priority Score (1 - 100): {newPriorityScore}</label>
              <input
                type="range"
                min="1"
                max="100"
                value={newPriorityScore}
                onChange={(e) => setNewPriorityScore(Number(e.target.value))}
                className="w-full"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Priority Rank</label>
              <select
                value={newPriorityRank}
                onChange={(e) => setNewPriorityRank(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-slate-200 text-xs bg-slate-50 font-semibold"
              >
                <option value="Critical">Critical</option>
                <option value="Urgent">Urgent</option>
                <option value="Standard">Standard</option>
                <option value="Routine">Routine</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Recommended Action</label>
              <input
                type="text"
                value={newPriorityAction}
                onChange={(e) => setNewPriorityAction(e.target.value)}
                className="w-full p-2 rounded-xl border border-slate-200 text-xs"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowPriorityModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                onClick={handleOverridePriority}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white"
              >
                Save Priority Override
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Batch 2: Duplicate Comparison & Merge Modal */}
      {showDuplicateModal && selectedDuplicate && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-2xl w-full shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                  <Layers className="w-5 h-5 text-purple-600" />
                  <span>Duplicate Incident Comparison</span>
                </h3>
                <span className="text-xs text-slate-500">
                  Compare primary incident with suspected duplicate candidate
                </span>
              </div>
              <button
                onClick={() => setShowDuplicateModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Heuristic Score Banner */}
            <div className="p-3 bg-purple-50 rounded-xl border border-purple-200 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-purple-950 block">Multi-Factor Match Score: {selectedDuplicate.similarity_score}%</span>
                <span className="text-[10px] text-purple-800">
                  * Explainable heuristic combining spatial distance, temporal window, category alignment, and HSV visual correlation.
                </span>
              </div>
              <span className="px-2.5 py-1 rounded-lg bg-purple-600 text-white font-black text-xs">
                {selectedDuplicate.similarity_score >= 80 ? 'HIGH MATCH' : 'MODERATE MATCH'}
              </span>
            </div>

            {/* Side-by-Side Comparison Grid */}
            <div className="grid grid-cols-2 gap-4">
              {/* Primary Incident */}
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                  Current Master Incident
                </span>
                <img
                  src={incident.image_url}
                  alt=""
                  className="w-full h-36 object-cover rounded-lg border border-slate-200"
                />
                <div className="space-y-1 text-xs">
                  <span className="font-mono font-bold text-slate-900 block">{incident.incident_number}</span>
                  <span className="font-medium text-slate-700 block truncate">{incident.title}</span>
                  <div className="flex items-center gap-1.5 text-slate-500 text-[11px]">
                    <MapPin className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">{incident.location_name}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-500 text-[11px]">
                    <Calendar className="w-3.5 h-3.5 shrink-0" />
                    <span>{incident.date_reported}</span>
                  </div>
                  <div className="pt-1">
                    <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-bold text-[10px]">
                      {incident.primary_encroachment_type}
                    </span>
                  </div>
                </div>
              </div>

              {/* Duplicate Candidate */}
              <div className="p-4 rounded-xl border border-purple-200 bg-purple-50/30 space-y-3">
                <span className="text-[11px] font-bold uppercase tracking-wider text-purple-600 block">
                  Suspected Duplicate Candidate
                </span>
                <img
                  src={selectedDuplicate.image_url}
                  alt=""
                  className="w-full h-36 object-cover rounded-lg border border-purple-200"
                />
                <div className="space-y-1 text-xs">
                  <span className="font-mono font-bold text-slate-900 block">{selectedDuplicate.incident_number}</span>
                  <span className="font-medium text-slate-700 block truncate">{selectedDuplicate.title}</span>
                  <div className="flex items-center gap-1.5 text-slate-500 text-[11px]">
                    <MapPin className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">{selectedDuplicate.location_name}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-500 text-[11px]">
                    <Calendar className="w-3.5 h-3.5 shrink-0" />
                    <span>{selectedDuplicate.date_reported}</span>
                  </div>
                  <div className="pt-1">
                    <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 font-bold text-[10px]">
                      {selectedDuplicate.primary_encroachment_type}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Matching Criteria Breakdown */}
            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs">
              <span className="font-bold text-slate-800 block">Correlation Factor Evidence:</span>
              <ul className="space-y-1 text-slate-600 text-[11px]">
                {(selectedDuplicate.reasons || [
                  selectedDuplicate.distance_meters !== null ? `Spatial distance: ${selectedDuplicate.distance_meters} meters` : 'Address textual similarity match',
                  selectedDuplicate.time_diff_hours !== null ? `Temporal difference: ${selectedDuplicate.time_diff_hours} hours` : 'Recorded within matching window',
                  selectedDuplicate.category_match ? `Matching obstruction category: ${selectedDuplicate.primary_encroachment_type}` : 'Related encroachment category',
                  selectedDuplicate.visual_similarity !== null ? `Visual HSV histogram similarity: ${Math.round(selectedDuplicate.visual_similarity * 100)}%` : 'Visual correlation analyzed'
                ]).map((r, i) => (
                  <li key={i} className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-600" />
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <button
                onClick={handleKeepSeparate}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 border border-slate-200"
              >
                Keep Separate (Independent Case)
              </button>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowDuplicateModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-500 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleMergeDuplicate(selectedDuplicate.id)}
                  disabled={mergingDuplicate}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-purple-600 hover:bg-purple-700 text-white shadow-sm flex items-center gap-1.5"
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span>{mergingDuplicate ? 'Merging Records...' : 'Confirm & Merge Records'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Batch 2: Attach Evidence Modal */}
      {showAddEvidenceModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                <Camera className="w-5 h-5 text-emerald-600" />
                <span>Attach Multi-Image Evidence</span>
              </h3>
              <button
                onClick={() => setShowAddEvidenceModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Upload an additional perspective or supporting photograph. The AI will perform separate YOLOv5n-ONNX object detection, corridor segmentation, and cross-perspective consistency verification.
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Perspective / Caption</label>
                <select
                  value={evidenceCaption}
                  onChange={(e) => setEvidenceCaption(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-200 text-xs bg-slate-50 font-semibold"
                >
                  <option value="Secondary Perspective">Secondary Perspective</option>
                  <option value="Opposite Angle View">Opposite Angle View</option>
                  <option value="Close-up Obstruction">Close-up Obstruction</option>
                  <option value="Pedestrian Corridor Clearance">Pedestrian Corridor Clearance</option>
                  <option value="Supporting Evidence">Supporting Evidence</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Select Photograph</label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setEvidenceFile(e.target.files[0]);
                    }
                  }}
                  className="w-full text-xs text-slate-600 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100"
                />
              </div>

              {evidenceFile && (
                <div className="p-2 border border-slate-200 rounded-xl bg-slate-50">
                  <span className="text-[10px] text-slate-500 block mb-1">Selected: {evidenceFile.name} ({(evidenceFile.size / 1024).toFixed(1)} KB)</span>
                  <img
                    src={URL.createObjectURL(evidenceFile)}
                    alt="Preview"
                    className="w-full h-32 object-cover rounded-lg"
                  />
                </div>
              )}
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => {
                  setShowAddEvidenceModal(false);
                  setEvidenceFile(null);
                }}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                onClick={handleAddEvidence}
                disabled={uploadingEvidence || !evidenceFile}
                className="px-5 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white shadow-sm flex items-center gap-1.5"
              >
                <Camera className="w-3.5 h-3.5" />
                <span>{uploadingEvidence ? 'Analyzing Perspective...' : 'Attach & Run AI Inference'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Batch 5.5: Submit Resolution Modal */}
      {showResolutionSubmitModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl p-6 max-w-lg w-full shadow-2xl space-y-4 animate-scale-in">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <FileCheck className="w-5 h-5 text-emerald-600" />
                <span>Submit Field Clearance Resolution</span>
              </h3>
              <button
                onClick={() => setShowResolutionSubmitModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-600">
              Document on-site municipal enforcement and upload photographic evidence verifying complete footpath clearance.
            </p>

            <form onSubmit={handleSubmitResolution} className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Resolution Notes <span className="text-red-500">*</span>
                </label>
                <textarea
                  rows={3}
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  placeholder="Detail physical removal, vendor relocation, barricade dismantling, or civil works conducted..."
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-emerald-500 font-medium"
                  required
                />
                <span className="text-[10px] text-slate-400">Minimum 10 characters required.</span>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  After-Clearance Verification Photo <span className="text-red-500">*</span>
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      setResolutionAfterFile(e.target.files[0]);
                    }
                  }}
                  className="w-full text-xs text-slate-600 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100"
                  required
                />
              </div>

              {resolutionAfterFile && (
                <div className="p-2 border border-emerald-200 rounded-xl bg-emerald-50/50">
                  <span className="text-[10px] text-emerald-800 font-bold block mb-1">Preview After-Clearance Photo:</span>
                  <img
                    src={URL.createObjectURL(resolutionAfterFile)}
                    alt="After preview"
                    className="w-full h-36 object-cover rounded-lg border border-emerald-300"
                  />
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowResolutionSubmitModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingResolution}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white shadow-sm flex items-center gap-1.5"
                >
                  <FileCheck className="w-4 h-4" />
                  <span>{submittingResolution ? 'Submitting Resolution...' : 'Submit Resolution'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Batch 5.5: Supervisory Review Modal */}
      {showResolutionReviewModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl p-6 max-w-lg w-full shadow-2xl space-y-4 animate-scale-in">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-indigo-600" />
                <span>Supervisory Resolution Review</span>
              </h3>
              <button
                onClick={() => setShowResolutionReviewModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              <div className="p-3 bg-slate-50 rounded-xl text-xs space-y-1">
                <span className="font-bold text-slate-800 block">Submitted Resolution Notes:</span>
                <p className="text-slate-600">{incident.resolution_notes || 'No notes attached.'}</p>
              </div>

              {incident.after_images && incident.after_images.length > 0 && (
                <div>
                  <span className="text-xs font-bold text-slate-700 block mb-1">Clearance Photo Evidence:</span>
                  <img
                    src={incident.after_images[0]}
                    alt="Clearance Evidence"
                    className="w-full h-40 object-cover rounded-xl border border-slate-200"
                  />
                </div>
              )}

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Review Decision</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setResolutionReviewDecision('ACCEPT')}
                    className={`py-2 px-3 rounded-xl text-xs font-bold border transition-colors flex items-center justify-center gap-1.5 ${
                      resolutionReviewDecision === 'ACCEPT'
                        ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs'
                        : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Accept &amp; Verify</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setResolutionReviewDecision('REJECT')}
                    className={`py-2 px-3 rounded-xl text-xs font-bold border transition-colors flex items-center justify-center gap-1.5 ${
                      resolutionReviewDecision === 'REJECT'
                        ? 'bg-red-600 text-white border-red-600 shadow-xs'
                        : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <X className="w-4 h-4" />
                    <span>Reject Resolution</span>
                  </button>
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Supervisory Notes {resolutionReviewDecision === 'REJECT' && <span className="text-red-500">* (Mandatory for rejection)</span>}
                </label>
                <textarea
                  rows={2}
                  value={resolutionReviewNotes}
                  onChange={(e) => setResolutionReviewNotes(e.target.value)}
                  placeholder={
                    resolutionReviewDecision === 'REJECT'
                      ? 'Specify why clearance was deemed insufficient (e.g., debris still on corridor, partial sidewalk obstruction remains)...'
                      : 'Optional verification comments...'
                  }
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowResolutionReviewModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleReviewResolution(resolutionReviewDecision)}
                disabled={submittingReview}
                className={`px-5 py-2 rounded-xl text-xs font-bold text-white shadow-sm flex items-center gap-1.5 disabled:opacity-50 ${
                  resolutionReviewDecision === 'ACCEPT' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-red-600 hover:bg-red-700'
                }`}
              >
                <ShieldCheck className="w-4 h-4" />
                <span>{submittingReview ? 'Processing...' : resolutionReviewDecision === 'ACCEPT' ? 'Confirm Verification' : 'Confirm Rejection'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Batch 5.5: Reopen Incident Modal */}
      {showReopenModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4 animate-scale-in">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <RotateCcw className="w-5 h-5 text-purple-600" />
                <span>Reopen Incident Case</span>
              </h3>
              <button
                onClick={() => setShowReopenModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-600">
              Reopening a case returns it to active municipal investigation and recalculates live SLA milestones. A documented justification is required.
            </p>

            <form onSubmit={handleReopenIncident} className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Reopening Justification <span className="text-red-500">*</span>
                </label>
                <textarea
                  rows={3}
                  value={reopenReasonText}
                  onChange={(e) => setReopenReasonText(e.target.value)}
                  placeholder="Document recurrence, citizen appeal, or incomplete municipal clearance..."
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none focus:border-purple-500 font-medium"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowReopenModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingReopen}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white shadow-sm flex items-center gap-1.5"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>{submittingReopen ? 'Reopening...' : 'Confirm Reopen'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
