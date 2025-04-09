// src/services/health-profile.service.js
import axios from 'axios';
import authHeader from './auth-header';

const API_URL = 'http://localhost:8000/api/';

class HealthProfileService {
    getHealthProfile() {
        return axios.get(API_URL + 'health-profiles/my-profile/', { headers: authHeader() });
    }

    updateHealthProfile(profileData) {
        return axios.put(API_URL + 'health-profiles/my-profile/', profileData, { headers: authHeader() });
    }

    addWeightEntry(weight) {
        return axios.post(API_URL + 'weight-history/', { weight_kg: weight }, { headers: authHeader() });
    }

    getWeightHistory() {
        return axios.get(API_URL + 'weight-history/', { headers: authHeader() });
    }
}

export default new HealthProfileService();