const API_BASE = '/api';

function getAuthHeaders() {
  const token = localStorage.getItem('hia_auth_token');
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
    const token = localStorage.getItem('hia_auth_token');
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
};
