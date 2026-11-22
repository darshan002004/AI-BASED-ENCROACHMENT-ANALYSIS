import React from 'react';

export function StatusBadge({ status }) {
  const norm = (status || '').toLowerCase().trim();

  // Resolved / Verified states (Green #059669)
  if (norm.includes('verified') || norm === 'resolved') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
        {status || 'Resolved - Verified'}
      </span>
    );
  }

  // Action completed / Pending verification (Light Green / Teal)
  if (norm.includes('pending verification')) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-50 text-teal-700 border border-teal-200">
        <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
        Verification Pending
      </span>
    );
  }

  // Active / In Progress / Assigned (Blue #2563EB)
  if (norm === 'in progress' || norm === 'assigned' || norm.includes('investigation') || norm === 'ai review') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
        <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
        {status || 'In Progress'}
      </span>
    );
  }

  // Pending / Awaiting Evidence / Submitted (Amber #D97706)
  if (norm === 'pending' || norm === 'submitted' || norm.includes('awaiting evidence')) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
        {status || 'Pending Review'}
      </span>
    );
  }

  // Reopened / Rejected / Escalated (Red #DC2626)
  if (norm === 'reopened' || norm === 'rejected' || norm.includes('escalated') || norm.includes('overdue')) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
        <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
        {status || 'Action Required'}
      </span>
    );
  }

  // Fallback
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
      <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
      {status || 'Unknown'}
    </span>
  );
}

export function SeverityBadge({ severity }) {
  const norm = (severity || '').toLowerCase().trim();

  // Critical / High Severity (Red #DC2626)
  if (norm === 'high' || norm === 'critical') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-bold bg-red-50 text-red-700 border border-red-200 uppercase tracking-wide">
        High Severity
      </span>
    );
  }

  // Moderate / Medium Severity (Amber #D97706)
  if (norm === 'medium' || norm === 'moderate') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200 uppercase tracking-wide">
        Medium
      </span>
    );
  }

  // Low Severity (Neutral Slate)
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-bold bg-slate-100 text-slate-600 border border-slate-200 uppercase tracking-wide">
      Low
    </span>
  );
}
