<!-- src/views/MealPlanningDashboard.vue -->
<template>
  <div class="meal-planning-dashboard">
    <div class="dashboard-header">
      <h1>Meal Planning Dashboard</h1>
      <p>AI-powered nutrition and meal planning</p>
    </div>

    <div class="dashboard-tabs">
      <nav class="tabs-nav">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="tab-button"
          :class="{ 'active': activeTab === tab.id }"
        >
          <i :class="tab.icon"></i>
          {{ tab.name }}
        </button>
      </nav>

      <div class="tab-content">
        <div v-if="activeTab === 'recipes'" class="tab-panel">
          <recipe-browser
            :recipes="recipes"
            :loading="recipesLoading"
            :has-more="recipesHasMore"
            @recipe-selected="selectRecipe"
            @search="searchRecipes"
            @load-more="loadMoreRecipes"
          />
        </div>

        <div v-if="activeTab === 'profile'" class="tab-panel">
          <nutrition-profile-setup
            :profile="nutritionProfile"
            :loading="profileLoading"
            @profile-updated="onProfileUpdated"
          />
        </div>

        <div v-if="activeTab === 'meal-plans'" class="tab-panel">
          <meal-plan-manager
            :loading="mealPlansLoading"
            :nutrition-profile="nutritionProfile"
            @meal-plan-generated="onMealPlanGenerated"
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
  <recipe-detail-modal
    v-if="showRecipeModal"
    :recipe="selectedRecipe"
    @close="closeRecipeModal"
  />
</div>
</template>

<script>
import RecipeBrowser from '../components/meal-planning/RecipeBrowser.vue'
import NutritionProfileSetup from '../components/meal-planning/NutritionProfileSetup.vue'
import MealPlanManager from '../components/meal-planning/MealPlanManager.vue'
import ComingSoonCard from '../components/meal-planning/ComingSoonCard.vue'
import RecipeDetailModal from '../components/meal-planning/RecipeDetailModal.vue'
import { mealPlanningApi } from '@/services/mealPlanningApi'

export default {
  name: 'MealPlanningDashboard',
  components: {
    RecipeBrowser,
    NutritionProfileSetup,
    MealPlanManager,
    ComingSoonCard,
    RecipeDetailModal
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
      profileLoading: false,
      mealPlansLoading: false,
      showRecipeModal: false,
      selectedRecipe: null,
      // Pagination state
      recipesPage: 1,
      recipesHasMore: true,
      lastSearchQuery: ''
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
        // Reset recipes if this is a new search
        this.recipes = []
        
        const response = await mealPlanningApi.getRecipes({
          page_size: 10,
          page: 1
        })
        
        this.recipes = response.data.results || response.data || []
        this.recipesHasMore = !!response.data.next
        this.recipesPage = 1
      } catch (error) {
        console.error('Failed to load recipes:', error)
        // Show user-friendly error
        this.$toast?.error?.('Failed to load recipes') ||
        alert('Failed to load recipes')
      } finally {
        this.recipesLoading = false
      }
    },

    async searchRecipes(query) {
      this.recipesLoading = true
      try {
        this.recipes = []
        
        const params = {
          page_size: 10,
          page: 1
        }
        
        if (query && query.trim()) {
          params.search = query.trim()
        }
        
        const response = await mealPlanningApi.getRecipes(params)
        this.recipes = response.data.results || response.data || []
        this.recipesHasMore = !!response.data.next
        this.recipesPage = 1
        this.lastSearchQuery = query
      } catch (error) {
        console.error('Failed to search recipes:', error)
        this.$toast?.error?.('Failed to search recipes') ||
        alert('Failed to search recipes')
      } finally {
        this.recipesLoading = false
      }
    },

    async loadMoreRecipes() {
      if (this.recipesLoading || !this.recipesHasMore) return
      
      this.recipesLoading = true
      try {
        const params = {
          page_size: 10,
          page: this.recipesPage + 1
        }
        
        if (this.lastSearchQuery) {
          params.search = this.lastSearchQuery
        }
        
        const response = await mealPlanningApi.getRecipes(params)
        const newRecipes = response.data.results || response.data || []
        
        this.recipes = [...this.recipes, ...newRecipes]
        this.recipesHasMore = !!response.data.next
        this.recipesPage = this.recipesPage + 1
      } catch (error) {
        console.error('Failed to load more recipes:', error)
        this.$toast?.error?.('Failed to load more recipes') ||
        alert('Failed to load more recipes')
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
          cuisine_preferences: [],
          disliked_ingredients: [],
          meals_per_day: 3,
          timezone: 'Europe/Tallinn'
        }
      } finally {
        this.profileLoading = false
      }
    },

    // Fixed: Handle profile updates properly
    onProfileUpdated(updatedProfile) {
      // Update local state with the new profile data
      this.nutritionProfile = { ...updatedProfile }

      // Optionally reload related data that depends on the profile
      // For example, if meal plans depend on the nutrition profile
      if (this.activeTab === 'meal-plans') {
        // Refresh meal plans since preferences might have changed
        this.$nextTick(() => {
          this.$forceUpdate()
        })
      }
    },

    selectRecipe(recipe) {
      this.selectedRecipe = recipe
      this.showRecipeModal = true
    },

    closeRecipeModal() {
      this.showRecipeModal = false
      this.selectedRecipe = null
    },

    onMealPlanGenerated(mealPlan) {
      console.log('New meal plan generated:', mealPlan)
      // Handle the new meal plan - could show success message, refresh data, etc.
      this.$toast?.success?.('Meal plan generated successfully!') ||
      alert('Meal plan generated successfully!')
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.meal-planning-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: $spacing-6;
}

.dashboard-header {
  text-align: center;
  margin-bottom: $spacing-8;

  h1 {
    margin: 0 0 $spacing-2 0;
    color: $primary-dark;
    font-size: 2rem;
    font-weight: 600;
  }

  p {
    margin: 0;
    color: $gray;
    font-size: 1.1rem;
  }
}

.dashboard-tabs {
  background: $white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow;
  overflow: hidden;
}

.tabs-nav {
  display: flex;
  background: $gray-light;
  border-bottom: 1px solid $gray-lighter;
}

.tab-button {
  flex: 1;
  padding: $spacing-4 $spacing-6;
  border: none;
  background: transparent;
  color: $gray;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-2;

  i {
    font-size: 0.9rem;
  }

  &:hover {
    background: rgba($primary, 0.1);
    color: $primary;
  }

  &.active {
    background: $primary;
    color: $white;
    box-shadow: inset 0 -3px 0 rgba($white, 0.3);
  }
}

.tab-content {
  min-height: 600px;
}

.tab-panel {
  padding: $spacing-6;
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

// Responsive design
@media (max-width: 768px) {
  .meal-planning-dashboard {
    padding: $spacing-4;
  }

  .tabs-nav {
    flex-direction: column;
  }

  .tab-button {
    justify-content: flex-start;
    padding: $spacing-3 $spacing-4;
  }

  .tab-panel {
    padding: $spacing-4;
  }

  .dashboard-header {
    h1 {
      font-size: 1.5rem;
    }
  }
}
</style>