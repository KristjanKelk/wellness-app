<!-- src/views/Activities.vue -->
<template>
  <div class="activities-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">My Activities</h1>
        <p class="page-description">Track and manage all your fitness activities in one place.</p>
      </div>
      <button class="btn btn-primary" @click="showAddModal = true">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 5V19M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Log New Activity
      </button>
    </div>

    <!-- Filters Section -->
    <div class="filters-section">
      <h2 class="section-title">Filter Activities</h2>
      <div class="filters-grid">
        <div class="filter-group">
          <label class="filter-label">From Date</label>
          <input
            type="date"
            v-model="filters.startDate"
            class="filter-input"
          />
        </div>
        <div class="filter-group">
          <label class="filter-label">To Date</label>
          <input
            type="date"
            v-model="filters.endDate"
            class="filter-input"
          />
        </div>
        <div class="filter-group">
          <label class="filter-label">Activity Type</label>
          <select v-model="filters.activityType" class="filter-select">
            <option
              v-for="type in activityTypes"
              :key="type.value"
              :value="type.value"
            >
              {{ type.label }}
            </option>
          </select>
        </div>
        <div class="filter-actions">
          <button class="btn btn-secondary" @click="fetchActivities">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 21L16.5 16.5M19 11C19 15.4183 15.4183 19 11 19C6.58172 19 3 15.4183 3 11C3 6.58172 6.58172 3 11 3C15.4183 3 19 6.58172 19 11Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Apply Filters
          </button>
          <button class="btn btn-text" @click="clearFilters">
            Clear
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading your activities...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <div class="error-icon">⚠️</div>
      <p class="error-message">{{ error }}</p>
      <button class="btn btn-secondary" @click="fetchActivities">
        Try Again
      </button>
    </div>

    <!-- Content -->
    <div v-else class="activities-content">
      <!-- Activities Found -->
      <div v-if="activities.length" class="activities-data">
        <!-- Stats Summary -->
        <div class="stats-section">
          <h2 class="section-title">Activity Summary</h2>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon activity-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2L2 7V17C2 19.21 3.79 21 6 21H18C20.21 21 22 19.21 22 17V7L12 2Z" stroke="#30C1B1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.totalActivities }}</div>
                <div class="stat-label">Total Activities</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon duration-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="#30C1B1" stroke-width="2"/>
                  <path d="M12 6V12L16 14" stroke="#30C1B1" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ formatDuration(stats.totalDuration) }}</div>
                <div class="stat-label">Total Duration</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon distance-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 11L12 14L22 4M21 12V19C21 20.1046 20.1046 21 19 21H5C3.89543 21 3 20.1046 3 19V5C3 3.89543 3.89543 3 5 3H16" stroke="#30C1B1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.totalDistance.toFixed(1) }} km</div>
                <div class="stat-label">Total Distance</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon calories-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2C13.5 2 16.5 7 16.5 10C16.5 13 14.5 15 12 15C9.5 15 7.5 13 7.5 10C7.5 7 10.5 2 12 2Z" stroke="#30C1B1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M12 15V22" stroke="#30C1B1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.totalCalories }}</div>
                <div class="stat-label">Total Calories</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon days-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2" stroke="#30C1B1" stroke-width="2"/>
                  <line x1="16" y1="2" x2="16" y2="6" stroke="#30C1B1" stroke-width="2" stroke-linecap="round"/>
                  <line x1="8" y1="2" x2="8" y2="6" stroke="#30C1B1" stroke-width="2" stroke-linecap="round"/>
                  <line x1="3" y1="10" x2="21" y2="10" stroke="#30C1B1" stroke-width="2"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.activeDays }}</div>
                <div class="stat-label">Active Days</div>
              </div>
            </div>
            <canvas ref="statsChart" class="stats-chart"></canvas>
          </div>
        </div>

        <!-- Activities Table -->
        <div class="activities-table-section">
          <h2 class="section-title">Activity History</h2>
          <div class="table-container">
            <table class="activities-table">
              <thead>
                <tr>
                  <th>Date & Time</th>
                  <th>Type</th>
                  <th>Activity Name</th>
                  <th>Duration</th>
                  <th>Distance</th>
                  <th>Calories</th>
                  <th>Notes</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="activity in activities" :key="activity.id" class="activity-row">
                  <td class="date-cell">
                    <div class="date-info">
                      <div class="date">{{ formatDate(activity.performed_at) }}</div>
                      <div class="time">{{ formatTime(activity.performed_at) }}</div>
                    </div>
                  </td>
                  <td class="type-cell">
                    <div class="activity-type-badge" :class="`type-${activity.activity_type}`">
                      <span class="type-icon">{{ getActivityIcon(activity.activity_type) }}</span>
                      <span class="type-label">{{ getActivityTypeLabel(activity.activity_type) }}</span>
                    </div>
                  </td>
                  <td class="name-cell">
                    <span class="activity-name">{{ activity.name }}</span>
                  </td>
                  <td class="duration-cell">
                    <span class="duration-value">{{ activity.duration_minutes }}m</span>
                  </td>
                  <td class="distance-cell">
                    <span v-if="activity.distance_km" class="distance-value">{{ activity.distance_km }} km</span>
                    <span v-else class="no-data">—</span>
                  </td>
                  <td class="calories-cell">
                    <span v-if="activity.calories_burned" class="calories-value">{{ activity.calories_burned }} cal</span>
                    <span v-else class="no-data">—</span>
                  </td>
                  <td class="notes-cell">
                    <span v-if="activity.notes" class="notes-text" :title="activity.notes">
                      {{ truncateNotes(activity.notes) }}
                    </span>
                    <span v-else class="no-data">—</span>
                  </td>
                  <td class="actions-cell">
                    <div class="action-buttons">
                      <button
                        class="action-btn edit-btn"
                        @click="editActivity(activity)"
                        title="Edit activity"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M11 4H4C3.46957 4 2.96086 4.21071 2.58579 4.58579C2.21071 4.96086 2 5.46957 2 6V20C2 20.5304 2.21071 21.0391 2.58579 21.4142C2.96086 21.7893 3.46957 22 4 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <path d="M18.5 2.50023C18.8978 2.1024 19.4374 1.87891 20 1.87891C20.5626 1.87891 21.1022 2.1024 21.5 2.50023C21.8978 2.89805 22.1213 3.43762 22.1213 4.00023C22.1213 4.56284 21.8978 5.1024 21.5 5.50023L12 15.0002L8 16.0002L9 12.0002L18.5 2.50023Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                      </button>
                      <button
                        class="action-btn delete-btn"
                        @click="deleteActivity(activity.id)"
                        title="Delete activity"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M3 6H5H21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <path d="M8 6V4C8 3.46957 8.21071 2.96086 8.58579 2.58579C8.96086 2.21071 9.46957 2 10 2H14C14.5304 2 15.0391 2.21071 15.4142 2.58579C15.7893 2.96086 16 3.46957 16 4V6M19 6V20C19 20.5304 18.7893 21.0391 18.4142 21.4142C18.0391 21.7893 17.5304 22 17 22H7C6.46957 22 5.96086 21.7893 5.58579 21.4142C5.21071 21.0391 5 20.5304 5 20V6H19Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="empty-state">
        <div class="empty-icon">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7V17C2 19.21 3.79 21 6 21H18C20.21 21 22 19.21 22 17V7L12 2Z" stroke="#CBD5E0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h3 class="empty-title">No Activities Found</h3>
        <p class="empty-description">
          No activities match your current filters. Try adjusting your date range or activity type.
        </p>
        <button class="btn btn-primary" @click="clearFilters">
          Clear Filters
        </button>
      </div>
    </div>

    <!-- Add Activity Modal -->
    <add-activity-modal
      v-if="showAddModal"
      :loading="modalLoading"
      :error="modalError"
      @close="onCloseModal"
      @save="onSaveActivity"
    />
  </div>
</template>

<script>
import ActivitiesService from '@/services/activities.service';
import AddActivityModal from '@/components/dashboard/AddActivityModal.vue';

export default {
  name: 'ActivitiesPage',
  components: { AddActivityModal },
  data() {
    const today = new Date().toISOString().substr(0, 10);
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);

    return {
      activities: [],
      stats: {
        totalActivities: 0,
        totalDuration: 0,
        totalDistance: 0,
        totalCalories: 0,
        activeDays: 0,
        distribution: {}
      },
      loading: false,
      error: null,
      filters: {
        startDate: weekAgo.toISOString().substr(0, 10),
        endDate: today,
        activityType: ''
      },
      activityTypes: [
        { value: '', label: 'All Types' },
        { value: 'cardio', label: 'Cardio' },
        { value: 'strength', label: 'Strength Training' },
        { value: 'flexibility', label: 'Flexibility' },
        { value: 'sports', label: 'Sports' },
        { value: 'hiit', label: 'HIIT' },
        { value: 'yoga', label: 'Yoga' },
        { value: 'other', label: 'Other' }
      ],
      showAddModal: false,
      modalLoading: false,
      modalError: null
    };
  },
  created() {
    this.fetchActivities();
  },
  methods: {
    async fetchActivities() {
      this.loading = true;
      this.error = null;
      try {
        let response;
        const { startDate, endDate, activityType } = this.filters;
        if (activityType) {
          response = await ActivitiesService.getActivitiesByType(activityType);
          this.activities = response.data.filter(activity => {
            const activityDate = activity.performed_at.substr(0, 10);
            return activityDate >= startDate && activityDate <= endDate;
          });
        } else {
          response = await ActivitiesService.getActivitiesByDateRange(startDate, endDate);
          this.activities = response.data;
        }
        this.computeStats();
      } catch (error) {
        console.error('Failed to fetch activities:', error);
        this.error = 'Failed to load activities. Please try again.';
      } finally {
        this.loading = false;
      }
    },
    computeStats() {
      const activities = this.activities;
      this.stats = {
        totalActivities: activities.length,
        totalDuration: activities.reduce((sum, activity) => sum + (activity.duration_minutes || 0), 0),
        totalDistance: activities.reduce((sum, activity) => sum + (parseFloat(activity.distance_km) || 0), 0),
        totalCalories: activities.reduce((sum, activity) => sum + (activity.calories_burned || 0), 0),
        activeDays: ActivitiesService.calculateActiveDays(activities),
        distribution: ActivitiesService.calculateActivityDistribution(activities)
      };
    },

    clearFilters() {
      const today = new Date().toISOString().substr(0, 10);
      const monthAgo = new Date();
      monthAgo.setMonth(monthAgo.getMonth() - 1);

      this.filters = {
        startDate: monthAgo.toISOString().substr(0, 10),
        endDate: today,
        activityType: ''
      };

      this.fetchActivities();
    },

    formatDate(timestamp) {
      const date = new Date(timestamp);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    },

    formatTime(timestamp) {
      const date = new Date(timestamp);
      return date.toLocaleTimeString(undefined, {
        hour: '2-digit',
        minute: '2-digit'
      });
    },

    formatDuration(minutes) {
      if (minutes < 60) {
        return `${minutes}m`;
      }
      const hours = Math.floor(minutes / 60);
      const mins = minutes % 60;
      return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
    },

    truncateNotes(notes) {
      if (!notes) return '';
      return notes.length > 30 ? notes.substring(0, 30) + '...' : notes;
    },

    getActivityIcon(type) {
      const icons = {
        cardio: '🏃',
        strength: '💪',
        flexibility: '🧘',
        sports: '⚽',
        hiit: '⚡',
        yoga: '🧘',
        other: '🏋️'
      };
      return icons[type] || '🏃';
    },

    getActivityTypeLabel(type) {
      const activity = this.activityTypes.find(a => a.value === type);
      return activity ? activity.label : type;
    },

    async deleteActivity(activityId) {
      if (!confirm('Are you sure you want to delete this activity? This action cannot be undone.')) {
        return;
      }

      try {
        await ActivitiesService.deleteActivity(activityId);
        await this.fetchActivities();
      } catch (error) {
        console.error('Failed to delete activity:', error);
        alert('Failed to delete activity. Please try again.');
      }
    },

    editActivity(activity) {
      // TODO: Implement edit functionality
      console.log('Edit functionality not yet implemented', activity);
      alert('Edit functionality will be implemented in a future update.');
    },
    onCloseModal() {
      this.showAddModal = false;
      this.modalError = null;
    },
    async onSaveActivity(activityData) {
      this.modalLoading = true;
      this.modalError = null;
      try {
        await ActivitiesService.createActivity(activityData);
        this.showAddModal = false;
        await this.fetchActivities();
      } catch (error) {
        console.error('Failed to save activity:', error);
        this.modalError = 'Failed to save activity. Please try again.';
      } finally {
        this.modalLoading = false;
      }
    }
  }
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';
</style>