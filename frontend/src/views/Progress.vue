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
      <!-- Chart Controls -->
      <div class="chart-controls">
        <div class="time-range-selector">
          <label for="timeRange">Time Range:</label>
          <select id="timeRange" v-model="selectedTimeRange" @change="updateChart">
            <option value="all">All Time</option>
            <option value="year">Last Year</option>
            <option value="6months">Last 6 Months</option>
            <option value="3months">Last 3 Months</option>
            <option value="month">Last Month</option>
            <option value="week">Last Week</option>
          </select>
        </div>

      </div>

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
          <div v-if="showTrendline" class="info-item">
            <div class="info-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 20L21 4" stroke="#9C27B0" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="info-text">Purple line shows the overall trend of your weight change</div>
          </div>
        </div>
      </div>

      <!-- Progress Summary Section -->
      <div class="progress-summary-section" v-if="hasEnoughData">
        <h2>Progress Summary</h2>
        <div class="summary-cards">
          <div class="summary-card">
            <h3>Weekly Change</h3>
            <div class="summary-value" :class="getChangeClass(weeklyChange)">
              {{ weeklyChange > 0 ? '+' : '' }}{{ weeklyChange }} kg
            </div>
            <div class="summary-label">Average change per week</div>
          </div>

          <div class="summary-card">
            <h3>Monthly Change</h3>
            <div class="summary-value" :class="getChangeClass(monthlyChange)">
              {{ monthlyChange > 0 ? '+' : '' }}{{ monthlyChange }} kg
            </div>
            <div class="summary-label">Average change per month</div>
          </div>

          <div class="summary-card">
            <h3>Projected Goal</h3>
            <div class="summary-value">
              {{ projectedGoal }}
            </div>
            <div class="summary-label">Based on current progress</div>
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
                <td :class="getChangeClass(getWeightChange(entry, index))">
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
import {computed, nextTick, onMounted, onUnmounted, ref, watch} from 'vue';
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

    // Chart configuration options
    const selectedTimeRange = ref('all');
    const selectedChartType = ref('line');
    const showTrendline = ref(true);

    // Computed properties
    const hasProfileData = computed(() => {
      return profile.value && profile.value.height_cm && profile.value.weight_kg;
    });

    const hasEnoughData = computed(() => {
      return weightHistory.value && weightHistory.value.length > 2;
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
      return (currentWeight - startingWeight.value).toFixed(1);
    });

    // Calculate weekly and monthly changes
    const weeklyChange = computed(() => {
      if (!hasEnoughData.value) return '0.0';
      const changeRate = calculateChangeRate(7); // 7 days
      return changeRate.toFixed(1);
    });

    const monthlyChange = computed(() => {
      if (!hasEnoughData.value) return '0.0';
      const changeRate = calculateChangeRate(30); // 30 days
      return changeRate.toFixed(1);
    });

    // Projected goal date based on current trend
    const projectedGoal = computed(() => {
      if (!hasEnoughData.value || !profile.value?.target_weight_kg) return 'Not available';

      const currentWeight = parseFloat(profile.value.weight_kg);
      const targetWeight = parseFloat(profile.value.target_weight_kg);
      const dailyChange = calculateChangeRate(1);

      // If no change or wrong direction, cannot project
      if (Math.abs(dailyChange) < 0.01 ||
          (profile.value.fitness_goal === 'weight_loss' && dailyChange >= 0) ||
          (profile.value.fitness_goal === 'muscle_gain' && dailyChange <= 0)) {
        return 'Not on track';
      }

      const daysToGoal = Math.abs(Math.round((targetWeight - currentWeight) / dailyChange));

      if (daysToGoal > 365 * 2) {
        return 'Long-term goal';
      }

      const date = new Date();
      date.setDate(date.getDate() + daysToGoal);

      return `~${formatDate(date)} (${daysToGoal} days)`;
    });

    // Calculate weight change rate (per day specified)
    const calculateChangeRate = (daysInterval) => {
      if (!weightHistory.value || weightHistory.value.length < 2) return 0;

      // Get chronologically sorted data
      const sorted = [...weightHistory.value].sort((a, b) =>
        new Date(a.recorded_at) - new Date(b.recorded_at)
      );

      // Get oldest and newest entries
      const oldest = sorted[0];
      const newest = sorted[sorted.length - 1];

      // Calculate days between first and last entry
      const firstDate = new Date(oldest.recorded_at);
      const lastDate = new Date(newest.recorded_at);
      const daysDiff = (lastDate - firstDate) / (1000 * 60 * 60 * 24);

      if (daysDiff < 1) return 0; // Avoid division by zero or if all entries are same day

      // Calculate change per day, then multiply by specified interval
      const weightDiff = parseFloat(newest.weight_kg) - parseFloat(oldest.weight_kg);
      const ratePerDay = weightDiff / daysDiff;

      return ratePerDay * daysInterval;
    };

    // Calculate trend line data
    const calculateTrendLine = (entries) => {
      if (entries.length < 2) return null;

      // Extract x (timestamps) and y (weight) values
      const timestamps = entries.map(entry => new Date(entry.recorded_at).getTime());
      const weights = entries.map(entry => parseFloat(entry.weight_kg));

      // Calculate means
      const meanX = timestamps.reduce((sum, val) => sum + val, 0) / timestamps.length;
      const meanY = weights.reduce((sum, val) => sum + val, 0) / weights.length;

      // Calculate numerator and denominator for slope
      let numerator = 0;
      let denominator = 0;

      for (let i = 0; i < timestamps.length; i++) {
        numerator += (timestamps[i] - meanX) * (weights[i] - meanY);
        denominator += (timestamps[i] - meanX) * (timestamps[i] - meanX);
      }

      // Calculate slope and intercept
      const slope = denominator !== 0 ? numerator / denominator : 0;
      const intercept = meanY - slope * meanX;

      // Calculate trend values for first and last points
      const firstPoint = {
        x: new Date(timestamps[0]),
        y: slope * timestamps[0] + intercept
      };

      const lastPoint = {
        x: new Date(timestamps[timestamps.length - 1]),
        y: slope * timestamps[timestamps.length - 1] + intercept
      };

      return [firstPoint, lastPoint];
    };

    // Updated fetchData function to ensure chart renders on initial load
    const fetchData = async () => {
      loading.value = true;
      error.value = null;

      try {
        const profileResponse = await HealthProfileService.getHealthProfile();
        profile.value = profileResponse.data;

        const weightResponse = await HealthProfileService.getWeightHistory();
        weightHistory.value = weightResponse.data;

        // Wait for the DOM to update before rendering chart
        await nextTick();

        // Only try to render chart if we have data
        if (weightHistory.value && weightHistory.value.length > 0) {
          const filteredEntries = filterEntriesByTimeRange();
          renderChart(filteredEntries);
        }
      } catch (err) {
        console.error('Error fetching progress data:', err);
        error.value = 'Failed to load progress data. Please try again.';
      } finally {
        loading.value = false;
      }
    };

    // Initialize component with immediate rendering
    onMounted(() => {
      // Fetch data immediately
      fetchData();

      // Add resize handler for responsive charts
      const resizeHandler = () => {
        if (weightChartInstance.value) {
          weightChartInstance.value.resize();
        }
      };

      window.addEventListener('resize', resizeHandler);

      // Clean up on unmount
      onUnmounted(() => {
        window.removeEventListener('resize', resizeHandler);
        if (weightChartInstance.value) {
          weightChartInstance.value.destroy();
        }
      });
    });

    // Update chart based on selected options
    const updateChart = () => {
      if (!weightChart.value || !weightHistory.value || weightHistory.value.length === 0) return;

      if (weightChartInstance.value) {
        weightChartInstance.value.destroy();
      }

      const filteredEntries = filterEntriesByTimeRange();
      if (filteredEntries.length === 0) return;

      renderChart(filteredEntries);
    };

    // Filter entries based on selected time range
    const filterEntriesByTimeRange = () => {
      if (!weightHistory.value || weightHistory.value.length === 0) return [];

      // Sort by date
      const sortedEntries = [...weightHistory.value].sort((a, b) =>
        new Date(a.recorded_at) - new Date(b.recorded_at)
      );

      if (selectedTimeRange.value === 'all') {
        return sortedEntries;
      }

      // Calculate cut-off date based on selected range
      const now = new Date();
      let cutoffDate = new Date();

      switch (selectedTimeRange.value) {
        case 'year':
          cutoffDate.setFullYear(now.getFullYear() - 1);
          break;
        case '6months':
          cutoffDate.setMonth(now.getMonth() - 6);
          break;
        case '3months':
          cutoffDate.setMonth(now.getMonth() - 3);
          break;
        case 'month':
          cutoffDate.setMonth(now.getMonth() - 1);
          break;
        case 'week':
          cutoffDate.setDate(now.getDate() - 7);
          break;
        default:
          return sortedEntries;
      }

      // Filter entries by date
      return sortedEntries.filter(entry =>
        new Date(entry.recorded_at) >= cutoffDate
      );
    };

    // Render weight progress chart
    // Fix the renderChart function to address the bar chart error and initial loading
    const renderChart = (entries) => {
      if (!weightChart.value || !entries || entries.length === 0) return;

      // Destroy existing chart instance if it exists
      if (weightChartInstance.value) {
        weightChartInstance.value.destroy();
      }

      // Format dates for labels
      const labels = entries.map(entry => formatDate(entry.recorded_at));
      const weightData = entries.map(entry => parseFloat(entry.weight_kg));

      // Basic configuration common to all chart types
      const config = {
        type: selectedChartType.value,
        data: {
          labels: labels,
          datasets: []
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
                label: function(context) {
                  let label = context.dataset.label || '';
                  if (label) {
                    label += ': ';
                  }
                  if (context.parsed.y !== null) {
                    label += context.parsed.y.toFixed(1) + ' kg';
                  }
                  return label;
                }
              }
            }
          },
          scales: {
            x: {
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
      };

      // Add appropriate datasets based on chart type

      // 1. Weight dataset
      const weightDataset = {
        label: 'Weight (kg)',
        data: weightData,
        borderColor: '#30C1B1',
        backgroundColor: selectedChartType.value === 'line' ? 'rgba(48, 193, 177, 0.1)' : 'rgba(48, 193, 177, 0.7)',
        borderWidth: 2,
        tension: 0.3,
        fill: selectedChartType.value === 'line'
      };

      // 2. Target weight dataset (only shown as line)
      let targetDataset = null;
      if (profile.value?.target_weight_kg) {
        targetDataset = {
          label: 'Target Weight',
          data: Array(entries.length).fill(parseFloat(profile.value.target_weight_kg)),
          borderColor: '#FF9800',
          backgroundColor: 'transparent',
          borderWidth: 2,
          borderDash: [5, 5],
          pointRadius: 0,
          type: 'line', // Force line chart for target weight
          order: 1 // Draw lines above bars
        };
      }

      // 3. Trendline dataset (only shown as line)
      let trendDataset = null;
      if (showTrendline.value && entries.length >= 2) {
        const trendLine = calculateTrendLine(entries);

        if (trendLine) {
          // Create array with nulls and only first and last points for a straight line
          const trendData = Array(entries.length).fill(null);
          trendData[0] = trendLine[0].y;
          trendData[trendData.length - 1] = trendLine[1].y;

          trendDataset = {
            label: 'Trend',
            data: trendData,
            borderColor: '#9C27B0',
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0,
            spanGaps: true, // Connect points with line despite null values
            type: 'line', // Force line chart for trend line
            order: 0 // Draw on top
          };
        }
      }

      // Add datasets to config
      config.data.datasets.push(weightDataset);
      if (targetDataset) config.data.datasets.push(targetDataset);
      if (trendDataset) config.data.datasets.push(trendDataset);

      // Create new chart instance
      weightChartInstance.value = new Chart(weightChart.value, config);
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

    const getChangeClass = (change) => {
      if (change === '—' || change === 0 || change === '0' || change === '0.0') return 'neutral';

      let numChange = 0;
      if (typeof change === 'string') {
        numChange = parseFloat(change);
      } else {
        numChange = change;
      }

      if (profile.value && profile.value.fitness_goal) {
        if (profile.value.fitness_goal === 'weight_loss') {
          return numChange < 0 ? 'positive' : 'negative';
        } else if (profile.value.fitness_goal === 'muscle_gain') {
          return numChange > 0 ? 'positive' : 'negative';
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

    // Watch for changes in chart configuration
    watch([selectedChartType, showTrendline], () => {
      updateChart();
    });

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
      hasEnoughData,
      sortedWeightHistory,
      startingWeight,
      totalWeightChange,
      weeklyChange,
      monthlyChange,
      projectedGoal,
      selectedTimeRange,
      selectedChartType,
      showTrendline,
      fetchData,
      updateChart,
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

// Chart controls
.chart-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;

  .time-range-selector,
  .chart-type-selector,
  .comparison-selector {
    display: flex;
    align-items: center;
    gap: 0.5rem;

    label {
      font-weight: 500;
      margin-bottom: 0;
    }

    select {
      padding: 0.5rem;
      border-radius: 4px;
      border: 1px solid #ddd;
      background-color: white;
    }
  }
}

// Progress summary
.progress-summary-section {
  margin-bottom: 2rem;

  .summary-cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;

    .summary-card {
      padding: 1.5rem;
      background-color: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      text-align: center;

      h3 {
        font-size: 1rem;
        margin-bottom: 0.5rem;
      }

      .summary-value {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;

        &.positive {
          color: #4caf50;
        }

        &.negative {
          color: #f44336;
        }

        &.neutral {
          color: #757575;
        }
      }

      .summary-label {
        font-size: 0.9rem;
        color: #757575;
      }
    }
  }
}

// Chart section styling
.chart-section {
  margin-bottom: 2rem;

  .chart-container {
    background-color: white;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    height: 400px;
  }

  .chart-info {
    margin-top: 1rem;
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;

    .info-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background-color: #f8f9fa;
      padding: 0.5rem 1rem;
      border-radius: 4px;

      .info-text {
        font-size: 0.9rem;
      }
    }
  }
}

// Weight history table styling
.weight-history-section {
  .weight-history-table {
    margin-top: 1rem;
    overflow-x: auto;

    table {
      width: 100%;
      border-collapse: collapse;

      th, td {
        padding: 0.75rem;
        text-align: left;
        border-bottom: 1px solid #ddd;
      }

      th {
        background-color: #f8f9fa;
        font-weight: 600;
      }

      tr:hover {
        background-color: #f8f9fa;
      }

      td.positive {
        color: #4caf50;
        font-weight: 500;
      }

      td.negative {
        color: #f44336;
        font-weight: 500;
      }
    }
  }
}

// Empty state styling
.empty-container {
  text-align: center;
  padding: 3rem;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  p {
    margin-bottom: 1.5rem;
    color: #757575;
  }
}

// Error and loading states
.error-container,
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid rgba(0, 0, 0, 0.1);
    border-top-color: #30C1B1;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }

  .error-message {
    color: #f44336;
    margin-bottom: 1rem;
  }

  .btn-retry {
    padding: 0.5rem 1rem;
    background-color: #f44336;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;

    &:hover {
      background-color: darken(#f44336, 10%);
    }
  }
}

.weight-history-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;

  .weight-summary {
    display: flex;
    flex-wrap: wrap;
    gap: 1.5rem;

    .summary-item {
      .summary-label {
        font-size: 0.9rem;
        color: #757575;
      }

      .summary-value {
        font-size: 1.2rem;
        font-weight: 600;

        &.positive {
          color: #4caf50;
        }

        &.negative {
          color: #f44336;
        }
      }
    }
  }
}

.no-data-message {
  text-align: center;
  padding: 2rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 1.5rem;

  p {
    color: #757575;
  }
}

.timestamp-verification {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: #e8f5e9;
  padding: 0.75rem 1rem;
  border-radius: 4px;
  margin-top: 1.5rem;

  .verification-icon {
    color: #4caf50;
    font-weight: bold;
  }

  .verification-text {
    font-size: 0.9rem;
    color: #2e7d32;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>