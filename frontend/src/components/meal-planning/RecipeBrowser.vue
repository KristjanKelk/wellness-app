<!-- src/components/meal-planning/RecipeBrowser.vue -->
<template>
  <div class="recipe-browser">
    <!-- Search and Filters -->
    <div class="search-section">
      <div class="search-header">
        <h3>My Recipe Collection</h3>
        <button @click="$emit('refresh-recipes')" class="refresh-btn" :disabled="loading">
          <i :class="loading ? 'fas fa-spinner fa-spin' : 'fas fa-sync-alt'"></i>
          Refresh
        </button>
      </div>
      
      <div class="search-bar">
        <i class="fas fa-search search-icon"></i>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search recipes..."
          class="search-input"
          @input="debouncedSearch"
        />
      </div>

      <div class="filters">
        <select v-model="selectedCuisine" @change="applyFilters" class="filter-select">
          <option value="">All Cuisines</option>
          <option v-for="cuisine in cuisines" :key="cuisine" :value="cuisine">
            {{ formatCuisine(cuisine) }}
          </option>
        </select>

        <select v-model="selectedMealType" @change="applyFilters" class="filter-select">
          <option value="">All Meal Types</option>
          <option value="breakfast">Breakfast</option>
          <option value="lunch">Lunch</option>
          <option value="dinner">Dinner</option>
          <option value="snack">Snack</option>
        </select>
      </div>
    </div>

    <!-- Recipe Grid -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading delicious recipes...</p>
    </div>

    <div v-else-if="filteredRecipes.length === 0" class="empty-state">
      <i class="fas fa-utensils"></i>
      <h3>No recipes found</h3>
      <p v-if="recipes.length === 0">
        You haven't saved any recipes yet! Save recipes from your meal plans to build your personal collection.
        <br><br>
        <strong>💡 Tip:</strong> Go to the "Meal Plans" tab to create meal plans, then save your favorite recipes.
      </p>
      <p v-else>Try adjusting your search or filters</p>
    </div>

    <div v-else class="recipe-grid">
      <div
        v-for="recipe in filteredRecipes"
        :key="recipe.id"
        class="recipe-card"
      >
        <div class="recipe-image" @click="$emit('recipe-selected', recipe)">
          <img
            :src="recipe.image_url || 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+CiAgPHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OTk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkZvb2QgUmVjaXBlPC90ZXh0Pgo8L3N2Zz4K'"
            :alt="recipe.title"
            @error="handleImageError"
          />
          <div class="recipe-badges">
            <span v-for="tag in (recipe.dietary_tags || []).slice(0, 2)" :key="tag" class="badge">
              {{ formatTag(tag) }}
            </span>
          </div>
          <button 
            class="save-btn" 
            @click.stop="toggleSaveRecipe(recipe)"
            :title="recipe.is_saved_by_user ? 'Remove from my recipes' : 'Save to my recipes'"
          >
            <i :class="recipe.is_saved_by_user ? 'fas fa-heart' : 'far fa-heart'"></i>
          </button>
        </div>

        <div class="recipe-content" @click="$emit('recipe-selected', recipe)">
          <h3 class="recipe-title">{{ recipe.title }}</h3>
          <p class="recipe-summary" v-html="truncateSummary(recipe.summary)"></p>

          <div class="recipe-stats">
            <div class="stat">
              <i class="fas fa-clock"></i>
              <span>{{ recipe.total_time_minutes || 'N/A' }}{{ recipe.total_time_minutes ? 'min' : '' }}</span>
            </div>
            <div class="stat">
              <i class="fas fa-fire"></i>
              <span>{{ recipe.calories_per_serving ? Math.round(recipe.calories_per_serving) : 'N/A' }}{{ recipe.calories_per_serving ? ' cal' : '' }}</span>
            </div>
            <div class="stat">
              <i class="fas fa-users"></i>
              <span>{{ recipe.servings || 'N/A' }}{{ recipe.servings ? ' servings' : '' }}</span>
            </div>
          </div>

          <div class="nutrition-preview">
            <div class="macro">
              <span class="macro-label">Protein</span>
              <span class="macro-value">{{ recipe.protein_per_serving ? Math.round(recipe.protein_per_serving) : 'N/A' }}{{ recipe.protein_per_serving ? 'g' : '' }}</span>
            </div>
            <div class="macro">
              <span class="macro-label">Carbs</span>
              <span class="macro-value">{{ recipe.carbs_per_serving ? Math.round(recipe.carbs_per_serving) : 'N/A' }}{{ recipe.carbs_per_serving ? 'g' : '' }}</span>
            </div>
            <div class="macro">
              <span class="macro-label">Fat</span>
              <span class="macro-value">{{ recipe.fat_per_serving ? Math.round(recipe.fat_per_serving) : 'N/A' }}{{ recipe.fat_per_serving ? 'g' : '' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// Using a simple debounce function instead of lodash
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

export default {
  name: 'RecipeBrowser',
  props: {
    recipes: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['recipe-selected', 'refresh-recipes', 'recipe-saved', 'recipe-removed'],
  data() {
    return {
      searchQuery: '',
      selectedCuisine: '',
      selectedMealType: '',
      filteredRecipes: []
    }
  },
  computed: {
    cuisines() {
      return [...new Set(this.recipes.map(r => r.cuisine).filter(Boolean))]
    }
  },
  watch: {
    recipes: {
      immediate: true,
      handler(newRecipes) {
        if (process.env.NODE_ENV === 'development') {
          console.log('🍽️ RecipeBrowser: Recipes updated')
          console.log(`📊 Count: ${newRecipes?.length || 0} recipes`)
          if (newRecipes?.length > 0) {
            console.log(`📋 Sample: "${newRecipes[0]?.title}" (${newRecipes[0]?.id})`)
          }
        }
        this.filteredRecipes = this.recipes
      }
    }
  },
  created() {
    this.debouncedSearch = debounce(this.applyFilters, 300)
  },
  methods: {
    applyFilters() {
      let filtered = this.recipes

      // Search filter
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        filtered = filtered.filter(recipe =>
          (recipe.title && recipe.title.toLowerCase().includes(query)) ||
          (recipe.summary && recipe.summary.toLowerCase().includes(query))
        )
      }

      // Cuisine filter
      if (this.selectedCuisine) {
        filtered = filtered.filter(recipe => recipe.cuisine === this.selectedCuisine)
      }

      // Meal type filter
      if (this.selectedMealType) {
        filtered = filtered.filter(recipe => recipe.meal_type === this.selectedMealType)
      }

      if (process.env.NODE_ENV === 'development' && 
          (this.searchQuery || this.selectedCuisine || this.selectedMealType)) {
        console.log(`🔍 Filters applied: ${this.recipes?.length || 0} → ${filtered.length} recipes`)
      }

      this.filteredRecipes = filtered
    },

    formatCuisine(cuisine) {
      return cuisine.charAt(0).toUpperCase() + cuisine.slice(1)
    },

    formatTag(tag) {
      return tag.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    },

    truncateSummary(summary) {
      if (!summary) return ''
      const clean = summary.replace(/<[^>]*>/g, '')
      return clean.length > 120 ? clean.substring(0, 120) + '...' : clean
    },

    handleImageError(event) {
      event.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+CiAgPHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OTk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkZvb2QgUmVjaXBlPC90ZXh0Pgo8L3N2Zz4K'
    },

    async toggleSaveRecipe(recipe) {
      try {
        // Import the API service
        const { mealPlanningApi } = await import('@/services/mealPlanningApi')
        
        let response
        
        if (recipe.is_saved_by_user) {
          // Remove from saved recipes
          if (!recipe.id) {
            throw new Error('Cannot remove recipe: No recipe ID found')
          }
          
          response = await mealPlanningApi.removeRecipeFromMyCollection(recipe.id)
          
          // Update local state
          recipe.is_saved_by_user = false
          
          this.$emit('recipe-removed', recipe)
          
          // Show success message
          const message = response.data?.message || 'Recipe removed from your collection!'
          this.$toast?.success?.(message) || alert(message)
        } else {
          // Save recipe - handle both spoonacular and existing recipes
          if (recipe.spoonacular_id && !recipe.created_by) {
            // Save from meal plan data
            response = await mealPlanningApi.saveRecipeFromMealPlan(recipe)
          } else if (recipe.id) {
            // Save existing recipe to user's collection
            response = await mealPlanningApi.saveRecipeToMyCollection(recipe.id)
          } else {
            // This is recipe data that needs to be saved
            response = await mealPlanningApi.saveRecipeFromMealPlan(recipe)
          }
          
          // Update local state
          recipe.is_saved_by_user = true
          
          this.$emit('recipe-saved', response.data.recipe || recipe)
          
          // Show success message
          const message = response.data?.message || 'Recipe saved to your collection!'
          this.$toast?.success?.(message) || alert(message)
        }
      } catch (error) {
        console.error('Error toggling recipe save status:', error)
        
        let errorMessage = 'An error occurred'
        
        if (error.response?.status === 404) {
          errorMessage = 'Recipe not found. It may have been removed.'
        } else if (error.response?.status === 403) {
          errorMessage = 'You don\'t have permission to perform this action.'
        } else if (error.response?.status === 500) {
          errorMessage = 'Server error. Please try again later.'
        } else if (error.response?.data?.error) {
          errorMessage = error.response.data.error
        } else if (error.response?.data?.message) {
          errorMessage = error.response.data.message
        } else if (error.message) {
          errorMessage = error.message
        }
        
        this.$toast?.error?.(errorMessage) || alert(`Error: ${errorMessage}`)
      }
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.recipe-browser {
  width: 100%;
}

.search-section {
  margin-bottom: $spacing-6;
}

.search-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-4;

  h3 {
    margin: 0;
    color: $primary-dark;
    font-size: 1.5rem;
    font-weight: 600;
  }
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: $spacing-2;
  padding: 8px 16px;
  background: $primary;
  color: $white;
  border: none;
  border-radius: $border-radius;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover:not(:disabled) {
    background: $primary-dark;
    transform: translateY(-1px);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  i {
    font-size: 0.85rem;
  }
}

.search-bar {
  position: relative;
  margin-bottom: $spacing-4;
}

.search-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: $gray;
  font-size: 1.1rem;
}

.search-input {
  width: 100%;
  padding: 12px 16px 12px 48px;
  border: 2px solid $gray-lighter;
  border-radius: 12px;
  font-size: 1rem;
  transition: border-color 0.2s ease;
  background: $white;

  &:focus {
    outline: none;
    border-color: $primary;
    box-shadow: 0 0 0 3px rgba($primary, 0.1);
  }
}

.filters {
  display: flex;
  gap: $spacing-4;
  flex-wrap: wrap;
}

.filter-select {
  padding: 10px 16px;
  border: 2px solid $gray-lighter;
  border-radius: 8px;
  background: $white;
  font-size: 0.95rem;
  cursor: pointer;
  transition: border-color 0.2s ease;

  &:focus {
    outline: none;
    border-color: $primary;
  }

  @include responsive('sm') {
    flex: 1;
    min-width: 0;
  }
}

.loading-state, .empty-state {
  text-align: center;
  padding: 60px 20px;
  color: $gray;
  background: $white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid $gray-lighter;
  border-left: 4px solid $primary;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state i {
  font-size: 3rem;
  margin-bottom: 16px;
  display: block;
}

.recipe-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: $spacing-6;

  @include responsive('sm') {
    grid-template-columns: 1fr;
  }
}

.recipe-card {
  background: $white;
  border-radius: $border-radius-lg;
  box-shadow: $shadow;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid $gray-lighter;

  &:hover {
    transform: translateY(-4px);
    box-shadow: $shadow-lg;
  }
}

.recipe-image {
  position: relative;
  height: 200px;
  overflow: hidden;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.recipe-badges {
  position: absolute;
  top: 12px;
  left: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.save-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba($white, 0.9);
  color: $error;
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  opacity: 0;
  transform: scale(0.8);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  &:hover {
    background: $white;
    transform: scale(1.1);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  i {
    font-size: 1rem;
    
    &.fas.fa-heart {
      color: #e74c3c; // Filled heart - red
    }
    
    &.far.fa-heart {
      color: #7f8c8d; // Unfilled heart - gray
    }
  }
}

.recipe-card:hover .save-btn {
  opacity: 1;
  transform: scale(1);
}

.badge {
  background: rgba($white, 0.95);
  color: $primary-dark;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.recipe-content {
  padding: $spacing-4;
}

.recipe-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: $primary-dark;
  margin: 0 0 $spacing-2 0;
  line-height: 1.3;
}

.recipe-summary {
  color: $gray;
  font-size: 0.9rem;
  line-height: 1.4;
  margin: 0 0 $spacing-4 0;
}

.recipe-stats {
  display: flex;
  justify-content: space-between;
  margin-bottom: $spacing-4;
  padding: $spacing-3 0;
  border-top: 1px solid $gray-lighter;
  border-bottom: 1px solid $gray-lighter;
}

.stat {
  display: flex;
  align-items: center;
  gap: 6px;
  color: $gray;
  font-size: 0.85rem;

  i {
    font-size: 0.9rem;
    color: $primary;
  }
}

.nutrition-preview {
  display: flex;
  justify-content: space-between;
}

.macro {
  text-align: center;
}

.macro-label {
  display: block;
  font-size: 0.75rem;
  color: $gray;
  margin-bottom: 2px;
}

.macro-value {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  color: $primary-dark;
}
</style>