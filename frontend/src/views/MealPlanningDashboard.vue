<!-- src/views/MealPlanningDashboard.vue -->
<template>
  <div class="meal-planning-page">
    <div class="meal-planning-dashboard">
      <!-- Header Section -->
      <div class="dashboard__header">
        <h1>Meal Planning</h1>
        <p>AI-powered nutrition planning tailored to your goals</p>
      </div>

      <!-- Navigation Tabs -->
      <div class="tab-navigation">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="['tab-button', { active: activeTab === tab.id }]"
        >
          <i :class="tab.icon"></i>
          {{ tab.name }}
        </button>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Recipes Tab -->
        <div v-if="activeTab === 'recipes'" class="tab-panel">
          <recipe-browser
            :recipes="recipes"
            :loading="recipesLoading"
            @recipe-selected="selectRecipe"
          />
        </div>

        <!-- Nutrition Profile Tab -->
        <div v-if="activeTab === 'profile'" class="tab-panel">
          <nutrition-profile-setup
            :profile="nutritionProfile"
            :loading="profileLoading"
            @profile-updated="updateProfile"
          />
        </div>

        <!-- Coming Soon Tabs -->
        <div v-if="activeTab === 'meal-plans'" class="tab-panel">
          <coming-soon-card
            title="Meal Plans"
            description="AI-generated meal plans coming soon!"
            icon="fas fa-calendar-alt"
          />
        </div>

        <div v-if="activeTab === 'analytics'" class="tab-panel">
          <coming-soon-card
            title="Nutrition Analytics"
            description="Detailed nutrition analytics coming soon!"
            icon="fas fa-chart-line"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import RecipeBrowser from '../components/meal-planning/RecipeBrowser.vue'
import NutritionProfileSetup from '../components/meal-planning/NutritionProfileSetup.vue'
import ComingSoonCard from '../components/meal-planning/ComingSoonCard.vue'
import { mealPlanningApi } from '@/services/mealPlanningApi'

export default {
  name: 'MealPlanningDashboard',
  components: {
    RecipeBrowser,
    NutritionProfileSetup,
    ComingSoonCard
  },
  data() {
    return {
      activeTab: 'recipes',
      tabs: [
        { id: 'recipes', name: 'Recipes', icon: 'fas fa-utensils' },
        { id: 'profile', name: 'Nutrition Profile', icon: 'fas fa-user-cog' },
        { id: 'meal-plans', name: 'Meal Plans', icon: 'fas fa-calendar-alt' },
        { id: 'analytics', name: 'Analytics', icon: 'fas fa-chart-line' }
      ],
      recipes: [],
      nutritionProfile: null,
      recipesLoading: false,
      profileLoading: false
    }
  },
  computed: {
    currentUser() {
      return this.$store.getters['auth/currentUser'];
    }
  },
  async mounted() {
    if (!this.currentUser) {
      this.$router.push('/login');
      return;
    }
    await this.loadInitialData()
  },
  methods: {
    async loadInitialData() {
      await Promise.all([
        this.loadRecipes(),
        this.loadNutritionProfile()
      ])
    },

    async loadRecipes() {
      this.recipesLoading = true
      try {
        const response = await mealPlanningApi.getRecipes()
        this.recipes = response.data.results || []
      } catch (error) {
        console.error('Failed to load recipes:', error)
        // Show user-friendly error
        this.$toast?.error?.('Failed to load recipes') ||
        alert('Failed to load recipes')
      } finally {
        this.recipesLoading = false
      }
    },

    async loadNutritionProfile() {
      this.profileLoading = true
      try {
        const response = await mealPlanningApi.getNutritionProfile()
        this.nutritionProfile = response.data
      } catch (error) {
        console.error('Failed to load nutrition profile:', error)
        // Create default profile if none exists
        this.nutritionProfile = {
          calorie_target: 2000,
          protein_target: 100,
          carb_target: 250,
          fat_target: 67,
          dietary_preferences: [],
          allergies_intolerances: [],
          cuisine_preferences: []
        }
      } finally {
        this.profileLoading = false
      }
    },

    async updateProfile(profileData) {
      try {
        const response = await mealPlanningApi.updateNutritionProfile(profileData)
        this.nutritionProfile = response.data
        this.$toast?.success?.('Nutrition profile updated!') ||
        alert('Nutrition profile updated!')
      } catch (error) {
        console.error('Failed to update profile:', error)
        this.$toast?.error?.('Failed to update profile') ||
        alert('Failed to update profile')
      }
    },

    selectRecipe(recipe) {
      // Handle recipe selection - could open a modal or navigate to detail view
      console.log('Selected recipe:', recipe)
      // For now, just log it. Later we can add a recipe detail modal
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.meal-planning-page {
  min-height: 100vh;
  background-color: $bg-light;
}

.meal-planning-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: $spacing-6;

  @include responsive('sm') {
    padding: $spacing-4;
  }
}

.dashboard__header {
  text-align: center;
  margin-bottom: $spacing-6;

  h1 {
    font-size: 2.5rem;
    font-weight: 700;
    color: $primary-dark;
    margin-bottom: $spacing-2;
  }

  p {
    font-size: 1.1rem;
    color: $gray;
    margin: 0;
  }
}

.tab-navigation {
  display: flex;
  border-bottom: 2px solid $gray-lighter;
  margin-bottom: $spacing-6;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;

  @include responsive('sm') {
    justify-content: center;
  }
}

.tab-button {
  display: flex;
  align-items: center;
  gap: $spacing-2;
  padding: $spacing-3 $spacing-4;
  border: none;
  background: none;
  font-size: 1rem;
  font-weight: 500;
  color: $gray;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.2s ease;
  white-space: nowrap;
  min-width: fit-content;

  &:hover {
    color: $primary;
    background-color: rgba($primary, 0.05);
  }

  &.active {
    color: $primary;
    border-bottom-color: $primary;
    background-color: rgba($primary, 0.1);
  }

  i {
    font-size: 1.1rem;
  }

  @include responsive('sm') {
    padding: $spacing-2 $spacing-3;
    font-size: 0.9rem;

    i {
      font-size: 1rem;
    }
  }
}

.tab-content {
  min-height: 500px;
}

.tab-panel {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>