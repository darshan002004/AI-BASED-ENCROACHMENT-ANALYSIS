import axios from 'axios';

const API = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('encrowatch_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear expired credentials from localStorage to prevent repetitive unauthorized calls
      localStorage.removeItem('encrowatch_token');
      localStorage.removeItem('encrowatch_user');
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (data) => API.post('/auth/login', data),
  register: (data) => API.post('/auth/register', data),
  registerOfficer: (data) => API.post('/auth/register-officer', data),
  getMe: () => API.get('/auth/me'),
  getOfficers: () => API.get('/auth/officers'),
  getPendingOfficers: () => API.get('/auth/officers/pending'),
  getAllOfficers: (status) => API.get('/auth/officers/all', { params: status ? { status } : {} }),
  approveOfficer: (userId) => API.post(`/auth/officers/${userId}/approve`),
  rejectOfficer: (userId, reason) => API.post(`/auth/officers/${userId}/reject`, { reason }),
  toggleOfficerActive: (userId) => API.post(`/auth/officers/${userId}/toggle-active`),
  getUsers: (params) => API.get('/auth/users', { params }),
  demoSwitch: (role) => API.post(`/auth/demo-switch/${role}`),
};

export const incidentsAPI = {
  list: (params) => API.get('/incidents', { params }),
  getById: (id) => API.get(`/incidents/${id}`),
  create: (data) => API.post('/incidents', data),
  update: (id, data) => API.patch(`/incidents/${id}`, data),
  submitInspection: (id, data) => API.post(`/incidents/${id}/inspect`, data),
  verifyResolution: (id) => API.post(`/incidents/${id}/verify-resolution`),
  getPossibleDuplicates: (id) => API.get(`/incidents/${id}/possible-duplicates`),
  mergeDuplicate: (id, masterId) => API.post(`/incidents/${id}/merge-duplicate`, null, { params: { master_incident_id: masterId } }),
  keepSeparate: (id, reason) => API.post(`/incidents/${id}/keep-separate`, null, { params: { reason } }),
  addEvidence: (id, formData, caption = 'Additional Evidence') => API.post(`/incidents/${id}/evidence`, formData, {
    params: { caption },
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getRiskForecast: (id) => API.get(`/incidents/${id}/risk-forecast`),
  getReviewQueue: (params = {}) => API.get('/incidents/review-queue', { params }),
  getRawEvidence: (id) => API.get(`/incidents/${id}/raw-evidence`),
  batchSync: (data) => API.post('/incidents/batch-sync', data),
  submitResolution: (id, data) => API.post(`/incidents/${id}/submit-resolution`, data),
  reviewResolution: (id, data) => API.post(`/incidents/${id}/review-resolution`, data),
  reopen: (id, data) => API.post(`/incidents/${id}/reopen`, data),
  addCitizenComment: (id, data) => API.post(`/incidents/${id}/citizen-comment`, data),
};

export const aiAPI = {
  getCapabilities: () => API.get('/ai/capabilities'),
  analyzeImage: (formData, params = {}) => API.post('/ai/analyze', formData, {
    params,
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  analyzeMultiple: (formData, params = {}) => API.post('/ai/analyze-multiple', formData, {
    params,
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  trackVideo: (formData) => API.post('/ai/track-video', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  verifyBeforeAfter: (formData) => API.post('/ai/verify', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
};

export const analyticsAPI = {
  getKPIs: () => API.get('/analytics/kpis'),
  getTypes: () => API.get('/analytics/encroachment-types'),
  getMonthlyTrend: () => API.get('/analytics/monthly-trend'),
  getTopAreas: () => API.get('/analytics/top-affected-areas'),
  getTimeOfDay: () => API.get('/analytics/time-of-day'),
  getDayOfWeek: () => API.get('/analytics/day-of-week'),
  getHotspots: (params = {}) => API.get('/analytics/hotspots', { params }),
  getLocationHealth: () => API.get('/analytics/location-health'),
  compareAreas: (areas) => API.get('/analytics/compare-areas', { params: { areas } }),
  predictHotspotRisk: (area, time_window) => API.get('/analytics/predict-hotspot-risk', { params: { area, time_window } }),
};

export const feedbackAPI = {
  getDataset: (params) => API.get('/feedback/dataset', { params }),
  getMetrics: () => API.get('/feedback/metrics'),
  verify: (data) => API.post('/feedback/verify', data),
  approve: (id) => API.post(`/feedback/${id}/approve`),
  reject: (id, reason) => API.post(`/feedback/${id}/reject`, null, { params: { reason } }),
  getTrainingWorkflow: () => API.get('/feedback/training-workflow'),
  getExportUrl: (format = 'jsonl', status = 'APPROVED') => `/api/feedback/export?format=${format}&approval_status=${status}`,
};

export const auditAPI = {
  getLogs: (params) => API.get('/audit/logs', { params }),
  verifyIntegrity: () => API.get('/audit/verify-integrity'),
};

export const modelOpsAPI = {
  listModels: () => API.get('/model-ops/models'),
  registerCandidate: (data) => API.post('/model-ops/models/register', data),
  evaluate: (data) => API.post('/model-ops/evaluate', data),
  getEvaluations: (params = {}) => API.get('/model-ops/evaluations', { params }),
  getEvaluationDetails: (id) => API.get(`/model-ops/evaluations/${id}`),
  promoteCandidate: (data) => API.post('/model-ops/models/promote', data),
  rollback: (data) => API.post('/model-ops/models/rollback', data),
  validateDataset: (data) => API.post('/model-ops/training/validate-dataset', data),
  prepareTraining: (data) => API.post('/model-ops/training/prepare', data),
  getTrainingEnvironment: () => API.get('/model-ops/training/environment'),
};

export const reportsAPI = {
  getCSVUrl: () => '/api/reports/csv',
  getIncidentPDFUrl: (id) => `/api/reports/pdf/incident/${id}`,
};

export const slaAPI = {
  getRules: () => API.get('/sla/rules'),
  updateRules: (data) => API.put('/sla/rules', data),
  evaluate: (incidentId = null) => API.post('/sla/evaluate', null, { params: incidentId ? { incident_id: incidentId } : {} }),
  getIncidentSLA: (id) => API.get(`/sla/incident/${id}`),
};

export const notificationsAPI = {
  list: (params = {}) => API.get('/notifications', { params }),
  getUnreadCount: () => API.get('/notifications/unread-count'),
  markRead: (id) => API.patch(`/notifications/${id}/read`),
  markAllRead: () => API.post('/notifications/mark-all-read'),
};

export const publicAPI = {
  getIncidents: (params = {}) => API.get('/public/incidents', { params }),
  getStatistics: (days = 30) => API.get('/public/statistics', { params: { days } }),
};

export const serviceFeedbackAPI = {
  submit: (id, data) => API.post(`/incidents/${id}/citizen-feedback`, data),
  get: (id) => API.get(`/incidents/${id}/citizen-feedback`),
  getSummary: () => API.get('/service-quality/summary'),
};

export default API;

