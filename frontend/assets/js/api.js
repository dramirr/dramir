// ✅ CRITICAL: Auto-detect API URL based on environment
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000/api'
    : `${window.location.origin}/api`;

console.log('🔗 API URL:', API_URL);

function getAuthHeader() {
    const token = localStorage.getItem('access_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

const api = {
    async login(username, password) {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Login failed');
        }
        
        return await response.json();
    },

    async getCurrentUser() {
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            }
        });
        
        if (!response.ok) throw new Error('Failed to get user info');
        return await response.json();
    },

    async logout() {
        await fetch(`${API_URL}/auth/logout`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            }
        });
    },

    async getPositions() {
        const response = await fetch(`${API_URL}/positions`, {
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            }
        });
        
        if (!response.ok) throw new Error('Failed to get positions');
        return await response.json();
    },

    async getPosition(id) {
        const response = await fetch(`${API_URL}/positions/${id}`, {
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            }
        });
        
        if (!response.ok) throw new Error('Failed to get position');
        return await response.json();
    },

    async createPosition(data) {
        const response = await fetch(`${API_URL}/positions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) throw new Error('Failed to create position');
        return await response.json();
    },

    async uploadResume(file, positionId) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('position_id', positionId);
        
        const token = localStorage.getItem('access_token');
        const headers = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${API_URL}/resumes/upload`, {
            method: 'POST',
            headers: headers,
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: 'Upload failed' }));
            throw new Error(error.message || error.error || 'Upload failed');
        }
        
        return await response.json();
    },

    async bulkUploadResumes(files, positionId) {
        const formData = new FormData();
        files.forEach(file => formData.append('files', file));
        formData.append('position_id', positionId);
        
        const token = localStorage.getItem('access_token');
        const headers = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${API_URL}/resumes/bulk`, {
            method: 'POST',
            headers: headers,
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: 'Bulk upload failed' }));
            throw new Error(error.message || 'Bulk upload failed');
        }
        return await response.json();
    },

    async getResumes(filters = {}) {
        let url = `${API_URL}/resumes`;
        const params = new URLSearchParams();
        
        if (filters.position_id) {
            params.append('position_id', filters.position_id);
        }
        
        if (filters.status) {
            params.append('status', filters.status);
        }
        
        if (filters.score_min !== undefined) {
            params.append('score_min', filters.score_min);
        }
        if (filters.score_max !== undefined) {
            params.append('score_max', filters.score_max);
        }
        
        if (params.toString()) {
            url += `?${params.toString()}`;
        }
        
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            }
        });
        
        if (!response.ok) throw new Error('Failed to get resumes');
        return await response.json();
    },

    async getResume(id) {
        const response = await fetch(`${API_URL}/resumes/${id}`, {
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            }
        });
        
        if (!response.ok) throw new Error('Failed to get resume');
        return await response.json();
    },

    async getResumeStatus(resumeId) {
        const response = await fetch(`${API_URL}/resumes/${resumeId}/status`, {
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            }
        });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.message || 'Failed to get resume status');
        }
        return await response.json();
    },

    async deleteResume(id) {
        const response = await fetch(`${API_URL}/resumes/${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            }
        });
        
        if (!response.ok) throw new Error('Failed to delete resume');
        return await response.json();
    },

    async getInterviewQuestions(resumeId) {
        const response = await fetch(`${API_URL}/resumes/${resumeId}/questions`, {
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            }
        });
        
        if (!response.ok) throw new Error('Failed to get interview questions');
        return await response.json();
    },

    async getCandidates() {
        const response = await fetch(`${API_URL}/candidates`, {
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            }
        });
        
        if (!response.ok) throw new Error('Failed to get candidates');
        return await response.json();
    },

    async getCandidate(id) {
        const response = await fetch(`${API_URL}/candidates/${id}`, {
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            }
        });
        
        if (!response.ok) throw new Error('Failed to get candidate');
        return await response.json();
    },

    async searchCandidates(query) {
        const response = await fetch(`${API_URL}/candidates/search?q=${encodeURIComponent(query)}`, {
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            }
        });
        
        if (!response.ok) throw new Error('Search failed');
        return await response.json();
    },

    async addCandidateNote(candidateId, noteText) {
        const response = await fetch(`${API_URL}/candidates/${candidateId}/notes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            },
            body: JSON.stringify({ note_text: noteText })
        });
        
        if (!response.ok) throw new Error('Failed to add note');
        return await response.json();
    },

    async getCriteria(positionId) {
        const response = await fetch(`${API_URL}/criteria/positions/${positionId}/criteria`, {
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            }
        });
        
        if (!response.ok) throw new Error('Failed to get criteria');
        return await response.json();
    },

    async createCriterion(positionId, data) {
        const response = await fetch(`${API_URL}/criteria/positions/${positionId}/criteria`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) throw new Error('Failed to create criterion');
        return await response.json();
    },

    async updateCriterion(id, data) {
        const response = await fetch(`${API_URL}/criteria/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) throw new Error('Failed to update criterion');
        return await response.json();
    },

    async deleteCriterion(id) {
        const response = await fetch(`${API_URL}/criteria/${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            }
        });
        
        if (!response.ok) throw new Error('Failed to delete criterion');
        return await response.json();
    }
};

// Make api object available globally
window.api = api;