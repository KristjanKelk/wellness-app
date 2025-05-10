<template>
  <div class="progress-container">
    <h1>Your Progress</h1>
    <p class="page-description">Track your weight changes over time.</p>

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

    <div v-else class="progress-content">
      <!-- Weight Progress Chart -->
      <div class="chart-section">
        <h2>Weight Progress Chart</h2>
        <div class="chart-container">
          <canvas ref="weightChart"></canvas>
        </div>

        <div v-if="weightHistory && weightHistory.length > 1" class="chart-info">
          <div class="info-item">
            <div class="info-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="#30C1B1" stroke-width="2"/>
                <path d="M12 16V12" stroke="#30C1B1" stroke-width="2" stroke-linecap="round"/>
                <circle cx="12" cy="8" r="1" fill="#30C1B1"/>
              </svg>
            </div>
            <div class="info-text">Each point represents a weight entry with a unique timestamp</div>
          </div>
          <div v-if="profile?.target_weight_kg" class="info-item">
            <div class="info-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 12H21" stroke="#FF9800" stroke-width="2" stroke-linecap="round" stroke-dasharray="4 4"/>
              </svg>
            </div>
            <div class="info-text">Dashed line shows your target weight ({{ profile.target_weight_kg }} kg)</div>
          </div>
        </div>
      </div>

      <!-- Weight History Section -->
      <div class="weight-history-section">
        <h2>Weight History</h2>
        <div class="weight-history-header">
          <div class="weight-summary">
            <div class="summary-item">
              <div class="summary-label">Starting Weight</div>
              <div class="summary-value">{{ startingWeight || '—' }} kg</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">Current Weight</div>
              <div class="summary-value">{{ profile?.weight_kg || '—' }} kg</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">Target Weight</div>
              <div class="summary-value">{{ profile?.target_weight_kg || 'Not set' }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">Total Change</div>
              <div class="summary-value" :class="getTotalChangeClass()">
                {{ totalWeightChange > 0 ? '+' : '' }}{{ totalWeightChange || '0' }} kg
              </div>
            </div>
          </div>
          <div class="action-buttons">
            <button @click="showAddWeightModal = true" class="btn-primary">
              Log New Weight
            </button>
          </div>
        </div>

        <div v-if="weightHistory && weightHistory.length > 0" class="weight-history-table">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Time</th>
                <th>Weight (kg)</th>
                <th>Change</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(entry, index) in sortedWeightHistory" :key="entry.id">
                <td>{{ formatDate(entry.recorded_at) }}</td>
                <td>{{ formatTime(entry.recorded_at) }}</td>
                <td>{{ entry.weight_kg }}</td>
                <td :class="getChangeClass(entry, index)">
                  {{ getWeightChange(entry, index) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="no-data-message">
          <p>No weight history data available. Start logging your weight to see your progress over time.</p>
        </div>

        <div v-if="weightHistory && weightHistory.length > 1" class="timestamp-verification">
          <div class="verification-icon">✓</div>
          <div class="verification-text">
            Each weight entry has a unique timestamp for accurate tracking
          </div>
        </div>
      </div>
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
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import Chart from 'chart.js/auto';
import AddWeightModal from '@/components/dashboard/AddWeightModal.vue';
import HealthProfileService from '@/services/health-profile_service';

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
    const weightChart = ref(null);
    const weightChartInstance = ref(null);

    // Computed properties
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

    // Data fetching
    const fetchData = async () => {
      loading.value = true;
      error.value = null;

      try {
        const profileResponse = await HealthProfileService.getHealthProfile();
        profile.value = profileResponse.data;

        const weightResponse = await HealthProfileService.getWeightHistory();
        weightHistory.value = weightResponse.data;

        renderWeightChart();
      } catch (err) {
        console.error('Error fetching progress data:', err);
        error.value = 'Failed to load progress data. Please try again.';
      } finally {
        loading.value = false;
      }
    };

    // Render weight progress chart
    const renderWeightChart = () => {
      if (!weightChart.value || !weightHistory.value || weightHistory.value.length === 0) return;

      if (weightChartInstance.value) {
        weightChartInstance.value.destroy();
      }

      const sortedEntries = [...weightHistory.value].sort((a, b) =>
        new Date(a.recorded_at) - new Date(b.recorded_at)
      );

      const datasets = [
        {
          label: 'Weight (kg)',
          data: sortedEntries.map(entry => ({
            x: new Date(entry.recorded_at),
            y: parseFloat(entry.weight_kg)
          })),
          borderColor: '#30C1B1',
          backgroundColor: 'rgba(48, 193, 177, 0.1)',
          borderWidth: 2,
          tension: 0.3,
          fill: true
        }
      ];

      // Add target weight line if available
      if (profile.value?.target_weight_kg) {
        datasets.push({
          label: 'Target Weight',
          data: sortedEntries.map(entry => ({
            x: new Date(entry.recorded_at),
            y: parseFloat(profile.value.target_weight_kg)
          })),
          borderColor: '#FF9800',
          borderWidth: 2,
          borderDash: [5, 5],
          fill: false,
          pointRadius: 0
        });
      }

      weightChartInstance.value = new Chart(weightChart.value, {
        type: 'line',
        data: {
          datasets: datasets
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            mode: 'index',
            intersect: false,
          },
          plugins: {
            legend: {
              position: 'bottom'
            },
            tooltip: {
              callbacks: {
                title: function(context) {
                  return new Date(context[0].parsed.x).toLocaleDateString();
                }
              }
            }
          },
          scales: {
            x: {
              type: 'time',
              time: {
                unit: sortedEntries.length <= 7 ? 'day' :
                     sortedEntries.length <= 30 ? 'week' : 'month'
              },
              title: {
                display: true,
                text: 'Date'
              }
            },
            y: {
              title: {
                display: true,
                text: 'Weight (kg)'
              }
            }
          }
        }
      });
    };

    // Add new weight entry
    const saveNewWeight = async (weight) => {
      weightLoading.value = true;
      weightError.value = null;

      try {
        await HealthProfileService.addWeightEntry(weight);
        const profileData = { ...profile.value, weight_kg: weight };
        await HealthProfileService.updateHealthProfile(profileData);
        await fetchData();
        showAddWeightModal.value = false;
      } catch (err) {
        console.error('Error saving weight:', err);
        if (err.response && err.response.data && err.response.data.detail) {
          weightError.value = err.response.data.detail;
        } else {
          weightError.value = 'Failed to save weight. Please try again.';
        }
      } finally {
        weightLoading.value = false;
      }
    };

    // Utility methods
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
        return '—';
      }

      const currentWeight = parseFloat(entry.weight_kg);
      const previousWeight = parseFloat(sortedWeightHistory.value[index + 1].weight_kg);
      const change = (currentWeight - previousWeight).toFixed(1);

      return change > 0 ? `+${change}` : change;
    };

    const getChangeClass = (entry, index) => {
      if (index === sortedWeightHistory.value.length - 1) {
        return 'neutral';
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

    // Initialize component
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
      weightChart,
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

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';
@import '@/assets/styles/pages/_progress.scss';
</style>