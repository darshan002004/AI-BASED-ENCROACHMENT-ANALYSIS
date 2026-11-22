import React, { useState, useEffect } from 'react';
import {
  Search,
  Plus,
  Eye,
  Download,
  Calendar,
  Filter,
  ExternalLink,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { StatusBadge, SeverityBadge } from '../../components/StatusBadge';
import { incidentsAPI, reportsAPI } from '../../services/api';

export default function IncidentsPage({ onSelectIncident, onNewIncident }) {
  const [incidents, setIncidents] = useState([]);
  const [statusFilter, setStatusFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchIncidents = async () => {
    setLoading(true);
    try {
      const params = { limit: 50 };
      if (statusFilter !== 'All') params.status = statusFilter;
      if (typeFilter !== 'All') params.encroachment_type = typeFilter;
      if (searchQuery) params.search = searchQuery;

      const res = await incidentsAPI.list(params);
      setIncidents(res.data || []);
    } catch (err) {
      console.error('Failed to fetch incidents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, [statusFilter, typeFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchIncidents();
  };

  const handleDownloadCSV = () => {
    window.open(reportsAPI.getCSVUrl(), '_blank');
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-4">
        <div>
          <h1 className="text-base font-bold text-slate-900 tracking-tight">Incidents Directory</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Verified urban encroachment logs, field assignments, and resolution statuses
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={handleDownloadCSV}
            className="px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors shadow-2xs flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            Export CSV
          </button>
          <button
            onClick={onNewIncident}
            className="px-3.5 py-1.5 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg shadow-2xs transition-colors flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>Add Incident</span>
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <form
        onSubmit={handleSearchSubmit}
        className="bg-white rounded-xl border border-slate-200/90 shadow-2xs p-3.5 flex flex-wrap items-center gap-2.5 text-xs"
      >
        {/* Status Dropdown */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 cursor-pointer text-xs"
        >
          <option value="All">All Status</option>
          <option value="Pending">Pending</option>
          <option value="Verified">Verified</option>
          <option value="Assigned">Assigned</option>
          <option value="In Progress">In Progress</option>
          <option value="Resolved">Resolved</option>
        </select>

        {/* Type Dropdown */}
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 cursor-pointer text-xs"
        >
          <option value="All">All Type</option>
          <option value="Street Vendor">Street Vendor</option>
          <option value="Vehicle">Vehicle</option>
          <option value="Construction">Construction Material</option>
          <option value="Shop Extension">Shop Extension</option>
          <option value="Garbage">Garbage / Debris</option>
        </select>

        {/* Date Inputs */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5">
          <Calendar className="w-3.5 h-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Start Date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="bg-transparent text-slate-700 w-20 focus:outline-none font-normal placeholder:text-slate-400 text-xs"
          />
          <span className="text-slate-300">→</span>
          <input
            type="text"
            placeholder="End Date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="bg-transparent text-slate-700 w-20 focus:outline-none font-normal placeholder:text-slate-400 text-xs"
          />
        </div>

        {/* Search Input & Button */}
        <div className="flex items-center gap-1.5 ml-auto w-full sm:w-auto">
          <div className="relative flex-1 sm:w-56">
            <input
              type="text"
              placeholder="Search incident, location..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-xs font-normal"
            />
          </div>
          <button
            type="submit"
            className="p-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg shadow-2xs transition-colors shrink-0"
            title="Search"
          >
            <Search className="w-3.5 h-3.5" />
          </button>
        </div>
      </form>

      {/* Incidents Table */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            {/* Table Header */}
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
              <tr>
                <th className="py-3 px-4">ID</th>
                <th className="py-3 px-4">Image</th>
                <th className="py-3 px-4">Location</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>

            {/* Table Body */}
            <tbody className="divide-y divide-slate-100">
              {incidents.length > 0 ? (
                incidents.map((inc, index) => {
                  const displayId = inc.incident_number || `#00${index + 1}`;
                  return (
                    <tr
                      key={inc.id || inc._id}
                      className="hover:bg-slate-50/80 transition-colors group"
                    >
                      {/* ID */}
                      <td className="py-3 px-4 font-mono font-semibold text-slate-700">
                        {displayId}
                      </td>

                      {/* Image Thumbnail */}
                      <td className="py-3 px-4">
                        <img
                          src={inc.image_url || '/uploads/original/clear_street.jpg'}
                          alt={inc.title || 'Incident Image'}
                          onError={(e) => { e.currentTarget.onerror = null; e.currentTarget.src = '/uploads/original/clear_street.jpg'; }}
                          className="w-10 h-10 rounded-lg object-cover border border-slate-200 bg-slate-100"
                        />
                      </td>

                      {/* Location */}
                      <td className="py-3 px-4 font-semibold text-slate-900">
                        {inc.location_name || 'Unspecified Corridor'}
                      </td>

                      {/* Type */}
                      <td className="py-3 px-4 text-slate-600 font-medium">
                        {inc.primary_encroachment_type || 'General'}
                      </td>

                      {/* Severity Badge */}
                      <td className="py-3 px-4">
                        <SeverityBadge severity={inc.severity} />
                      </td>

                      {/* Status Badge */}
                      <td className="py-3 px-4">
                        <StatusBadge status={inc.status} />
                      </td>

                      {/* Date */}
                      <td className="py-3 px-4 text-slate-500 font-normal whitespace-nowrap">
                        {inc.date_reported || inc.created_at || 'Recently Reported'}
                      </td>

                      {/* Action Button: [View] */}
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => onSelectIncident && onSelectIncident(inc)}
                          className="px-3 py-1 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <p className="font-semibold text-slate-700 text-sm">No incidents have been reported yet.</p>
                    <p className="mt-1 text-xs text-slate-500">No incidents match the selected filters or exist in the database.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Table Footer / Summary */}
        <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500 font-medium px-4">
          <span>Showing <strong>{incidents.length}</strong> incidents</span>
          <div className="flex items-center gap-1">
            <button className="p-1 rounded-lg border border-slate-200 text-slate-400 hover:bg-white disabled:opacity-50" disabled>
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button className="p-1 rounded-lg border border-slate-200 text-slate-400 hover:bg-white disabled:opacity-50" disabled>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
