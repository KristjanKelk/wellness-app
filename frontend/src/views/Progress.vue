<template>
  <div class="progress-container">
    <div class="page-header">
      <h1>Goal Tracking Progress</h1>
      <p class="page-description">Track your nutritional intake against your goals with detailed progress insights.</p>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading your progress data...</p>
    </div>

    <div v-else-if="error" class="error-container">
      <p class="error-message">{{ error }}</p>
      <button @click="fetchData" class="btn-retry">Retry</button>
    </div>

    <div v-else-if="!hasProfileData" class="empty-container">
      <p>Please complete your health profile and nutrition goals to start tracking your progress.</p>
      <router-link to="/profile" class="btn-primary">Complete Profile</router-link>
    </div>

    <div v-else class="progress-content">
      <!-- Daily Progress Section -->
      <div class="daily-progress-section">
        <h2>Today's Progress</h2>
        <div class="date-selector">
          <label for="selectedDate">Date:</label>
          <input 
            type="date" 
            id="selectedDate" 
            v-model="selectedDate" 
            @change="fetchDailyData"
            :max="getCurrentDate()"
          >
        </div>

        <div class="progress-cards">
          <!-- Calorie Progress Card -->
          <div class="progress-card calories">
            <div class="card-header">
              <h3>Daily Calories</h3>
              <div class="progress-indicator" :class="getCalorieStatusClass()">
                {{ getCalorieStatusText() }}
              </div>
            </div>
            <div class="progress-bar-container">
              <div class="progress-bar">
                <div 
                  class="progress-fill calories-fill" 
                  :style="{ width: `${getCalorieProgressPercentage()}%` }"
                ></div>
              </div>
              <div class="progress-labels">
                <span>{{ dailyData.totalCalories || 0 }} kcal</span>
                <span>{{ nutritionProfile?.calorie_target || 0 }} kcal target</span>
              </div>
            </div>
            <div class="deficit-surplus">
              <span :class="getDeficitSurplusClass()">
                {{ getDeficitSurplusText() }}
              </span>
            </div>
          </div>

          <!-- Protein Progress Card -->
          <div class="progress-card protein">
            <div class="card-header">
              <h3>Protein</h3>
              <div class="progress-indicator" :class="getProteinStatusClass()">
                {{ getProteinStatusText() }}
              </div>
            </div>
            <div class="progress-bar-container">
              <div class="progress-bar">
                <div 
                  class="progress-fill protein-fill" 
                  :style="{ width: `${getProteinProgressPercentage()}%` }"
                ></div>
              </div>
              <div class="progress-labels">
                <span>{{ Math.round(dailyData.totalProtein || 0) }}g</span>
                <span>{{ Math.round(nutritionProfile?.protein_target || 0) }}g target</span>
              </div>
            </div>
          </div>

          <!-- Carbs Progress Card -->
          <div class="progress-card carbs">
            <div class="card-header">
              <h3>Carbs</h3>
              <div class="progress-indicator" :class="getCarbsStatusClass()">
                {{ getCarbsStatusText() }}
              </div>
            </div>
            <div class="progress-bar-container">
              <div class="progress-bar">
                <div 
                  class="progress-fill carbs-fill" 
                  :style="{ width: `${getCarbsProgressPercentage()}%` }"
                ></div>
              </div>
              <div class="progress-labels">
                <span>{{ Math.round(dailyData.totalCarbs || 0) }}g</span>
                <span>{{ Math.round(nutritionProfile?.carb_target || 0) }}g target</span>
              </div>
            </div>
          </div>

          <!-- Fat Progress Card -->
          <div class="progress-card fat">
            <div class="card-header">
              <h3>Fat</h3>
              <div class="progress-indicator" :class="getFatStatusClass()">
                {{ getFatStatusText() }}
              </div>
            </div>
            <div class="progress-bar-container">
              <div class="progress-bar">
                <div 
                  class="progress-fill fat-fill" 
                  :style="{ width: `${getFatProgressPercentage()}%` }"
                ></div>
              </div>
              <div class="progress-labels">
                <span>{{ Math.round(dailyData.totalFat || 0) }}g</span>
                <span>{{ Math.round(nutritionProfile?.fat_target || 0) }}g target</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Weekly Progress Section -->
      <div class="weekly-progress-section">
        <h2>Weekly Overview</h2>
        <div class="time-range-selector">
          <label for="weekRange">Week:</label>
          <select id="weekRange" v-model="selectedWeek" @change="fetchWeeklyData">
            <option v-for="week in availableWeeks" :key="week.value" :value="week.value">
              {{ week.label }}
            </option>
          </select>
        </div>

        <div class="weekly-summary">
          <div class="summary-card">
            <h3>Average Daily Calories</h3>
            <div class="summary-value" :class="getWeeklyCalorieClass()">
              {{ Math.round(weeklyAverages.calories || 0) }} kcal
            </div>
            <div class="summary-target">
              Target: {{ nutritionProfile?.calorie_target || 0 }} kcal
            </div>
            <div class="summary-difference" :class="getWeeklyCalorieDifferenceClass()">
              {{ getWeeklyCalorieDifference() }}
            </div>
          </div>

          <div class="summary-card">
            <h3>Weekly Deficit/Surplus</h3>
            <div class="summary-value" :class="getWeeklyDeficitClass()">
              {{ Math.round(weeklyAverages.totalDeficit || 0) }} kcal
            </div>
            <div class="summary-label">Total for the week</div>
          </div>

          <div class="summary-card">
            <h3>Days on Target</h3>
            <div class="summary-value success">
              {{ weeklyStats.daysOnTarget || 0 }}/7
            </div>
            <div class="summary-label">Within ±10% of goals</div>
          </div>

          <div class="summary-card">
            <h3>Consistency Score</h3>
            <div class="summary-value" :class="getConsistencyScoreClass()">
              {{ Math.round(weeklyStats.consistencyScore || 0) }}%
            </div>
            <div class="summary-label">Goal adherence</div>
          </div>
        </div>
      </div>

      <!-- Trend Analysis Section -->
      <div class="trend-analysis-section">
        <h2>Caloric Trend Analysis</h2>
        <div class="chart-controls">
          <div class="chart-type-selector">
            <label>Chart Type:</label>
            <div class="radio-group">
              <label>
                <input type="radio" v-model="chartType" value="deficit" />
                Daily Deficit/Surplus
              </label>
              <label>
                <input type="radio" v-model="chartType" value="intake" />
                Calorie Intake vs Target
              </label>
            </div>
          </div>
          <div class="time-period-selector">
            <label for="chartPeriod">Period:</label>
            <select id="chartPeriod" v-model="chartPeriod" @change="updateChart">
              <option value="week">Last 7 Days</option>
              <option value="month">Last 30 Days</option>
              <option value="quarter">Last 3 Months</option>
            </select>
          </div>
        </div>

        <div class="chart-container">
          <canvas ref="trendChart"></canvas>
        </div>

        <div class="chart-insights">
          <div class="insight-card" v-if="trendInsights.averageDeficit">
            <h4>Average Daily Deficit</h4>
            <p :class="getDeficitInsightClass()">
              {{ Math.round(trendInsights.averageDeficit) }} kcal
              <span class="insight-note">
                {{ getDeficitInsightText() }}
              </span>
            </p>
          </div>
          
          <div class="insight-card" v-if="trendInsights.trend">
            <h4>Trend Direction</h4>
            <p :class="getTrendDirectionClass()">
              {{ getTrendDirectionText() }}
              <span class="insight-note">
                {{ getTrendInsightText() }}
              </span>
            </p>
          </div>
        </div>
      </div>

      <!-- Historical Progress Section -->
      <div class="historical-progress-section">
        <h2>Historical Progress</h2>
        <div class="progress-history-table">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Calories</th>
                <th>Target</th>
                <th>Deficit/Surplus</th>
                <th>Goal Achievement</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="day in progressHistory" :key="day.date">
                <td>{{ formatDate(day.date) }}</td>
                <td>{{ Math.round(day.totalCalories || 0) }}</td>
                <td>{{ nutritionProfile?.calorie_target || 0 }}</td>
                <td :class="getDeficitSurplusClass(day.calorieDeficitSurplus)">
                  {{ getDeficitSurplusText(day.calorieDeficitSurplus) }}
                </td>
                <td>
                  <div class="achievement-indicator" :class="getAchievementClass(day)">
                    {{ getAchievementText(day) }}
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import Chart from 'chart.js/auto';
import HealthProfileService from '@/services/health-profile_service';

export default {
  name: 'Progress',
  setup() {
    const loading = ref(true);
    const error = ref(null);
    const healthProfile = ref(null);
    const nutritionProfile = ref(null);
    const selectedDate = ref(new Date().toISOString().split('T')[0]);
    const selectedWeek = ref('current');
    const chartType = ref('deficit');
    const chartPeriod = ref('week');

    // Data refs
    const dailyData = ref({
      totalCalories: 0,
      totalProtein: 0,
      totalCarbs: 0,
      totalFat: 0,
      calorieDeficitSurplus: 0
    });

    const weeklyAverages = ref({
      calories: 0,
      protein: 0,
      carbs: 0,
      fat: 0,
      totalDeficit: 0
    });

    const weeklyStats = ref({
      daysOnTarget: 0,
      consistencyScore: 0
    });

    const progressHistory = ref([]);
    const trendInsights = ref({
      averageDeficit: 0,
      trend: null
    });

    // Chart ref
    const trendChart = ref(null);
    let chartInstance = null;

    // Computed properties
    const hasProfileData = computed(() => {
      return healthProfile.value && nutritionProfile.value;
    });

    const availableWeeks = computed(() => {
      const weeks = [];
      const today = new Date();
      
      for (let i = 0; i < 12; i++) {
        const weekStart = new Date(today);
        weekStart.setDate(today.getDate() - (today.getDay() + 7 * i));
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekStart.getDate() + 6);
        
        const label = i === 0 ? 'This Week' : 
                     i === 1 ? 'Last Week' : 
                     `${weekStart.toLocaleDateString()} - ${weekEnd.toLocaleDateString()}`;
        
        weeks.push({
          value: `week-${i}`,
          label: label,
          startDate: weekStart.toISOString().split('T')[0],
          endDate: weekEnd.toISOString().split('T')[0]
        });
      }
      
      return weeks;
    });

    // Methods
    const getCurrentDate = () => {
      return new Date().toISOString().split('T')[0];
    };

    const fetchData = async () => {
      try {
        loading.value = true;
        error.value = null;

        // Fetch health profile
        const healthResponse = await HealthProfileService.getProfile();
        healthProfile.value = healthResponse.data;

        // Fetch nutrition profile
        const nutritionResponse = await HealthProfileService.getNutritionProfile();
        nutritionProfile.value = nutritionResponse.data;

        await Promise.all([
          fetchDailyData(),
          fetchWeeklyData(),
          fetchProgressHistory()
        ]);

      } catch (err) {
        console.error('Error fetching data:', err);
        error.value = 'Failed to load progress data. Please try again.';
      } finally {
        loading.value = false;
      }
    };

    const fetchDailyData = async () => {
      try {
        const response = await HealthProfileService.getNutritionLog(selectedDate.value);
        if (response.data) {
          dailyData.value = response.data;
          
          // Calculate deficit/surplus
          if (nutritionProfile.value?.calorie_target) {
            dailyData.value.calorieDeficitSurplus = 
              (dailyData.value.totalCalories || 0) - nutritionProfile.value.calorie_target;
          }
        } else {
          // No data for this date
          dailyData.value = {
            totalCalories: 0,
            totalProtein: 0,
            totalCarbs: 0,
            totalFat: 0,
            calorieDeficitSurplus: -(nutritionProfile.value?.calorie_target || 0)
          };
        }
      } catch (err) {
        console.error('Error fetching daily data:', err);
      }
    };

    const fetchWeeklyData = async () => {
      try {
        const weekInfo = availableWeeks.value.find(w => w.value === selectedWeek.value);
        if (!weekInfo) return;

        const response = await HealthProfileService.getNutritionLogs(
          weekInfo.startDate, 
          weekInfo.endDate
        );
        
        const logs = response.data || [];
        
        if (logs.length > 0) {
          // Calculate averages
          const totals = logs.reduce((acc, log) => ({
            calories: acc.calories + (log.totalCalories || 0),
            protein: acc.protein + (log.totalProtein || 0),
            carbs: acc.carbs + (log.totalCarbs || 0),
            fat: acc.fat + (log.totalFat || 0),
            deficit: acc.deficit + (log.calorieDeficitSurplus || 0)
          }), { calories: 0, protein: 0, carbs: 0, fat: 0, deficit: 0 });

          weeklyAverages.value = {
            calories: totals.calories / logs.length,
            protein: totals.protein / logs.length,
            carbs: totals.carbs / logs.length,
            fat: totals.fat / logs.length,
            totalDeficit: totals.deficit
          };

          // Calculate stats
          const calorieTarget = nutritionProfile.value?.calorie_target || 0;
          const daysOnTarget = logs.filter(log => {
            const variance = Math.abs((log.totalCalories || 0) - calorieTarget) / calorieTarget;
            return variance <= 0.1; // Within 10%
          }).length;

          const totalVariance = logs.reduce((acc, log) => {
            const variance = Math.abs((log.totalCalories || 0) - calorieTarget) / calorieTarget;
            return acc + Math.min(variance, 1); // Cap at 100% variance
          }, 0);

          weeklyStats.value = {
            daysOnTarget,
            consistencyScore: Math.max(0, 100 - (totalVariance / logs.length * 100))
          };
        }
      } catch (err) {
        console.error('Error fetching weekly data:', err);
      }
    };

    const fetchProgressHistory = async () => {
      try {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - 30); // Last 30 days

        const response = await HealthProfileService.getNutritionLogs(
          startDate.toISOString().split('T')[0],
          endDate.toISOString().split('T')[0]
        );

        progressHistory.value = (response.data || []).map(log => ({
          ...log,
          calorieDeficitSurplus: (log.totalCalories || 0) - (nutritionProfile.value?.calorie_target || 0)
        }));

        calculateTrendInsights();
        updateChart();
      } catch (err) {
        console.error('Error fetching progress history:', err);
      }
    };

    const calculateTrendInsights = () => {
      if (progressHistory.value.length === 0) return;

      const deficits = progressHistory.value.map(day => day.calorieDeficitSurplus || 0);
      const averageDeficit = deficits.reduce((acc, def) => acc + def, 0) / deficits.length;

      // Simple trend calculation (last 7 days vs previous 7 days)
      const recentDeficits = deficits.slice(-7);
      const previousDeficits = deficits.slice(-14, -7);
      
      let trend = null;
      if (previousDeficits.length > 0) {
        const recentAvg = recentDeficits.reduce((acc, def) => acc + def, 0) / recentDeficits.length;
        const previousAvg = previousDeficits.reduce((acc, def) => acc + def, 0) / previousDeficits.length;
        
        if (Math.abs(recentAvg - previousAvg) > 50) {
          trend = recentAvg < previousAvg ? 'improving' : 'worsening';
        } else {
          trend = 'stable';
        }
      }

      trendInsights.value = {
        averageDeficit,
        trend
      };
    };

    const updateChart = async () => {
      await nextTick();
      
      if (!trendChart.value || progressHistory.value.length === 0) return;

      if (chartInstance) {
        chartInstance.destroy();
      }

      const ctx = trendChart.value.getContext('2d');
      const labels = progressHistory.value.slice(-getDaysForPeriod()).map(day => 
        new Date(day.date).toLocaleDateString()
      );

      let datasets = [];
      
      if (chartType.value === 'deficit') {
        datasets = [{
          label: 'Daily Deficit/Surplus',
          data: progressHistory.value.slice(-getDaysForPeriod()).map(day => day.calorieDeficitSurplus || 0),
          borderColor: '#30C1B1',
          backgroundColor: 'rgba(48, 193, 177, 0.1)',
          fill: true,
          tension: 0.4
        }, {
          label: 'Target (0)',
          data: new Array(labels.length).fill(0),
          borderColor: '#FF9800',
          borderDash: [5, 5],
          pointRadius: 0
        }];
      } else {
        datasets = [{
          label: 'Daily Intake',
          data: progressHistory.value.slice(-getDaysForPeriod()).map(day => day.totalCalories || 0),
          borderColor: '#4CAF50',
          backgroundColor: 'rgba(76, 175, 80, 0.1)',
          fill: false,
          tension: 0.4
        }, {
          label: 'Target',
          data: new Array(labels.length).fill(nutritionProfile.value?.calorie_target || 0),
          borderColor: '#FF9800',
          borderDash: [5, 5],
          pointRadius: 0
        }];
      }

      chartInstance = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: chartType.value === 'intake',
              title: {
                display: true,
                text: chartType.value === 'deficit' ? 'Calories (Deficit/Surplus)' : 'Calories'
              }
            },
            x: {
              title: {
                display: true,
                text: 'Date'
              }
            }
          },
          plugins: {
            legend: {
              display: true,
              position: 'top'
            },
            tooltip: {
              mode: 'index',
              intersect: false
            }
          }
        }
      });
    };

    const getDaysForPeriod = () => {
      switch (chartPeriod.value) {
        case 'week': return 7;
        case 'month': return 30;
        case 'quarter': return 90;
        default: return 7;
      }
    };

    // Progress calculation methods
    const getCalorieProgressPercentage = () => {
      if (!nutritionProfile.value?.calorie_target) return 0;
      const percentage = (dailyData.value.totalCalories || 0) / nutritionProfile.value.calorie_target * 100;
      return Math.min(percentage, 100);
    };

    const getProteinProgressPercentage = () => {
      if (!nutritionProfile.value?.protein_target) return 0;
      const percentage = (dailyData.value.totalProtein || 0) / nutritionProfile.value.protein_target * 100;
      return Math.min(percentage, 100);
    };

    const getCarbsProgressPercentage = () => {
      if (!nutritionProfile.value?.carb_target) return 0;
      const percentage = (dailyData.value.totalCarbs || 0) / nutritionProfile.value.carb_target * 100;
      return Math.min(percentage, 100);
    };

    const getFatProgressPercentage = () => {
      if (!nutritionProfile.value?.fat_target) return 0;
      const percentage = (dailyData.value.totalFat || 0) / nutritionProfile.value.fat_target * 100;
      return Math.min(percentage, 100);
    };

    // Status methods
    const getCalorieStatusClass = () => {
      const percentage = getCalorieProgressPercentage();
      if (percentage >= 90 && percentage <= 110) return 'success';
      if (percentage >= 80 && percentage <= 120) return 'warning';
      return 'danger';
    };

    const getCalorieStatusText = () => {
      const percentage = getCalorieProgressPercentage();
      if (percentage >= 90 && percentage <= 110) return 'On Target';
      if (percentage < 80) return 'Under Target';
      if (percentage > 120) return 'Over Target';
      return 'Close to Target';
    };

    const getProteinStatusClass = () => {
      const percentage = getProteinProgressPercentage();
      if (percentage >= 90) return 'success';
      if (percentage >= 70) return 'warning';
      return 'danger';
    };

    const getProteinStatusText = () => {
      const percentage = getProteinProgressPercentage();
      if (percentage >= 90) return 'Good';
      if (percentage >= 70) return 'Low';
      return 'Very Low';
    };

    const getCarbsStatusClass = () => {
      const percentage = getCarbsProgressPercentage();
      if (percentage >= 80 && percentage <= 120) return 'success';
      if (percentage >= 60 && percentage <= 140) return 'warning';
      return 'danger';
    };

    const getCarbsStatusText = () => {
      const percentage = getCarbsProgressPercentage();
      if (percentage >= 80 && percentage <= 120) return 'Balanced';
      if (percentage < 60) return 'Low';
      return 'High';
    };

    const getFatStatusClass = () => {
      const percentage = getFatProgressPercentage();
      if (percentage >= 80 && percentage <= 120) return 'success';
      if (percentage >= 60 && percentage <= 140) return 'warning';
      return 'danger';
    };

    const getFatStatusText = () => {
      const percentage = getFatProgressPercentage();
      if (percentage >= 80 && percentage <= 120) return 'Balanced';
      if (percentage < 60) return 'Low';
      return 'High';
    };

    const getDeficitSurplusClass = (value = null) => {
      const deficit = value !== null ? value : dailyData.value.calorieDeficitSurplus;
      if (deficit <= -200) return 'success'; // Good deficit
      if (deficit >= -50 && deficit <= 50) return 'warning'; // Near maintenance
      if (deficit > 200) return 'danger'; // Surplus
      return 'neutral';
    };

    const getDeficitSurplusText = (value = null) => {
      const deficit = value !== null ? value : dailyData.value.calorieDeficitSurplus;
      if (deficit < 0) return `${Math.abs(Math.round(deficit))} kcal deficit`;
      if (deficit > 0) return `${Math.round(deficit)} kcal surplus`;
      return 'At maintenance';
    };

    // Weekly methods
    const getWeeklyCalorieClass = () => {
      if (!nutritionProfile.value?.calorie_target) return 'neutral';
      const target = nutritionProfile.value.calorie_target;
      const actual = weeklyAverages.value.calories;
      const percentage = actual / target;
      
      if (percentage >= 0.9 && percentage <= 1.1) return 'success';
      if (percentage >= 0.8 && percentage <= 1.2) return 'warning';
      return 'danger';
    };

    const getWeeklyCalorieDifference = () => {
      if (!nutritionProfile.value?.calorie_target) return '';
      const difference = weeklyAverages.value.calories - nutritionProfile.value.calorie_target;
      if (Math.abs(difference) < 10) return 'On target';
      return difference > 0 ? `+${Math.round(difference)} kcal` : `${Math.round(difference)} kcal`;
    };

    const getWeeklyCalorieDifferenceClass = () => {
      if (!nutritionProfile.value?.calorie_target) return 'neutral';
      const difference = weeklyAverages.value.calories - nutritionProfile.value.calorie_target;
      if (Math.abs(difference) < 50) return 'success';
      if (Math.abs(difference) < 100) return 'warning';
      return 'danger';
    };

    const getWeeklyDeficitClass = () => {
      const deficit = weeklyAverages.value.totalDeficit;
      if (deficit <= -1000) return 'success'; // Good weekly deficit
      if (deficit >= -300 && deficit <= 300) return 'warning'; // Near maintenance
      return 'danger'; // Surplus
    };

    const getConsistencyScoreClass = () => {
      const score = weeklyStats.value.consistencyScore;
      if (score >= 80) return 'success';
      if (score >= 60) return 'warning';
      return 'danger';
    };

    // Trend insight methods
    const getDeficitInsightClass = () => {
      const deficit = trendInsights.value.averageDeficit;
      if (deficit <= -200 && deficit >= -500) return 'success';
      if (deficit > -200 && deficit < 0) return 'warning';
      return 'danger';
    };

    const getDeficitInsightText = () => {
      const deficit = trendInsights.value.averageDeficit;
      if (deficit <= -400) return 'Aggressive deficit - monitor for sustainability';
      if (deficit <= -200) return 'Healthy deficit for weight loss';
      if (deficit < 0) return 'Mild deficit';
      if (deficit === 0) return 'At maintenance calories';
      return 'Caloric surplus';
    };

    const getTrendDirectionClass = () => {
      const trend = trendInsights.value.trend;
      if (trend === 'improving') return 'success';
      if (trend === 'stable') return 'warning';
      return 'danger';
    };

    const getTrendDirectionText = () => {
      const trend = trendInsights.value.trend;
      if (trend === 'improving') return 'Improving';
      if (trend === 'stable') return 'Stable';
      if (trend === 'worsening') return 'Needs Attention';
      return 'Unknown';
    };

    const getTrendInsightText = () => {
      const trend = trendInsights.value.trend;
      if (trend === 'improving') return 'Your deficit is getting better!';
      if (trend === 'stable') return 'Consistent with your goals';
      if (trend === 'worsening') return 'Consider adjusting your approach';
      return '';
    };

    // Achievement methods
    const getAchievementClass = (day) => {
      const target = nutritionProfile.value?.calorie_target || 0;
      const actual = day.totalCalories || 0;
      const variance = Math.abs(actual - target) / target;
      
      if (variance <= 0.05) return 'excellent'; // Within 5%
      if (variance <= 0.1) return 'good'; // Within 10%
      if (variance <= 0.2) return 'fair'; // Within 20%
      return 'poor';
    };

    const getAchievementText = (day) => {
      const target = nutritionProfile.value?.calorie_target || 0;
      const actual = day.totalCalories || 0;
      const variance = Math.abs(actual - target) / target;
      
      if (variance <= 0.05) return 'Excellent';
      if (variance <= 0.1) return 'Good';
      if (variance <= 0.2) return 'Fair';
      return 'Needs Work';
    };

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString();
    };

    // Watchers
    watch([chartType, chartPeriod], () => {
      updateChart();
    });

    watch(selectedWeek, () => {
      fetchWeeklyData();
    });

    // Lifecycle
    onMounted(() => {
      fetchData();
    });

    return {
      loading,
      error,
      healthProfile,
      nutritionProfile,
      selectedDate,
      selectedWeek,
      chartType,
      chartPeriod,
      dailyData,
      weeklyAverages,
      weeklyStats,
      progressHistory,
      trendInsights,
      trendChart,
      hasProfileData,
      availableWeeks,
      
      // Methods
      getCurrentDate,
      fetchData,
      fetchDailyData,
      fetchWeeklyData,
      fetchProgressHistory,
      updateChart,
      
      // Progress calculations
      getCalorieProgressPercentage,
      getProteinProgressPercentage,
      getCarbsProgressPercentage,
      getFatProgressPercentage,
      
      // Status methods
      getCalorieStatusClass,
      getCalorieStatusText,
      getProteinStatusClass,
      getProteinStatusText,
      getCarbsStatusClass,
      getCarbsStatusText,
      getFatStatusClass,
      getFatStatusText,
      getDeficitSurplusClass,
      getDeficitSurplusText,
      
      // Weekly methods
      getWeeklyCalorieClass,
      getWeeklyCalorieDifference,
      getWeeklyCalorieDifferenceClass,
      getWeeklyDeficitClass,
      getConsistencyScoreClass,
      
      // Trend insight methods
      getDeficitInsightClass,
      getDeficitInsightText,
      getTrendDirectionClass,
      getTrendDirectionText,
      getTrendInsightText,
      
      // Achievement methods
      getAchievementClass,
      getAchievementText,
      formatDate
    };
  }
};
</script>

<style scoped>
.progress-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-header h1 {
  color: #2c3e50;
  margin-bottom: 10px;
  font-size: 2.5rem;
  font-weight: 600;
}

.page-description {
  color: #7f8c8d;
  font-size: 1.1rem;
  max-width: 600px;
  margin: 0 auto;
}

.loading-container, .error-container, .empty-container {
  text-align: center;
  padding: 60px 20px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #30C1B1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #e74c3c;
  margin-bottom: 20px;
  font-size: 1.1rem;
}

.btn-retry, .btn-primary {
  background-color: #30C1B1;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  text-decoration: none;
  display: inline-block;
  transition: background-color 0.3s ease;
}

.btn-retry:hover, .btn-primary:hover {
  background-color: #27a496;
}

.progress-content {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

/* Daily Progress Section */
.daily-progress-section {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.daily-progress-section h2 {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 1.8rem;
  font-weight: 600;
}

.date-selector {
  margin-bottom: 30px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.date-selector label {
  font-weight: 500;
  color: #555;
}

.date-selector input {
  padding: 8px 12px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1rem;
}

.progress-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.progress-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  border-left: 4px solid #30C1B1;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.progress-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.progress-card.calories { border-left-color: #e74c3c; }
.progress-card.protein { border-left-color: #3498db; }
.progress-card.carbs { border-left-color: #f39c12; }
.progress-card.fat { border-left-color: #9b59b6; }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.card-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.2rem;
  font-weight: 600;
}

.progress-indicator {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
}

.progress-indicator.success { background: #d4edda; color: #155724; }
.progress-indicator.warning { background: #fff3cd; color: #856404; }
.progress-indicator.danger { background: #f8d7da; color: #721c24; }

.progress-bar-container {
  margin-bottom: 10px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.calories-fill { background: linear-gradient(90deg, #e74c3c, #c0392b); }
.protein-fill { background: linear-gradient(90deg, #3498db, #2980b9); }
.carbs-fill { background: linear-gradient(90deg, #f39c12, #e67e22); }
.fat-fill { background: linear-gradient(90deg, #9b59b6, #8e44ad); }

.progress-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: #666;
}

.deficit-surplus {
  text-align: center;
  font-weight: 600;
  font-size: 0.95rem;
}

.deficit-surplus .success { color: #27ae60; }
.deficit-surplus .warning { color: #f39c12; }
.deficit-surplus .danger { color: #e74c3c; }
.deficit-surplus .neutral { color: #7f8c8d; }

/* Weekly Progress Section */
.weekly-progress-section {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.weekly-progress-section h2 {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 1.8rem;
  font-weight: 600;
}

.time-range-selector {
  margin-bottom: 30px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.time-range-selector label {
  font-weight: 500;
  color: #555;
}

.time-range-selector select {
  padding: 8px 12px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1rem;
  background: white;
}

.weekly-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}

.summary-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  border-top: 4px solid #30C1B1;
}

.summary-card h3 {
  margin: 0 0 15px 0;
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
}

.summary-value {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 8px;
}

.summary-value.success { color: #27ae60; }
.summary-value.warning { color: #f39c12; }
.summary-value.danger { color: #e74c3c; }

.summary-target, .summary-label {
  color: #7f8c8d;
  font-size: 0.9rem;
  margin-bottom: 5px;
}

.summary-difference {
  font-weight: 600;
  font-size: 0.95rem;
}

.summary-difference.success { color: #27ae60; }
.summary-difference.warning { color: #f39c12; }
.summary-difference.danger { color: #e74c3c; }

/* Trend Analysis Section */
.trend-analysis-section {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.trend-analysis-section h2 {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 1.8rem;
  font-weight: 600;
}

.chart-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 30px;
  margin-bottom: 30px;
  align-items: center;
}

.chart-type-selector label:first-child,
.time-period-selector label {
  font-weight: 500;
  color: #555;
  margin-right: 10px;
}

.radio-group {
  display: flex;
  gap: 15px;
}

.radio-group label {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  color: #666;
}

.time-period-selector select {
  padding: 8px 12px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1rem;
  background: white;
}

.chart-container {
  height: 400px;
  margin-bottom: 30px;
  position: relative;
}

.chart-insights {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.insight-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  border-left: 4px solid #30C1B1;
}

.insight-card h4 {
  margin: 0 0 10px 0;
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
}

.insight-card p {
  margin: 0;
  font-weight: 600;
  font-size: 1.1rem;
}

.insight-card p.success { color: #27ae60; }
.insight-card p.warning { color: #f39c12; }
.insight-card p.danger { color: #e74c3c; }

.insight-note {
  display: block;
  font-weight: normal;
  font-size: 0.9rem;
  color: #666;
  margin-top: 5px;
}

/* Historical Progress Section */
.historical-progress-section {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.historical-progress-section h2 {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 1.8rem;
  font-weight: 600;
}

.progress-history-table {
  overflow-x: auto;
}

.progress-history-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

.progress-history-table th,
.progress-history-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.progress-history-table th {
  background: #f8f9fa;
  color: #2c3e50;
  font-weight: 600;
  position: sticky;
  top: 0;
}

.progress-history-table tr:hover {
  background: #f8f9fa;
}

.achievement-indicator {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
}

.achievement-indicator.excellent { background: #d4edda; color: #155724; }
.achievement-indicator.good { background: #d1ecf1; color: #0c5460; }
.achievement-indicator.fair { background: #fff3cd; color: #856404; }
.achievement-indicator.poor { background: #f8d7da; color: #721c24; }

/* Responsive Design */
@media (max-width: 768px) {
  .progress-container {
    padding: 15px;
  }
  
  .page-header h1 {
    font-size: 2rem;
  }
  
  .progress-cards {
    grid-template-columns: 1fr;
  }
  
  .weekly-summary {
    grid-template-columns: 1fr;
  }
  
  .chart-controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .radio-group {
    flex-direction: column;
    gap: 10px;
  }
  
  .chart-insights {
    grid-template-columns: 1fr;
  }
  
  .progress-history-table {
    font-size: 0.85rem;
  }
  
  .progress-history-table th,
  .progress-history-table td {
    padding: 8px;
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 1.75rem;
  }
  
  .chart-container {
    height: 300px;
  }
  
  .daily-progress-section,
  .weekly-progress-section,
  .trend-analysis-section,
  .historical-progress-section {
    padding: 20px;
  }
}
</style>