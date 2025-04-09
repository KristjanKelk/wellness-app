// src/services/health-profile.service.js
import apiClient from './http.service';

class HealthProfileService {
    getHealthProfile() {
        return apiClient.get('health-profiles/my_profile/');
    }

    updateHealthProfile(profileData) {
        return apiClient.put('health-profiles/my_profile/', profileData);
    }

    createHealthProfile(profileData) {
        return apiClient.post('health-profiles/', profileData);
    }

    addWeightEntry(weight) {
        return apiClient.post('weight-history/', { weight_kg: weight });
    }

    getWeightHistory() {
        return apiClient.get('weight-history/');
    }
}

export default new HealthProfileService();