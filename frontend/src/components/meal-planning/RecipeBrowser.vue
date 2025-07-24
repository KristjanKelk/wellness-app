<!-- src/components/meal-planning/RecipeBrowser.vue -->
<template>
  <div class="recipe-browser">
    <!-- Search and Filters -->
    <div class="search-section">
      <div class="search-controls">
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

        <div class="search-toggle">
          <button
            @click="searchMode = 'local'"
            class="toggle-btn"
            :class="{ active: searchMode === 'local' }"
          >
            <i class="fas fa-database"></i>
            Local Recipes
          </button>
          <button
            @click="searchMode = 'spoonacular'"
            class="toggle-btn"
            :class="{ active: searchMode === 'spoonacular' }"
          >
            <i class="fas fa-globe"></i>
            Spoonacular
          </button>
        </div>
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

        <select v-model="selectedDiet" @change="applyFilters" class="filter-select" v-if="searchMode === 'spoonacular'">
          <option value="">All Diets</option>
          <option value="vegetarian">Vegetarian</option>
          <option value="vegan">Vegan</option>
          <option value="pescatarian">Pescatarian</option>
          <option value="ketogenic">Ketogenic</option>
          <option value="paleo">Paleo</option>
          <option value="gluten_free">Gluten Free</option>
        </select>
      </div>
    </div>

    <!-- Recipe Grid -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>{{ searchMode === 'spoonacular' ? 'Searching Spoonacular database...' : 'Loading delicious recipes...' }}</p>
    </div>

    <div v-else-if="error" class="error-state">
      <i class="fas fa-exclamation-triangle"></i>
      <h3>Error Loading Recipes</h3>
      <p>{{ error }}</p>
      <button @click="loadRecipes" class="btn btn-primary">
        <i class="fas fa-redo"></i>
        Try Again
      </button>
    </div>

    <div v-else-if="displayedRecipes.length === 0" class="empty-state">
      <i class="fas fa-search"></i>
      <h3>No recipes found</h3>
      <p>Try adjusting your search or filters</p>
      <button v-if="searchMode === 'local'" @click="searchMode = 'spoonacular'" class="btn btn-outline">
        <i class="fas fa-globe"></i>
        Search Spoonacular Instead
      </button>
    </div>

    <div v-else class="recipe-grid">
      <div
        v-for="recipe in displayedRecipes"
        :key="recipe.id"
        class="recipe-card"
        @click="$emit('recipe-selected', recipe)"
      >
        <div class="recipe-image">
          <img
            :src="recipe.image_url || recipe.image || placeholderImage"
            :alt="recipe.title"
            @error="handleImageError"
          />
          <div class="recipe-badges">
            <span v-for="tag in (recipe.dietary_tags || recipe.diets || []).slice(0, 2)" :key="tag" class="badge">
              {{ formatTag(tag) }}
            </span>
          </div>
          <div v-if="searchMode === 'spoonacular'" class="source-badge">
            <i class="fas fa-globe"></i>
            Spoonacular
          </div>
        </div>

        <div class="recipe-content">
          <h3 class="recipe-title">{{ recipe.title }}</h3>
          <p class="recipe-summary" v-html="truncateSummary(recipe.summary)"></p>

          <div class="recipe-stats">
            <div class="stat">
              <i class="fas fa-clock"></i>
              <span>{{ recipe.total_time_minutes || recipe.readyInMinutes || 'N/A' }}min</span>
            </div>
            <div class="stat">
              <i class="fas fa-fire"></i>
              <span>{{ Math.round(recipe.calories_per_serving || recipe.calories || 0) }} cal</span>
            </div>
            <div class="stat">
              <i class="fas fa-users"></i>
              <span>{{ recipe.servings || 4 }} servings</span>
            </div>
          </div>

          <div class="nutrition-preview">
            <div class="macro">
              <span class="macro-label">Protein</span>
              <span class="macro-value">{{ Math.round(recipe.protein_per_serving || recipe.protein || 0) }}g</span>
            </div>
            <div class="macro">
              <span class="macro-label">Carbs</span>
              <span class="macro-value">{{ Math.round(recipe.carbs_per_serving || recipe.carbs || 0) }}g</span>
            </div>
            <div class="macro">
              <span class="macro-label">Fat</span>
              <span class="macro-value">{{ Math.round(recipe.fat_per_serving || recipe.fat || 0) }}g</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Load More Button for Spoonacular -->
      <div v-if="searchMode === 'spoonacular' && hasMore" class="load-more-section">
        <button @click="loadMoreRecipes" class="btn btn-outline" :disabled="loading">
          <i class="fas fa-plus"></i>
          Load More Recipes
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { mealPlanningApi } from '@/services/mealPlanningApi'

function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

export default {
  name: 'RecipeBrowser',
  emits: ['recipe-selected'],
  data() {
    return {
      // Search state
      searchQuery: '',
      searchMode: 'local', // 'local' or 'spoonacular'
      loading: false,
      error: null,
      
      // Filter state
      selectedCuisine: '',
      selectedMealType: '',
      selectedDiet: '',
      
      // Recipe data
      localRecipes: [],
      spoonacularRecipes: [],
      offset: 0,
      hasMore: true,
      
      // Static data
      cuisines: [
        'Mediterranean', 'Asian', 'Italian', 'Mexican', 'American',
        'Indian', 'Middle Eastern', 'French', 'Japanese', 'Thai',
        'Greek', 'Spanish', 'Chinese', 'Korean'
      ],
      
      placeholderImage: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+CiAgPHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OTk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkZvb2QgUmVjaXBlPC90ZXh0Pgo8L3N2Zz4K'
    }
  },
  computed: {
    displayedRecipes() {
      if (this.searchMode === 'spoonacular') {
        return this.spoonacularRecipes
      }
      return this.filteredLocalRecipes
    },
    
    filteredLocalRecipes() {
      let filtered = this.localRecipes

      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        filtered = filtered.filter(recipe =>
          recipe.title.toLowerCase().includes(query) ||
          (recipe.summary && recipe.summary.toLowerCase().includes(query))
        )
      }

      if (this.selectedCuisine) {
        filtered = filtered.filter(recipe => recipe.cuisine === this.selectedCuisine)
      }

      if (this.selectedMealType) {
        filtered = filtered.filter(recipe => recipe.meal_type === this.selectedMealType)
      }

      return filtered
    }
  },
  watch: {
    searchMode() {
      this.loadRecipes()
    }
  },
  async mounted() {
    this.debouncedSearch = debounce(this.loadRecipes, 500)
    await this.loadRecipes()
  },
  methods: {
    async loadRecipes() {
      if (this.searchMode === 'spoonacular') {
        await this.searchSpoonacular(true) // Reset search
      } else {
        await this.loadLocalRecipes()
      }
    },

    async loadLocalRecipes() {
      try {
        this.loading = true
        this.error = null
        
        const params = {}
        if (this.searchQuery) params.search = this.searchQuery
        if (this.selectedCuisine) params.cuisine = this.selectedCuisine
        if (this.selectedMealType) params.meal_type = this.selectedMealType
        
        const response = await mealPlanningApi.getRecipes(params)
        this.localRecipes = response.data?.results || response.data || []
        
      } catch (error) {
        console.error('Failed to load local recipes:', error)
        this.error = 'Failed to load recipes from local database'
        this.localRecipes = []
      } finally {
        this.loading = false
      }
    },

    async searchSpoonacular(reset = false) {
      try {
        this.loading = true
        this.error = null
        
        if (reset) {
          this.spoonacularRecipes = []
          this.offset = 0
          this.hasMore = true
        }
        
        const params = {
          number: 12,
          offset: this.offset
        }
        
        if (this.searchQuery) params.query = this.searchQuery
        if (this.selectedCuisine) params.cuisine = this.selectedCuisine
        if (this.selectedMealType) params.meal_type = this.selectedMealType
        if (this.selectedDiet) params.diet = this.selectedDiet
        
        const response = await mealPlanningApi.searchSpoonacular(params)
        const newRecipes = response.data?.results || response.data || []
        
        if (reset) {
          this.spoonacularRecipes = newRecipes
        } else {
          this.spoonacularRecipes.push(...newRecipes)
        }
        
        this.hasMore = newRecipes.length === 12
        this.offset += newRecipes.length
        
      } catch (error) {
        console.error('Failed to search Spoonacular:', error)
        this.error = error.response?.data?.detail || 'Failed to search Spoonacular recipes. The service might be unavailable.'
        if (reset) this.spoonacularRecipes = []
      } finally {
        this.loading = false
      }
    },

    async loadMoreRecipes() {
      if (this.searchMode === 'spoonacular' && this.hasMore && !this.loading) {
        await this.searchSpoonacular(false)
      }
    },

    applyFilters() {
      if (this.searchMode === 'spoonacular') {
        this.searchSpoonacular(true)
      }
      // Local filtering is handled by computed property
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
      event.target.src = this.placeholderImage
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

.search-controls {
  display: flex;
  gap: $spacing-4;
  margin-bottom: $spacing-4;
  align-items: stretch;
}

.search-bar {
  position: relative;
  flex: 1;
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

.search-toggle {
  display: flex;
  background: $gray-lighter;
  border-radius: 12px;
  padding: 4px;
  gap: 2px;
}

.toggle-btn {
  padding: 8px 16px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.9rem;
  color: $gray;
  display: flex;
  align-items: center;
  gap: 6px;

  &.active {
    background: $white;
    color: $primary;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  &:hover:not(.active) {
    color: $primary;
  }
}

.filters {
  display: flex;
  gap: $spacing-4;
  flex-wrap: wrap;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid $gray-lighter;
  border-radius: 8px;
  background: $white;
  font-size: 0.9rem;
  color: $primary-dark;
  min-width: 140px;

  &:focus {
    outline: none;
    border-color: $primary;
  }
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.9rem;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  text-decoration: none;

  &.btn-primary {
    background: $primary;
    color: $white;

    &:hover:not(:disabled) {
      background: darken($primary, 10%);
      transform: translateY(-1px);
    }
  }

  &.btn-outline {
    background: transparent;
    color: $primary;
    border: 1px solid $primary;

    &:hover:not(:disabled) {
      background: $primary;
      color: $white;
    }
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none !important;
  }
}

.loading-state, .empty-state, .error-state {
  text-align: center;
  padding: $spacing-8;
  color: $gray;

  i {
    font-size: 3rem;
    margin-bottom: $spacing-4;
    color: $gray-light;
  }

  h3 {
    margin: 0 0 $spacing-2 0;
    color: $primary-dark;
  }

  p {
    margin: 0 0 $spacing-4 0;
  }
}

.error-state {
  i {
    color: #dc3545;
  }
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid $gray-lighter;
  border-top: 4px solid $primary;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto $spacing-4 auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.recipe-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: $spacing-6;
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

.badge {
  background: rgba($white, 0.9);
  color: $primary;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.source-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba($primary, 0.9);
  color: $white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
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

.load-more-section {
  grid-column: 1 / -1;
  text-align: center;
  padding: $spacing-4;
}
</style>