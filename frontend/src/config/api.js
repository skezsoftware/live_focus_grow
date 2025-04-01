const API_BASE_URL = '/api';

export const API_ENDPOINTS = {
    register: `${API_BASE_URL}/auth/register`,
    login: `${API_BASE_URL}/auth/login`,
    // Add other endpoints as needed
};

export const API_CONFIG = {
    headers: {
        'Content-Type': 'application/json'
    }
}; 