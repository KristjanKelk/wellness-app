<!-- src/components/meal-planning/RecipeBrowser.vue -->
<template>
  <div class="recipe-browser">
    <!-- Search and Filters -->
    <div class="search-section">
      <div class="search-bar">
        <i class="fas fa-search search-icon"></i>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search recipes (e.g., 'chicken', 'pasta', 'vegan')..."
          class="search-input"
          @input="debouncedSearch"
          @keyup.enter="performSearch"
        />
        <button 
          v-if="searchQuery" 
          @click="clearSearch"
          class="clear-search-btn"
          type="button"
        >
          <i class="fas fa-times"></i>
        </button>
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
    <div v-if="loading && filteredRecipes.length === 0" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading delicious recipes...</p>
    </div>

    <div v-else-if="filteredRecipes.length === 0 && !loading" class="empty-state">
      <i class="fas fa-search"></i>
      <h3>No recipes found</h3>
      <p v-if="searchQuery">
        No recipes found for "{{ searchQuery }}". Try a different search term or clear your search.
      </p>
      <p v-else>
        Try searching for recipes like "chicken", "pasta", or "vegan".
      </p>
      <button v-if="searchQuery" @click="clearSearch" class="btn btn-primary">
        <i class="fas fa-times"></i>
        Clear Search
      </button>
    </div>

    <div v-else class="recipe-grid">
      <div
        v-for="recipe in filteredRecipes"
        :key="recipe.id || recipe.spoonacular_id"
        class="recipe-card"
        @click="$emit('recipe-selected', recipe)"
      >
        <div class="recipe-image">
          <img
            :src="recipe.image_url || 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+CiAgPHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OTk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkZvb2QgUmVjaXBlPC90ZXh0Pgo8L3N2Zz4K'"
            :alt="recipe.title"
            @error="handleImageError"
          />
          <div class="recipe-badges">
            <span v-for="tag in recipe.dietary_tags.slice(0, 2)" :key="tag" class="badge">
              {{ formatTag(tag) }}
            </span>
          </div>
        </div>

        <div class="recipe-content">
          <h3 class="recipe-title">{{ recipe.title }}</h3>
          <p class="recipe-summary" v-html="truncateSummary(recipe.summary)"></p>

          <div class="recipe-stats">
            <div class="stat">
              <i class="fas fa-clock"></i>
              <span>{{ recipe.total_time_minutes }}min</span>
            </div>
            <div class="stat">
              <i class="fas fa-fire"></i>
              <span>{{ Math.round(recipe.calories_per_serving) }} cal</span>
            </div>
            <div class="stat">
              <i class="fas fa-users"></i>
              <span>{{ recipe.servings }} servings</span>
            </div>
          </div>

          <div class="nutrition-preview">
            <div class="macro">
              <span class="macro-label">Protein</span>
              <span class="macro-value">{{ Math.round(recipe.protein_per_serving) }}g</span>
            </div>
            <div class="macro">
              <span class="macro-label">Carbs</span>
              <span class="macro-value">{{ Math.round(recipe.carbs_per_serving) }}g</span>
            </div>
            <div class="macro">
              <span class="macro-label">Fat</span>
              <span class="macro-value">{{ Math.round(recipe.fat_per_serving) }}g</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Load More Button -->
    <div v-if="hasMore && filteredRecipes.length > 0" class="load-more-section">
      <button 
        @click="$emit('load-more')" 
        :disabled="loading"
        class="load-more-btn"
      >
        <i v-if="loading" class="fas fa-spinner fa-spin"></i>
        <i v-else class="fas fa-plus"></i>
        {{ loading ? 'Loading...' : 'Load More Recipes' }}
      </button>
    </div>

    <!-- Loading overlay for load more -->
    <div v-if="loading && filteredRecipes.length > 0" class="loading-overlay">
      <div class="loading-spinner"></div>
      <p>Loading more recipes...</p>
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
    },
    hasMore: {
      type: Boolean,
      default: false
    }
  },
  emits: ['recipe-selected', 'load-more', 'search'],
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
      handler() {
        this.filteredRecipes = this.recipes
      }
    }
  },
  created() {
    this.debouncedSearch = debounce(this.emitSearch, 300)
  },
  methods: {
    applyFilters() {
      let filtered = this.recipes

      // Search filter
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        filtered = filtered.filter(recipe =>
          recipe.title.toLowerCase().includes(query) ||
          recipe.summary.toLowerCase().includes(query)
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

    performSearch() {
      this.emitSearch()
    },

    clearSearch() {
      this.searchQuery = ''
      this.emitSearch()
    },

    emitSearch() {
      // Emit search event to parent component
      this.$emit('search', this.searchQuery)
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

.clear-search-btn {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: $gray;
  font-size: 1rem;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: background-color 0.2s ease;

  &:hover {
    background-color: $gray-lightest;
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

.load-more-section {
  text-align: center;
  padding: $spacing-6 0;
  background: $white;
  border-top: 1px solid $gray-lighter;
  border-bottom: 1px solid $gray-lighter;
}

.load-more-btn {
  padding: 12px 24px;
  background: $primary;
  color: $white;
  border: none;
  border-radius: $border-radius-md;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;

  &:hover:not(:disabled) {
    background: $primary-dark;
  }

  &:disabled {
    background: $gray-lighter;
    color: $gray;
    cursor: not-allowed;
    opacity: 0.7;
  }
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba($white, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  border-radius: $border-radius-lg;
  box-shadow: $shadow;
}

.loading-overlay .loading-spinner {
  width: 60px;
  height: 60px;
  border: 6px solid $gray-lighter;
  border-left: 6px solid $primary;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}
</style>