/**
 * API Endpoints for DeceptGrid Backend Integration
 * Person C - Backend API endpoints for steganography and attack simulation
 */

// Base API URL - adjust for production vs development
const API_BASE = 'http://localhost:8001';

export const API = {
  // Steganography endpoints
  STEG_ENCODE: `${API_BASE}/api/steg/encode`,
  STEG_DECODE: `${API_BASE}/api/steg/decode`,
  STEG_CAPACITY: `${API_BASE}/api/steg/capacity`,

  // Attack simulation endpoints
  INJECT: `${API_BASE}/api/attacks/inject`,
  STOLEN_LOGIN: `${API_BASE}/api/attacks/stolen-login`,
  ATTACK_LOGS: `${API_BASE}/api/attacks/logs`,

  // Person A's endpoints (for integration)
  HONEYPOT_SCAN: `${API_BASE}/api/honeypot/scan`,
  HONEYPOT_LOGIN: `${API_BASE}/api/honeypot/login`,
  HONEYPOT_LOGS: `${API_BASE}/api/honeypot/logs`,

  // Person B's endpoints (for integration)
  AUTH_LOGIN: `${API_BASE}/api/auth/login`,
  METER_STATUS: `${API_BASE}/api/meter/status`,

  // Health checks
  HEALTH: `${API_BASE}/api/health`,
  ROOT: `${API_BASE}/`
};

// Common fetch wrapper with error handling
export const apiCall = async (url, options = {}) => {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
};

// Multipart form data wrapper for file uploads
export const apiUpload = async (url, formData) => {
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    return response;
  } catch (error) {
    console.error('Upload failed:', error);
    throw error;
  }
};

export default API;