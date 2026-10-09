const API_BASE = '/api';

function getAuthHeaders() {
  const token = localStorage.getItem('health_auth_token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export const api = {
  // Auth
  async signup(name, email, password) {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Signup failed');
    return data;
  },

  async signin(email, password) {
    const res = await fetch(`${API_BASE}/auth/signin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');
    return data;
  },

  async getMe() {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to get user');
    return data.user;
  },

  async signout() {
    await fetch(`${API_BASE}/auth/signout`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
  },

  // Sessions
  async getSessions() {
    const res = await fetch(`${API_BASE}/sessions`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) return [];
    return await res.json();
  },

  async createSession(title) {
    const res = await fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ title }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to create session');
    return data;
  },

  async deleteSession(sessionId) {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to delete session');
    return data;
  },

  async getSessionMessages(sessionId) {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/messages`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) return [];
    return await res.json();
  },

  // Analysis & PDF
  async getSampleReport() {
    const res = await fetch(`${API_BASE}/analysis/sample-report`);
    const data = await res.json();
    return data.report;
  },

  async extractPdf(file) {
    const formData = new FormData();
    formData.append('file', file);
    const token = localStorage.getItem('health_auth_token');
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}/analysis/extract-pdf`, {
      method: 'POST',
      headers,
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'PDF extraction failed');
    return data.text;
  },

  async runAnalysis({ sessionId, patientName, age, gender, reportText, model }) {
    const res = await fetch(`${API_BASE}/analysis`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        session_id: sessionId,
        patient_name: patientName,
        age: parseInt(age, 10),
        gender,
        report_text: reportText,
        model,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Analysis failed');
    return data;
  },

  // Chat follow-up
  async sendChatMessage({ sessionId, query, model }) {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        session_id: sessionId,
        query,
        model,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to send question');
    return data;
  },

  // Models & Config
  async getModels() {
    const res = await fetch(`${API_BASE}/models`);
    if (!res.ok) return null;
    return await res.json();
  },

  async getConfig() {
    const res = await fetch(`${API_BASE}/config`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) return null;
    return await res.json();
  },

  // ========================================================
  // Clinical Evidence Intelligence Platform APIs
  // ========================================================
  async uploadClinicalDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    const token = localStorage.getItem('health_auth_token');
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}/documents`, {
      method: 'POST',
      headers,
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Document upload failed');
    return data;
  },

  async listClinicalDocuments() {
    const res = await fetch(`${API_BASE}/documents`);
    if (!res.ok) return [];
    return await res.json();
  },

  async getClinicalDocument(docId) {
    const res = await fetch(`${API_BASE}/documents/${docId}`);
    if (!res.ok) throw new Error('Document not found');
    return await res.json();
  },

  async createClinicalPatient(patientData) {
    const res = await fetch(`${API_BASE}/patients`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(patientData),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to create patient');
    return data;
  },

  async listClinicalPatients() {
    const res = await fetch(`${API_BASE}/patients`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) return [];
    return await res.json();
  },

  async getClinicalPatient(patientId) {
    const res = await fetch(`${API_BASE}/patients/${patientId}`);
    if (!res.ok) throw new Error('Patient not found');
    return await res.json();
  },

  async analyzeClinicalPatient(patientId, documentId, model) {
    const res = await fetch(`${API_BASE}/patients/${patientId}/analyze`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        document_id: documentId,
        model: model || undefined,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Clinical analysis pipeline failed');
    return data;
  },

  async getClinicalPatientTimeline(patientId) {
    const res = await fetch(`${API_BASE}/patients/${patientId}/timeline`);
    if (!res.ok) throw new Error('Timeline retrieval failed');
    return await res.json();
  },

  async listKnowledgeBases() {
    const res = await fetch(`${API_BASE}/knowledge-bases`);
    if (!res.ok) return [];
    return await res.json();
  },

  async queryKnowledgeBase(kbId, query, topK = 4) {
    const res = await fetch(`${API_BASE}/knowledge-bases/${kbId}/query`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ query, top_k: topK }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Knowledge base query failed');
    return data;
  },

  async getAnalysisRecord(analysisId) {
    const res = await fetch(`${API_BASE}/analyses/${analysisId}`);
    if (!res.ok) throw new Error('Analysis record not found');
    return await res.json();
  },

  async listAnalysisRecords(patientId) {
    const url = patientId ? `${API_BASE}/analyses?patient_id=${patientId}` : `${API_BASE}/analyses`;
    const res = await fetch(url);
    if (!res.ok) return [];
    return await res.json();
  },

  async getAuditEvents(patientId, eventType, limit = 50) {
    let url = `${API_BASE}/audit/events?limit=${limit}`;
    if (patientId) url += `&patient_id=${patientId}`;
    if (eventType) url += `&event_type=${eventType}`;
    const res = await fetch(url);
    if (!res.ok) return [];
    return await res.json();
  },
};
