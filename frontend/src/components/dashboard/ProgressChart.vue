<template>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading your health data...</p>
    </div>

    <div v-else-if="error" class="error-container">
      <p class="error-message">{{ error }}</p>
      <button @click="fetchData" class="btn-retry">Retry</button>
    </div>

    <div v-else-if="!hasProfileData" class="empty-container">
      <p>Please complete your health profile to start tracking your progress.</p>
      <router-link to="/profile" class="btn-primary">Complete Profile</router-link>
    </div>

    <!-- Add Weight Modal -->
    <AddWeightModal
      v-if="showAddWeightModal"
      :loading="weightLoading"
      :error="weightError"
      @close="showAddWeightModal = false"
      @save="saveNewWeight"
      @error="setWeightError"
    />
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import AddWeightModal from '@/components/dashboard/AddWeightModal.vue';
import HealthProfileService from '@/services/health-profile_service';
//import WellnessService from '@/services/wellness-service';

export default {
  name: 'Progress',
  components: {
    AddWeightModal
  },
  setup() {
    const loading = ref(true);
    const error = ref(null);
    const profile = ref(null);
    const weightHistory = ref([]);
    const showAddWeightModal = ref(false);
    const weightLoading = ref(false);
    const weightError = ref(null);

    const hasProfileData = computed(() => {
      return profile.value && profile.value.height_cm && profile.value.weight_kg;
    });

    const sortedWeightHistory = computed(() => {
      if (!weightHistory.value || weightHistory.value.length === 0) return [];
      return [...weightHistory.value].sort((a, b) =>
        new Date(b.recorded_at) - new Date(a.recorded_at)
      );
    });

    const startingWeight = computed(() => {
      if (!weightHistory.value || weightHistory.value.length === 0) return null;

      // Get the oldest weight entry
      const oldest = [...weightHistory.value].sort((a, b) =>
        new Date(a.recorded_at) - new Date(b.recorded_at)
      )[0];

      return parseFloat(oldest.weight_kg);
    });

    const totalWeightChange = computed(() => {
      if (!profile.value || !startingWeight.value) return null;

      const currentWeight = parseFloat(profile.value.weight_kg);
      const change = (currentWeight - startingWeight.value).toFixed(1);

      return change;
    });

    const fetchData = async () => {
      loading.value = true;
      error.value = null;

      try {
        // Fetch health profile
        const profileResponse = await HealthProfileService.getHealthProfile();
        profile.value = profileResponse.data;

        // Fetch weight history
        const weightResponse = await HealthProfileService.getWeightHistory();
        weightHistory.value = weightResponse.data;
      } catch (err) {
        console.error('Error fetching progress data:', err);
        error.value = 'Failed to load progress data. Please try again.';
      } finally {
        loading.value = false;
      }
    };

    const saveNewWeight = async (weight) => {
      weightLoading.value = true;
      weightError.value = null;

      try {
        // Add new weight entry
        await HealthProfileService.addWeightEntry(weight);

        // Update profile weight
        const profileData = { ...profile.value, weight_kg: weight };
        await HealthProfileService.updateHealthProfile(profileData);

        // Refresh data
        await fetchData();

        // Close modal
        showAddWeightModal.value = false;
      } catch (err) {
        console.error('Error saving weight:', err);
        weightError.value = 'Failed to save weight. Please try again.';
      } finally {
        weightLoading.value = false;
      }
    };

    const setWeightError = (message) => {
      weightError.value = message;
    };

    const formatDate = (dateString) => {
      const date = new Date(dateString);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    };

    const formatTime = (dateString) => {
      const date = new Date(dateString);
      return date.toLocaleTimeString(undefined, {
        hour: '2-digit',
        minute: '2-digit'
      });
    };

    const getWeightChange = (entry, index) => {
      if (index === sortedWeightHistory.value.length - 1) {
        return '—'; // First entry (most recent)
      }

      const currentWeight = parseFloat(entry.weight_kg);
      const previousWeight = parseFloat(sortedWeightHistory.value[index + 1].weight_kg);
      const change = (currentWeight - previousWeight).toFixed(1);

      return change > 0 ? `+${change}` : change;
    };

    const getChangeClass = (entry, index) => {
      if (index === sortedWeightHistory.value.length - 1) {
        return 'neutral'; // First entry
      }

      const currentWeight = parseFloat(entry.weight_kg);
      const previousWeight = parseFloat(sortedWeightHistory.value[index + 1].weight_kg);
      const change = currentWeight - previousWeight;

      if (change === 0) return 'neutral';

      if (profile.value && profile.value.fitness_goal) {
        if (profile.value.fitness_goal === 'weight_loss') {
          return change < 0 ? 'positive' : 'negative';
        } else if (profile.value.fitness_goal === 'muscle_gain') {
          return change > 0 ? 'positive' : 'negative';
        }
      }

      return 'neutral';
    };

    const getTotalChangeClass = () => {
      if (!totalWeightChange.value || !profile.value) return 'neutral';

      const change = parseFloat(totalWeightChange.value);

      if (change === 0) return 'neutral';

      if (profile.value.fitness_goal === 'weight_loss') {
        return change < 0 ? 'positive' : 'negative';
      } else if (profile.value.fitness_goal === 'muscle_gain') {
        return change > 0 ? 'positive' : 'negative';
      }

      return 'neutral';
    };

    onMounted(() => {
      fetchData();
    });

    return {
      loading,
      error,
      profile,
      weightHistory,
      showAddWeightModal,
      weightLoading,
      weightError,
      hasProfileData,
      sortedWeightHistory,
      startingWeight,
      totalWeightChange,
      fetchData,
      saveNewWeight,
      setWeightError,
      formatDate,
      formatTime,
      getWeightChange,
      getChangeClass,
      getTotalChangeClass
    };
  }
};
</script>

<style scoped>

h1 {
  margin-top: 0;
  margin-bottom: 0.5rem;
}

.loading-container, .error-container, .empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  text-align: center;
  background-color: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top-color: #30C1B1;
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  color: #E53E3E;
  margin-bottom: 1rem;
}

.btn-retry {
  background-color: #4A5568;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.btn-primary {
  background-color: #30C1B1;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

table {
  width: 100%;
  border-collapse: collapse;
}

table th {
  text-align: left;
  padding: 0.75rem;
  background-color: #F7FAFC;
  border-bottom: 1px solid #E2E8F0;
  font-weight: 600;
}

table td {
  padding: 0.75rem;
  border-bottom: 1px solid #E2E8F0;
}

</style>