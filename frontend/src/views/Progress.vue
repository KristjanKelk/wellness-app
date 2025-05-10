<template>
  <div class="progress-container">
    <h1>Your Progress</h1>
    <p class="page-description">Track your health journey with detailed visualizations of your progress over time.</p>

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

      <!-- Wellness Score Section -->
      <div v-if="wellnessScores && wellnessScores.length > 0" class="wellness-evolution-section">
        <h2>Wellness Score Evolution</h2>
        <div class="wellness-chart">
          <canvas ref="wellnessChart"></canvas>
        </div>
        <div class="wellness-components">
          <h3>Score Components</h3>
          <div class="component-grid">
            <div class="component-item">
              <div class="component-header">
                <div class="component-title">BMI Score</div>
                <div class="component-percentage">30%</div>
              </div>
              <div class="component-bar-container">
                <div
                  class="component-bar bmi-bar"
                  :style="{ width: latestWellnessScore?.bmi_score + '%' }"
                ></div>
              </div>
              <div class="component-value">{{ latestWellnessScore?.bmi_score || 0 }}/100</div>
            </div>
            <div class="component-item">
              <div class="component-header">
                <div class="component-title">Activity Score</div>
                <div class="component-percentage">30%</div>
              </div>
              <div class="component-bar-container">
                <div
                  class="component-bar activity-bar"
                  :style="{ width: latestWellnessScore?.activity_score + '%' }"
                ></div>
              </div>
              <div class="component-value">{{ latestWellnessScore?.activity_score || 0 }}/100</div>
            </div>
            <div class="component-item">
              <div class="component-header">
                <div class="component-title">Progress Score</div>
                <div class="component-percentage">20%</div>
              </div>
              <div class="component-bar-container">
                <div
                  class="component-bar progress-bar"
                  :style="{ width: latestWellnessScore?.progress_score + '%' }"
                ></div>
              </div>
              <div class="component-value">{{ latestWellnessScore?.progress_score || 0 }}/100</div>
            </div>
            <div class="component-item">
              <div class="component-header">
                <div class="component-title">Habits Score</div>
                <div class="component-percentage">20%</div>
              </div>
              <div class="component-bar-container">
                <div
                  class="component-bar habits-bar"
                  :style="{ width: latestWellnessScore?.habits_score + '%' }"
                ></div>
              </div>
              <div class="component-value">{{ latestWellnessScore?.habits_score || 0 }}/100</div>
            </div>
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
import { ref, computed, onMounted, watch } from 'vue';
import Chart from 'chart.js/auto';
import AddWeightModal from '@/components/dashboard/AddWeightModal.vue';
import HealthProfileService from '@/services/health-profile_service';
import WellnessService from '@/services/wellness-service';

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
    const wellnessScores = ref([]);
    const showAddWeightModal = ref(false);
    const weightLoading = ref(false);
    const weightError = ref(null);
    const weightChart = ref(null);
    const wellnessChart = ref(null);
    const weightChartInstance = ref(null);
    const wellnessChartInstance = ref(null);

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

    const latestWellnessScore = computed(() => {
      if (!wellnessScores.value || wellnessScores.value.length === 0) return null;

      return [...wellnessScores.value].sort((a, b) =>
        new Date(b.created_at) - new Date(a.created_at)
      )[0];
    });

    // Data fetching
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

        // Generate mock wellness scores (in a real app, fetch these from an endpoint)
        generateMockWellnessScores();

        // Render charts after data is loaded
        renderCharts();
      } catch (err) {
        console.error('Error fetching progress data:', err);
        error.value = 'Failed to load progress data. Please try again.';
      } finally {
        loading.value = false;
      }
    };

    // Generate mock wellness scores based on weight entries
    const generateMockWellnessScores = () => {
      wellnessScores.value = [];

      if (!weightHistory.value || weightHistory.value.length === 0 || !profile.value) return;

      const sortedWeight = [...weightHistory.value].sort((a, b) =>
        new Date(a.recorded_at) - new Date(b.recorded_at)
      );

      sortedWeight.forEach((entry, index) => {
        // Calculate BMI score
        const bmiScore = WellnessService.calculateBMIScore(
          WellnessService.calculateBMI(profile.value.height_cm, entry.weight_kg)
        );

        // Activity score from profile
        const activityScore = WellnessService.calculateActivityScore(profile.value.activity_level);

        // Mock progress and habits scores
        const progressScore = 50 + Math.min(30, index * 2); // Improves with time
        const habitsScore = 50 + Math.sin(index * 0.5) * 15; // Fluctuates

        // Total wellness score
        const totalScore = WellnessService.calculateWellnessScore(
          bmiScore, activityScore, progressScore, habitsScore
        );

        wellnessScores.value.push({
          id: index,
          created_at: entry.recorded_at,
          total_score: totalScore,
          bmi_score: bmiScore,
          activity_score: activityScore,
          progress_score: progressScore,
          habits_score: habitsScore
        });
      });
    };

    // Render all charts
    const renderCharts = () => {
      renderWeightChart();
      renderWellnessChart();
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

      // Prepare datasets
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

      // Create chart instance
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
              display: false
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

      // Add target weight line if available
      if (profile.value?.target_weight_kg) {
        // This is a simple approach - in a real app, you might use the Chart.js Annotation plugin
        const ctx = weightChart.value.getContext('2d');
        if (ctx) {
          const yAxis = weightChartInstance.value.scales.y;
          const xAxis = weightChartInstance.value.scales.x;

          if (yAxis && xAxis) {
            const targetY = yAxis.getPixelForValue(parseFloat(profile.value.target_weight_kg));
            const startX = xAxis.left;
            const endX = xAxis.right;

            // Draw line after chart animation completes
            weightChartInstance.value.options.animation.onComplete = function() {
              ctx.save();
              ctx.beginPath();
              ctx.moveTo(startX, targetY);
              ctx.lineTo(endX, targetY);
              ctx.lineWidth = 2;
              ctx.strokeStyle = '#FF9800';
              ctx.setLineDash([5, 5]);
              ctx.stroke();
              ctx.restore();
            };
          }
        }
      }
    };

    // Render wellness score chart
    const renderWellnessChart = () => {
      if (!wellnessChart.value || !wellnessScores.value || wellnessScores.value.length === 0) return;

      if (wellnessChartInstance.value) {
        wellnessChartInstance.value.destroy();
      }

      const sortedScores = [...wellnessScores.value].sort((a, b) =>
        new Date(a.created_at) - new Date(b.created_at)
      );

      const labels = sortedScores.map(score => formatDate(score.created_at));

      wellnessChartInstance.value = new Chart(wellnessChart.value, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Total Wellness Score',
              data: sortedScores.map(score => score.total_score),
              borderColor: '#30C1B1',
              backgroundColor: 'rgba(48, 193, 177, 0.1)',
              borderWidth: 2,
              tension: 0.3,
              fill: true
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            y: {
              min: 0,
              max: 100,
              title: {
                display: true,
                text: 'Wellness Score'
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

        // Handle specific error for duplicate timestamps
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

    // Watch for changes in data to re-render charts
    watch([profile, weightHistory], () => {
      if (hasProfileData.value) {
        renderCharts();
      }
    }, { deep: true });

    // Initialize component
    onMounted(() => {
      fetchData();
    });

    return {
      loading,
      error,
      profile,
      weightHistory,
      wellnessScores,
      showAddWeightModal,
      weightLoading,
      weightError,
      weightChart,
      wellnessChart,
      hasProfileData,
      sortedWeightHistory,
      startingWeight,
      totalWeightChange,
      latestWellnessScore,
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
.progress-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
}

h1 {
  margin-top: 0;
  margin-bottom: 0.5rem;
}

.page-description {
  margin-bottom: 2rem;
  color: #666;
}

/* Loading, error and empty states */
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

/* Chart Section */
.chart-section {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.chart-container {
  height: 300px;
  margin-bottom: 1rem;
}

.chart-info {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #edf2f7;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #4a5568;
}

.info-icon {
  display: flex;
  align-items: center;
}

/* Weight History Section */
.weight-history-section {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.weight-history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.weight-summary {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.summary-item {
  min-width: 100px;
}

.summary-label {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 0.25rem;
}

.summary-value {
  font-size: 1.25rem;
  font-weight: 600;
}

.summary-value.positive {
  color: #38A169;
}

.summary-value.negative {
  color: #E53E3E;
}

/* Table styles */
.weight-history-table {
  overflow-x: auto;
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

.positive {
  color: #38A169;
}

.negative {
  color: #E53E3E;
}

.neutral {
  color: #718096;
}

.no-data-message {
  padding: 2rem;
  text-align: center;
  color: #718096;
  background-color: #F7FAFC;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.timestamp-verification {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: #E6FFFA;
  border-radius: 4px;
}

.verification-icon {
  color: #38A169;
  font-weight: bold;
  font-size: 1.25rem;
}

.verification-text {
  color: #2C7A7B;
  font-size: 0.875rem;
}

/* Wellness Score Section */
.wellness-evolution-section {
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.wellness-chart {
  height: 300px;
  margin-bottom: 2rem;
}

.wellness-components h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.125rem;
}

.component-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.5rem;
}

.component-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.component-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.component-title {
  font-weight: 500;
}

.component-percentage {
  font-size: 0.875rem;
  color: #718096;
}

.component-bar-container {
  height: 12px;
  background-color: #EDF2F7;
  border-radius: 6px;
  overflow: hidden;
}

.component-bar {
  height: 100%;
  border-radius: 6px;
  transition: width 0.3s ease;
}

.bmi-bar {
  background-color: #4299E1;
}

.activity-bar {
  background-color: #48BB78;
}

.progress-bar {
  background-color: #ED8936;
}

.habits-bar {
  background-color: #9F7AEA;
}

.component-value {
  font-size: 0.875rem;
  color: #4A5568;
  text-align: right;
}

</style>