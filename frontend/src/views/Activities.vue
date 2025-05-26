<!-- src/views/Activities.vue -->
<template>
  <div class="activities-page">
    <!-- Page Header -->
    <div class="page-header">
      <h1>My Activities</h1>
      <button class="btn btn-primary" @click="showAddModal = true">
        Log New Activity
      </button>
    </div>

    <!-- Filters -->
    <div class="filters">
      <label>
        From
        <input type="date" v-model="filters.startDate" />
      </label>
      <label>
        To
        <input type="date" v-model="filters.endDate" />
      </label>
      <label>
        Type
        <select v-model="filters.activityType">
          <option
            v-for="type in activityTypes"
            :key="type.value"
            :value="type.value"
          >
            {{ type.label }}
          </option>
        </select>
      </label>
      <button class="btn btn-secondary" @click="fetchActivities">
        Filter
      </button>
    </div>

    <!-- Loading / Error / Content -->
    <div v-if="loading" class="loading">
      Loading activities…
    </div>
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    <div v-else>
      <!-- If we have activities, show stats + table -->
      <div v-if="activities.length">
        <!-- Stats Summary -->
        <div class="stats">
          <div>Total Activities: {{ stats.totalActivities }}</div>
          <div>Total Duration: {{ stats.totalDuration }} min</div>
          <div>Total Distance: {{ stats.totalDistance }} km</div>
          <div>Total Calories: {{ stats.totalCalories }}</div>
          <div>Active Days: {{ stats.activeDays }}</div>
        </div>

        <!-- Activities Table -->
        <table class="activities-table">
          <thead>
            <tr>
              <th>Date</th><th>Type</th><th>Name</th>
              <th>Duration</th><th>Distance</th>
              <th>Calories</th><th>Notes</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="act in activities" :key="act.id">
              <td>{{ formatDate(act.performed_at) }}</td>
              <td>{{ act.activity_type }}</td>
              <td>{{ act.name }}</td>
              <td>{{ act.duration_minutes }}m</td>
              <td>{{ act.distance_km ?? '-' }}</td>
              <td>{{ act.calories_burned ?? '-' }}</td>
              <td>{{ act.notes ?? '-' }}</td>
              <td>
                <button class="btn btn-sm" @click="editActivity(act)">
                  Edit
                </button>
                <button
                  class="btn btn-sm btn-danger"
                  @click="deleteActivity(act.id)"
                >
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- No activities -->
      <div v-else class="empty">
        No activities found for the selected filters.
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
    const today = new Date().toISOString().substr(0,10);
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    return {
      activities: [],
      stats: null,
      loading: false,
      error: null,
      filters: {
        startDate: weekAgo.toISOString().substr(0,10),
        endDate: today,
        activityType: ''
      },
      activityTypes: [
        { value: '', label: 'All Types' },
        { value: 'cardio', label: 'Cardio' },
        { value: 'strength', label: 'Strength' },
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
        let resp;
        const { startDate, endDate, activityType } = this.filters;
        if (activityType) {
          resp = await ActivitiesService.getActivitiesByType(activityType);
          this.activities = resp.data.filter(a => {
            const d = a.performed_at.substr(0,10);
            return d >= startDate && d <= endDate;
          });
        } else {
          resp = await ActivitiesService.getActivitiesByDateRange(startDate, endDate);
          this.activities = resp.data;
        }
        this.computeStats();
      } catch (e) {
        console.error(e);
        this.error = 'Failed to load activities.';
      } finally {
        this.loading = false;
      }
    },
    computeStats() {
      const acts = this.activities;
      this.stats = {
        totalActivities: acts.length,
        totalDuration:   acts.reduce((sum,a) => sum + (a.duration_minutes||0), 0),
        totalDistance:   acts.reduce((sum,a) => sum + (a.distance_km||0), 0),
        totalCalories:   acts.reduce((sum,a) => sum + (a.calories_burned||0), 0),
        activeDays:      ActivitiesService.calculateActiveDays(acts),
        distribution:    ActivitiesService.calculateActivityDistribution(acts)
      };
    },
    formatDate(ts) {
      return new Date(ts).toLocaleDateString();
    },
    async deleteActivity(id) {
      if (!confirm('Delete this activity?')) return;
      await ActivitiesService.deleteActivity(id);
      await this.fetchActivities();
    },
    editActivity(act) {
      console.log('Edit not yet implemented', act);
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
      } catch (e) {
        console.error(e);
        this.modalError = 'Failed to save activity.';
      } finally {
        this.modalLoading = false;
      }
    }
  }
};
</script>

<style scoped>
.activities-page { padding: 2rem; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.filters { display: flex; gap: 1rem; margin-bottom: 1rem; align-items: center; }
.loading, .error, .empty { text-align: center; margin: 2rem 0; }
.stats { display: flex; gap: 1.5rem; margin-bottom: 1rem; }
.activities-table { width: 100%; border-collapse: collapse; margin-bottom: 1rem; }
.activities-table th, .activities-table td { border: 1px solid #ddd; padding: 0.5rem; text-align: left; }
</style>
