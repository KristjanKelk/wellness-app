<template>
  <div class="card">
    <h2>Activity Level</h2>
    <div v-if="profile && profile.activity_level" class="activity-container">
      <div class="activity-level">{{ activityLevelDisplay }}</div>
      <p>{{ activityDescription }}</p>
      <div class="activity-suggestions">
        <h3>Suggestions</h3>
        <ul>
          <li v-for="(suggestion, index) in activitySuggestions" :key="index">
            {{ suggestion }}
          </li>
        </ul>
      </div>
    </div>
    <div v-else>
      <p>Your activity tracking will appear once you've updated your profile.</p>
      <router-link to="/profile" class="btn btn-primary">Update Profile</router-link>
    </div>
  </div>
</template>

<script>
import WellnessService from '../../services/wellness-service';

export default {
  name: 'ActivityLevelCard',
  props: {
    profile: {
      type: Object,
      default: null
    }
  },
  computed: {
    activityLevelDisplay() {
      return WellnessService.getActivityLevelDisplay(this.profile?.activity_level);
    },
    activityDescription() {
      return WellnessService.getActivityDescription(this.profile?.activity_level);
    },
    activitySuggestions() {
      return WellnessService.getActivitySuggestions(this.profile?.activity_level);
    }
  }
};
</script>