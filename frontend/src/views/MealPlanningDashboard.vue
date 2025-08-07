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
            @recipe-selected="selectRecipe"
            @refresh-recipes="loadRecipes"
            @recipe-saved="onRecipeSaved"
            @recipe-removed="onRecipeRemoved"
          />
        </div>

        <div v-if="activeTab === 'meal-plans'" class="tab-panel">
          <meal-plan-manager
            :loading="mealPlansLoading"
            :nutrition-profile="nutritionProfile"
            @meal-plan-generated="onMealPlanGenerated"
          />
        </div>

      <!-- <div v-if="activeTab === 'analytics'" class="tab-panel">
        <coming-soon-card
          title="Nutrition Analytics"
          description="Detailed nutrition analytics coming soon!"
          icon="fas fa-chart-line"
        />
      </div>
    -->
    </div>
  </div>
  <recipe-detail-modal
    v-if="showRecipeModal"
    :recipe="selectedRecipe"
    @close="closeRecipeModal"
    @recipe-saved="onRecipeSaved"
  />
</div>
</template>

<script>
import RecipeBrowser from '../components/meal-planning/RecipeBrowser.vue'
import MealPlanManager from '../components/meal-planning/MealPlanManager.vue'
//import ComingSoonCard from '../components/meal-planning/ComingSoonCard.vue'
import RecipeDetailModal from '../components/meal-planning/RecipeDetailModal.vue'
import { mealPlanningApi } from '@/services/mealPlanningApi'

export default {
  name: 'MealPlanningDashboard',
  components: {
    RecipeBrowser,
    MealPlanManager,
    //ComingSoonCard,
    RecipeDetailModal
  },
  data() {
    return {
      activeTab: 'recipes',
      tabs: [
        { id: 'recipes', name: 'My Recipes', icon: 'fas fa-utensils' },
        { id: 'meal-plans', name: 'Meal Plans', icon: 'fas fa-calendar-alt' }
        //{ id: 'analytics', name: 'Analytics', icon: 'fas fa-chart-line' }
      ],
      recipes: [],
      nutritionProfile: null,
      recipesLoading: false,
      mealPlansLoading: false,
      showRecipeModal: false,
      selectedRecipe: null
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
        // Add cache busting parameter to ensure fresh data
        const params = {
          _t: Date.now(),
          page_size: 100  // Load more recipes by default
        }
        if (process.env.NODE_ENV === 'development') {
          console.log('🔄 Loading my recipes from API...')
        }
        
        const response = await mealPlanningApi.getMyRecipes(params)
        
        // Handle pagination response
        if (response?.data?.results && Array.isArray(response.data.results)) {
          this.recipes = response.data.results
          if (process.env.NODE_ENV === 'development') {
            console.log(`✅ Loaded ${this.recipes.length} my recipes (${response.data.count} total available)`)
          }
        } else if (Array.isArray(response?.data)) {
          this.recipes = response.data
          if (process.env.NODE_ENV === 'development') {
            console.log(`✅ Loaded ${this.recipes.length} my recipes`)
          }
        } else {
          console.warn('⚠️ Unexpected API response structure:', response?.data)
          this.recipes = []
        }
      } catch (error) {
        console.error('❌ Failed to load my recipes:', error.message)
        if (process.env.NODE_ENV === 'development') {
          console.error('Error details:', {
            status: error.response?.status,
            data: error.response?.data
          })
        }
        
        this.recipes = []
        // Show user-friendly error
        this.$toast?.error?.('Failed to load your recipes') ||
        alert('Failed to load your recipes')
      } finally {
        this.recipesLoading = false
      }
    },

    async loadNutritionProfile() {
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

    async onRecipeRemoved(removedRecipe) {
      console.log('Recipe removed event received:', removedRecipe)
      
      // Remove from local state
      this.recipes = this.recipes.filter(r => r.id !== removedRecipe.id)
      
      // Refresh the recipes list to ensure consistency
      await this.loadRecipes()
    },

    async onRecipeSaved(savedRecipe) {
      console.log('Recipe saved event received:', savedRecipe)
      
      // Refresh the recipes list to show the newly saved recipe
      await this.loadRecipes()
      
      // If we're on the recipes tab, show a brief highlight or message
      if (this.activeTab === 'recipes') {
        this.$nextTick(() => {
          console.log('My recipes refreshed after saving new recipe')
        })
      }
    },

    async onMealPlanGenerated(mealPlan) {
      console.log('New meal plan generated:', mealPlan)
      
      // Show success message
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