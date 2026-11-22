import React, { useState, useEffect } from 'react';
import {
  FileText,
  Clock,
  MapPin,
  CheckCircle2,
  ChevronRight,
  AlertTriangle,
  Upload,
  MessageSquare,
  Star,
  Send,
  Eye,
  Shield,
  Layers,
  Sparkles,
  Camera,
  RefreshCw,
  X,
  Info
} from 'lucide-react';
import { StatusBadge, SeverityBadge } from '../../components/StatusBadge';
import { incidentsAPI, serviceFeedbackAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';

export default function MyReports({ onSelectIncident, onNewReport }) {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState(null);
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Supplementary Comment & Evidence State
  const [commentText, setCommentText] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);
  const [evidenceFile, setEvidenceFile] = useState(null);
  const [evidenceCaption, setEvidenceCaption] = useState('Citizen Supplementary Evidence');
  const [uploadingEvidence, setUploadingEvidence] = useState(false);

  // Service Feedback State
  const [feedbackRating, setFeedbackRating] = useState(5);
  const [timelinessRating, setTimelinessRating] = useState(5);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [existingFeedback, setExistingFeedback] = useState(null);
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const res = await incidentsAPI.list({ my_reports: true, limit: 50 });
      setReports(res.data || []);
    } catch (err) {
      console.error('Failed to fetch citizen reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleOpenDetail = async (report) => {
    try {
      const res = await incidentsAPI.getById(report.id || report._id);
      setSelectedReport(res.data);
      // Fetch feedback if resolved
      if (['Resolved - Verified', 'Resolved', 'Closed'].includes(res.data.status)) {
        try {
          const fbRes = await serviceFeedbackAPI.get(res.data.id);
          if (fbRes.data?.feedback) {
            setExistingFeedback(fbRes.data.feedback);
            setFeedbackRating(fbRes.data.feedback.satisfaction_rating || 5);
            setTimelinessRating(fbRes.data.feedback.timeliness_rating || 5);
            setFeedbackComment(fbRes.data.feedback.feedback_text || '');
          } else {
            setExistingFeedback(null);
          }
        } catch (e) {
          setExistingFeedback(null);
        }
      } else {
        setExistingFeedback(null);
      }
    } catch (err) {
      console.error('Failed to load incident detail:', err);
      setSelectedReport(report);
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!commentText.trim() || !selectedReport) return;
    try {
      setSubmittingComment(true);
      await incidentsAPI.addCitizenComment(selectedReport.id, { comment: commentText.trim() });
      setCommentText('');
      // Refresh report
      const res = await incidentsAPI.getById(selectedReport.id);
      setSelectedReport(res.data);
      fetchReports();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to submit comment.');
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleUploadEvidence = async (e) => {
    e.preventDefault();
    if (!evidenceFile || !selectedReport) return;
    try {
      setUploadingEvidence(true);
      const formData = new FormData();
      formData.append('file', evidenceFile);
      await incidentsAPI.addEvidence(selectedReport.id, formData, evidenceCaption);
      setEvidenceFile(null);
      // Refresh report
      const res = await incidentsAPI.getById(selectedReport.id);
      setSelectedReport(res.data);
      fetchReports();
      alert('Supplementary evidence successfully added to your report.');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to upload evidence.');
    } finally {
      setUploadingEvidence(false);
    }
  };

  const handleSubmitFeedback = async (e) => {
    e.preventDefault();
    if (!selectedReport) return;
    try {
      setSubmittingFeedback(true);
      const res = await serviceFeedbackAPI.submit(selectedReport.id, {
        satisfaction_rating: feedbackRating,
        timeliness_rating: timelinessRating,
        feedback_text: feedbackComment.trim() || undefined,
      });
      setExistingFeedback(res.data?.feedback);
      setFeedbackSuccess(true);
      setTimeout(() => setFeedbackSuccess(false), 4000);
      fetchReports();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to submit feedback.');
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const filteredReports = reports.filter((r) => {
    if (statusFilter === 'ALL') return true;
    if (statusFilter === 'ACTIVE') return !['Resolved - Verified', 'Resolved', 'Closed'].includes(r.status);
    if (statusFilter === 'RESOLVED') return ['Resolved - Verified', 'Resolved', 'Closed'].includes(r.status);
    if (statusFilter === 'ACTION_NEEDED') return r.status === 'Awaiting Evidence' || r.status === 'Reopened';
    return true;
  });

  // Calculate milestone stages
  const getMilestoneIndex = (status) => {
    switch (status) {
      case 'Submitted':
      case 'Pending':
        return 0;
      case 'AI Review':
      case 'Under Review':
        return 1;
      case 'Assigned':
        return 2;
      case 'In Progress':
      case 'Under Investigation':
      case 'Awaiting Evidence':
        return 3;
      case 'Resolved - Pending Verification':
        return 4;
      case 'Resolved - Verified':
      case 'Resolved':
      case 'Closed':
        return 5;
      case 'Reopened':
        return 2;
      default:
        return 1;
    }
  };

  const milestones = [
    { label: 'Reported', desc: 'Incident received' },
    { label: 'Triage / AI Review', desc: 'Footpath impact analyzed' },
    { label: 'Officer Assigned', desc: 'Dispatched to local ward' },
    { label: 'In Progress', desc: 'On-site investigation' },
    { label: 'Clearance Submitted', desc: 'Awaiting supervisor signoff' },
    { label: 'Resolved & Verified', desc: 'Clearance verified' },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-20">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <CheckCircle2 className="w-6 h-6 text-blue-600" />
            {t('myReports') || 'My Reported Encroachments'}
          </h1>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            Track real-time municipal inspection, officer clearance, and submit service satisfaction feedback
          </p>
        </div>
        <button
          onClick={onNewReport}
          className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm flex items-center justify-center gap-1.5 self-start sm:self-auto"
        >
          <span>+</span>
          <span>{t('reportEncroachment') || 'Report Encroachment'}</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs font-semibold">
        {[
          { id: 'ALL', label: `All Reports (${reports.length})` },
          { id: 'ACTIVE', label: `Active (${reports.filter(r => !['Resolved - Verified', 'Resolved', 'Closed'].includes(r.status)).length})` },
          { id: 'ACTION_NEEDED', label: `Awaiting Action (${reports.filter(r => ['Awaiting Evidence', 'Reopened'].includes(r.status)).length})` },
          { id: 'RESOLVED', label: `Resolved (${reports.filter(r => ['Resolved - Verified', 'Resolved', 'Closed'].includes(r.status)).length})` },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setStatusFilter(tab.id)}
            className={`px-3.5 py-1.5 rounded-xl border transition-colors whitespace-nowrap ${
              statusFilter === tab.id
                ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Reports List */}
      {loading ? (
        <div className="bg-white rounded-2xl p-12 text-center text-slate-400 border border-slate-100 animate-pulse">
          Loading your reported incidents...
        </div>
      ) : filteredReports.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center text-slate-400 border border-slate-100 space-y-3">
          <Info className="w-8 h-8 text-slate-300 mx-auto" />
          <p className="text-sm font-medium">No reports match the selected filter.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredReports.map((r) => {
            const currentStage = getMilestoneIndex(r.status);
            const isResolved = ['Resolved - Verified', 'Resolved', 'Closed'].includes(r.status);
            const isAwaitingEvidence = r.status === 'Awaiting Evidence';
            const isReopened = r.status === 'Reopened';

            return (
              <div
                key={r.id || r._id}
                className="bg-white rounded-2xl p-5 border border-slate-200/90 shadow-xs hover:shadow-md transition-all space-y-4"
              >
                {/* Header row */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <img
                      src={r.image_url || '/uploads/original/clear_street.jpg'}
                      alt={r.title}
                      className="w-14 h-14 rounded-xl object-cover border border-slate-200 shrink-0"
                    />
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-mono font-bold text-blue-600">{r.incident_number}</span>
                        <SeverityBadge severity={r.severity} />
                        <StatusBadge status={r.status} />
                        {isAwaitingEvidence && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 animate-pulse">
                            Action Required: Supplementary Evidence Needed
                          </span>
                        )}
                        {isReopened && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
                            Case Reopened
                          </span>
                        )}
                      </div>
                      <h3 className="text-sm font-bold text-slate-900 mt-1">
                        {r.primary_encroachment_type} at {r.location_name}
                      </h3>
                      <div className="flex items-center gap-3 text-[11px] text-slate-400 mt-1">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" /> {r.date_reported}
                        </span>
                        <span>Occupancy: <strong className="text-slate-600">{r.occupancy_percentage}%</strong></span>
                        <span>Accessibility: <strong className="text-blue-600">{r.accessibility_score}%</strong></span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <button
                      onClick={() => handleOpenDetail(r)}
                      className="px-3 py-1.5 bg-slate-100 hover:bg-blue-50 text-slate-700 hover:text-blue-600 rounded-xl text-xs font-bold transition-colors flex items-center gap-1"
                    >
                      <span>Track Details</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Milestone Progress Bar */}
                <div className="pt-2 border-t border-slate-100">
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                    {milestones.map((m, idx) => {
                      const isCompleted = idx <= currentStage;
                      const isCurrent = idx === currentStage;
                      return (
                        <div key={m.label} className="flex flex-col items-center text-center">
                          <div
                            className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold mb-1 transition-colors ${
                              isCompleted
                                ? 'bg-blue-600 text-white shadow-xs'
                                : 'bg-slate-100 text-slate-400'
                            } ${isCurrent ? 'ring-2 ring-blue-400 ring-offset-1' : ''}`}
                          >
                            {isCompleted ? '✓' : idx + 1}
                          </div>
                          <span className={`text-[10px] font-semibold leading-tight ${isCurrent ? 'text-blue-600' : 'text-slate-500'}`}>
                            {m.label}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Officer assignment note (Privacy preserved - no personal phone/email) */}
                <div className="text-[11px] text-slate-500 bg-slate-50 p-2.5 rounded-xl flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-blue-500" />
                    <span>
                      Enforcement Unit:{' '}
                      <strong className="text-slate-700">
                        {r.assigned_officer_name ? `${r.assigned_officer_name} (Municipal Officer)` : 'Assigned to Ward Enforcement Team'}
                      </strong>
                    </span>
                  </span>
                  {r.sla_status && (
                    <span className="font-semibold text-slate-600">
                      SLA: <span className="text-blue-600">{r.sla_status.overall_status || 'ON_SCHEDULE'}</span>
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Detailed Report Modal / Drawer */}
      {selectedReport && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 shadow-2xl border border-slate-100 space-y-6 max-h-[90vh] overflow-y-auto animate-scale-in">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-slate-100 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-blue-600">{selectedReport.incident_number}</span>
                  <SeverityBadge severity={selectedReport.severity} />
                  <StatusBadge status={selectedReport.status} />
                </div>
                <h2 className="text-lg font-bold text-slate-900 mt-1">
                  {selectedReport.primary_encroachment_type} at {selectedReport.location_name}
                </h2>
              </div>
              <button
                onClick={() => setSelectedReport(null)}
                className="p-1.5 text-slate-400 hover:text-slate-700 rounded-xl hover:bg-slate-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Evidence & Verification Photos */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <span className="text-xs font-bold text-slate-700 flex items-center gap-1">
                  <Camera className="w-3.5 h-3.5 text-slate-500" /> Original Report Photo
                </span>
                <img
                  src={selectedReport.image_url}
                  alt="Original"
                  className="w-full h-44 rounded-xl object-cover border border-slate-200"
                />
              </div>

              {selectedReport.after_images && selectedReport.after_images.length > 0 ? (
                <div className="space-y-1.5">
                  <span className="text-xs font-bold text-emerald-700 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Officer Clearance Verification Photo
                  </span>
                  <img
                    src={selectedReport.after_images[0]}
                    alt="After clearance"
                    className="w-full h-44 rounded-xl object-cover border border-emerald-300 ring-2 ring-emerald-100"
                  />
                </div>
              ) : (
                <div className="space-y-1.5">
                  <span className="text-xs font-bold text-slate-400">Clearance Photo</span>
                  <div className="w-full h-44 rounded-xl bg-slate-50 border border-dashed border-slate-200 flex flex-col items-center justify-center text-slate-400 text-xs p-4 text-center">
                    <Clock className="w-6 h-6 mb-1 text-slate-300" />
                    Pending officer on-site clearance documentation
                  </div>
                </div>
              )}
            </div>

            {/* Reopen Warning if applicable */}
            {selectedReport.status === 'Reopened' && (
              <div className="p-3.5 rounded-xl bg-purple-50 border border-purple-200 text-xs text-purple-900 space-y-1">
                <div className="font-bold flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-purple-600" />
                  This incident was reopened for further municipal review
                </div>
                {selectedReport.reopen_reason && (
                  <p className="text-purple-700">Reason: {selectedReport.reopen_reason}</p>
                )}
              </div>
            )}

            {/* Resolution notes if resolved */}
            {selectedReport.resolution_notes && (
              <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 space-y-1">
                <div className="font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  Officer Resolution Notes
                </div>
                <p className="text-emerald-800">{selectedReport.resolution_notes}</p>
                {selectedReport.resolved_by_name && (
                  <div className="text-[10px] text-emerald-600 mt-1">
                    Resolved by {selectedReport.resolved_by_name} on {new Date(selectedReport.resolution_submitted_at || Date.now()).toLocaleDateString()}
                  </div>
                )}
              </div>
            )}

            {/* Feature F: Service Feedback Rating Card */}
            {['Resolved - Verified', 'Resolved', 'Closed'].includes(selectedReport.status) && (
              <div className="p-5 rounded-2xl bg-gradient-to-br from-blue-50/70 to-indigo-50/70 border border-blue-200/80 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Star className="w-5 h-5 text-amber-500 fill-amber-500" />
                    <h3 className="text-sm font-bold text-slate-900">Rate Municipal Resolution Quality</h3>
                  </div>
                  {existingFeedback && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                      Feedback Recorded
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-600">
                  Your rating directly impacts municipal service quality benchmarks and enforcement performance metrics.
                </p>

                <form onSubmit={handleSubmitFeedback} className="space-y-3">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="text-xs font-semibold text-slate-700 block mb-1">
                        Clearance Satisfaction (1–5 Stars)
                      </label>
                      <div className="flex items-center gap-1">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <button
                            key={star}
                            type="button"
                            onClick={() => setFeedbackRating(star)}
                            className="p-1 focus:outline-none"
                          >
                            <Star
                              className={`w-6 h-6 transition-colors ${
                                star <= feedbackRating
                                  ? 'text-amber-400 fill-amber-400'
                                  : 'text-slate-200'
                              }`}
                            />
                          </button>
                        ))}
                        <span className="ml-2 text-xs font-bold text-slate-700">{feedbackRating}/5</span>
                      </div>
                    </div>

                    <div>
                      <label className="text-xs font-semibold text-slate-700 block mb-1">
                        Timeliness of Resolution (1–5 Stars)
                      </label>
                      <div className="flex items-center gap-1">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <button
                            key={star}
                            type="button"
                            onClick={() => setTimelinessRating(star)}
                            className="p-1 focus:outline-none"
                          >
                            <Star
                              className={`w-6 h-6 transition-colors ${
                                star <= timelinessRating
                                  ? 'text-amber-400 fill-amber-400'
                                  : 'text-slate-200'
                              }`}
                            />
                          </button>
                        ))}
                        <span className="ml-2 text-xs font-bold text-slate-700">{timelinessRating}/5</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-700 block mb-1">
                      Citizen Feedback Comments (Optional)
                    </label>
                    <textarea
                      rows={2}
                      value={feedbackComment}
                      onChange={(e) => setFeedbackComment(e.target.value)}
                      placeholder="Was the footpath fully restored? Share your feedback with municipal authorities..."
                      className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-emerald-600 font-medium">
                      {feedbackSuccess && 'Thank you! Your feedback has been recorded.'}
                    </span>
                    <button
                      type="submit"
                      disabled={submittingFeedback}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-colors disabled:opacity-50"
                    >
                      {submittingFeedback ? 'Submitting...' : existingFeedback ? 'Update Feedback' : 'Submit Feedback'}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Supplementary Citizen Comment & Evidence Form */}
            {!['Resolved - Verified', 'Closed'].includes(selectedReport.status) && (
              <div className="border-t border-slate-100 pt-4 space-y-4">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                  <MessageSquare className="w-4 h-4 text-blue-600" />
                  Citizen Supplementary Updates
                </h3>

                {/* Comment box */}
                <form onSubmit={handleAddComment} className="flex gap-2">
                  <input
                    type="text"
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    placeholder="Add a follow-up note or update for investigating officers..."
                    className="flex-1 text-xs px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:border-blue-500"
                  />
                  <button
                    type="submit"
                    disabled={submittingComment || !commentText.trim()}
                    className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-colors flex items-center gap-1 disabled:opacity-50"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Send</span>
                  </button>
                </form>

                {/* Additional Evidence Photo Upload */}
                <form onSubmit={handleUploadEvidence} className="p-3 bg-slate-50 rounded-xl space-y-2 border border-slate-200/70">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                      <Upload className="w-3.5 h-3.5 text-slate-500" />
                      Attach Supplementary Evidence Photo
                    </span>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => setEvidenceFile(e.target.files[0])}
                      className="text-xs text-slate-500 file:mr-2 file:py-1 file:px-2.5 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                  </div>
                  {evidenceFile && (
                    <div className="flex items-center justify-between pt-1">
                      <span className="text-xs text-slate-600 truncate max-w-xs">{evidenceFile.name}</span>
                      <button
                        type="submit"
                        disabled={uploadingEvidence}
                        className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
                      >
                        {uploadingEvidence ? 'Uploading...' : 'Upload Photo'}
                      </button>
                    </div>
                  )}
                </form>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
