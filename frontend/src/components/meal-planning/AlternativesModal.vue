<template>
  <div class="modal fade show" style="display: block" tabindex="-1" role="dialog" aria-labelledby="alternativesModalLabel" aria-modal="true">
    <div class="modal-dialog modal-xl" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="alternativesModalLabel">
            <i class="fas fa-exchange-alt"></i>
            Recipe Alternatives for {{ formatMealType(mealType) }}
            <span v-if="day" class="text-muted">- {{ formatDate(day) }}</span>
          </h5>
          <button type="button" class="btn-close" @click="$emit('close')" aria-label="Close"></button>
        </div>
        
        <div class="modal-body">
          <!-- Options Toggle -->
          <div class="alternatives-options mb-4">
            <div class="row">
              <div class="col-md-6">
                <div class="form-check form-switch">
                  <input 
                    class="form-check-input" 
                    type="checkbox" 
                    id="includeUserRecipes" 
                    v-model="includeUserRecipes"
                    @change="loadAlternatives"
                  >
                  <label class="form-check-label" for="includeUserRecipes">
                    <i class="fas fa-heart text-danger"></i>
                    Include My Saved Recipes
                  </label>
                </div>
              </div>
              <div class="col-md-6">
                <div class="form-group">
                  <label for="alternativeCount" class="form-label">Number of alternatives:</label>
                  <select 
                    class="form-select form-select-sm" 
                    id="alternativeCount" 
                    v-model="alternativeCount"
                    @change="loadAlternatives"
                    style="width: auto; display: inline-block;"
                  >
                    <option value="3">3</option>
                    <option value="5">5</option>
                    <option value="8">8</option>
                    <option value="10">10</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          <!-- Loading State -->
          <div v-if="loading" class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading alternatives...</span>
            </div>
            <p class="mt-3 text-muted">Finding the perfect alternatives for you...</p>
          </div>

          <!-- Error State -->
          <div v-else-if="error" class="alert alert-danger" role="alert">
            <i class="fas fa-exclamation-triangle"></i>
            {{ error }}
            <button class="btn btn-sm btn-outline-danger ms-2" @click="loadAlternatives">
              <i class="fas fa-redo"></i> Retry
            </button>
          </div>

          <!-- Alternatives Grid -->
          <div v-else-if="alternatives.length > 0" class="alternatives-grid">
            <!-- Summary -->
            <div class="alternatives-summary mb-3">
              <div class="row">
                <div class="col-md-8">
                  <p class="mb-1">
                    <strong>{{ alternatives.length }}</strong> alternatives found
                    <span v-if="userRecipeCount > 0" class="badge bg-danger ms-2">
                      <i class="fas fa-heart"></i> {{ userRecipeCount }} from your recipes
                    </span>
                    <span v-if="externalRecipeCount > 0" class="badge bg-primary ms-1">
                      <i class="fas fa-globe"></i> {{ externalRecipeCount }} suggestions
                    </span>
                  </p>
                </div>
                <div class="col-md-4 text-end">
                  <small class="text-muted">
                    <i class="fas fa-info-circle"></i>
                    Click any recipe to replace your current meal
                  </small>
                </div>
              </div>
            </div>

            <!-- Recipe Cards -->
            <div class="row">
              <div v-for="recipe in alternatives" :key="recipe.id" class="col-md-6 col-lg-4 mb-4">
                <div 
                  class="recipe-alternative-card card h-100"
                  :class="{ 'user-recipe': recipe.is_user_recipe }"
                  @click="selectAlternative(recipe)"
                  style="cursor: pointer;"
                >
                  <!-- Recipe Source Badge -->
                  <div class="recipe-source-badge">
                    <span v-if="recipe.is_user_recipe" class="badge bg-danger">
                      <i class="fas fa-heart"></i> My Recipe
                    </span>
                    <span v-else class="badge bg-primary">
                      <i class="fas fa-globe"></i> Suggestion
                    </span>
                  </div>

                  <!-- Recipe Image -->
                  <div class="recipe-image-container">
                    <img 
                      :src="recipe.image || '/api/placeholder/300/200'" 
                      class="card-img-top recipe-image"
                      :alt="recipe.title"
                      @error="handleImageError"
                    >
                    <div class="recipe-overlay">
                      <button class="btn btn-primary btn-sm">
                        <i class="fas fa-exchange-alt"></i> Use This Recipe
                      </button>
                    </div>
                  </div>

                  <div class="card-body">
                    <h6 class="card-title">{{ recipe.title }}</h6>
                    
                    <!-- Recipe Info -->
                    <div class="recipe-info mb-2">
                      <small class="text-muted d-flex justify-content-between">
                        <span>
                          <i class="fas fa-clock"></i> {{ recipe.readyInMinutes || 30 }}min
                        </span>
                        <span>
                          <i class="fas fa-users"></i> {{ recipe.servings || 1 }}
                        </span>
                        <span v-if="recipe.rating">
                          <i class="fas fa-star text-warning"></i> {{ recipe.rating.toFixed(1) }}
                        </span>
                      </small>
                    </div>

                    <!-- Recipe Summary -->
                    <p class="card-text small">
                      {{ truncateSummary(recipe.summary) }}
                    </p>

                    <!-- Nutrition Preview (if available) -->
                    <div v-if="recipe.nutrition && Object.keys(recipe.nutrition).length > 0" class="nutrition-preview">
                      <small class="text-muted">
                        <i class="fas fa-chart-bar"></i> Nutrition per serving
                      </small>
                      <div class="nutrition-mini d-flex justify-content-between mt-1">
                        <span v-if="recipe.nutrition.calories">
                          {{ Math.round(recipe.nutrition.calories) }}cal
                        </span>
                        <span v-if="recipe.nutrition.protein">
                          {{ Math.round(recipe.nutrition.protein) }}g protein
                        </span>
                        <span v-if="recipe.nutrition.carbs">
                          {{ Math.round(recipe.nutrition.carbs) }}g carbs
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- No Alternatives Found -->
          <div v-else class="text-center py-5">
            <i class="fas fa-search fa-3x text-muted mb-3"></i>
            <h5 class="text-muted">No alternatives found</h5>
            <p class="text-muted">
              <span v-if="!includeUserRecipes">
                Try enabling "Include My Saved Recipes" or save some recipes first.
              </span>
              <span v-else>
                No matching recipes found for {{ formatMealType(mealType) }}.
              </span>
            </p>
            <button class="btn btn-outline-primary" @click="loadAlternatives">
              <i class="fas fa-redo"></i> Try Again
            </button>
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="$emit('close')">
            <i class="fas fa-times"></i> Cancel
          </button>
          <button 
            type="button" 
            class="btn btn-outline-primary" 
            @click="loadAlternatives"
            :disabled="loading"
          >
            <i class="fas fa-redo"></i> Refresh Alternatives
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mealPlanningApi } from '../../services/mealPlanningApi'

export default {
  name: 'AlternativesModal',
  
  props: {
    planId: {
      type: [String, Number],
      required: true
    },
    day: {
      type: String,
      required: true
    },
    mealType: {
      type: String,
      required: true
    }
  },

  emits: ['close', 'alternative-selected'],

  data() {
    return {
      loading: false,
      error: null,
      alternatives: [],
      includeUserRecipes: true,
      alternativeCount: 5,
      selectedRecipe: null
    }
  },

  computed: {
    userRecipeCount() {
      return this.alternatives.filter(alt => alt.is_user_recipe).length
    },
    
    externalRecipeCount() {
      return this.alternatives.filter(alt => !alt.is_user_recipe).length
    }
  },

  mounted() {
    this.loadAlternatives()
  },

  methods: {
    async loadAlternatives() {
      this.loading = true
      this.error = null
      
      try {
        console.log('Loading alternatives:', {
          planId: this.planId,
          day: this.day,
          mealType: this.mealType,
          count: this.alternativeCount,
          includeUserRecipes: this.includeUserRecipes
        })
        
        const response = await mealPlanningApi.getMealAlternatives(
          this.planId,
          this.day,
          this.mealType,
          this.alternativeCount,
          this.includeUserRecipes
        )
        
        console.log('Alternatives response:', response.data)
        
        // Handle both old and new API response formats
        if (response.data && response.data.alternatives) {
          this.alternatives = response.data.alternatives
        } else if (Array.isArray(response.data)) {
          this.alternatives = response.data
        } else {
          this.alternatives = []
        }
        
        console.log(`Loaded ${this.alternatives.length} alternatives`)
        
      } catch (error) {
        console.error('Error loading alternatives:', error)
        this.error = error.response?.data?.error || error.message || 'Failed to load alternatives'
        this.alternatives = []
      } finally {
        this.loading = false
      }
    },

    async selectAlternative(recipe) {
      try {
        console.log('Selecting alternative:', recipe)
        
        // Emit the selection event with recipe data
        this.$emit('alternative-selected', {
          day: this.day,
          mealType: this.mealType,
          recipe: recipe
        })
        
        // Close the modal
        this.$emit('close')
        
      } catch (error) {
        console.error('Error selecting alternative:', error)
        this.error = 'Failed to select alternative recipe'
      }
    },

    formatMealType(mealType) {
      if (!mealType) return ''
      return mealType.charAt(0).toUpperCase() + mealType.slice(1).toLowerCase()
    },

    formatDate(dateStr) {
      if (!dateStr) return ''
      try {
        const date = new Date(dateStr)
        return date.toLocaleDateString('en-US', { 
          weekday: 'long', 
          month: 'short', 
          day: 'numeric' 
        })
      } catch (e) {
        return dateStr
      }
    },

    truncateSummary(summary) {
      if (!summary) return 'No description available.'
      
      // Remove HTML tags
      const cleanSummary = summary.replace(/<[^>]*>/g, '')
      
      if (cleanSummary.length <= 120) {
        return cleanSummary
      }
      
      return cleanSummary.substring(0, 120) + '...'
    },

    handleImageError(event) {
      event.target.src = '/api/placeholder/300/200'
    }
  }
}
</script>

<style scoped>
.alternatives-modal {
  z-index: 1055;
}

.alternatives-grid {
  max-height: 70vh;
  overflow-y: auto;
}

.recipe-alternative-card {
  transition: all 0.3s ease;
  border: 2px solid transparent;
  position: relative;
}

.recipe-alternative-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.15);
  border-color: #007bff;
}

.recipe-alternative-card.user-recipe {
  border-left: 4px solid #dc3545;
}

.recipe-alternative-card.user-recipe:hover {
  border-color: #dc3545;
}

.recipe-source-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1;
}

.recipe-image-container {
  position: relative;
  overflow: hidden;
}

.recipe-image {
  height: 200px;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.recipe-alternative-card:hover .recipe-image {
  transform: scale(1.05);
}

.recipe-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 123, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.recipe-alternative-card:hover .recipe-overlay {
  opacity: 1;
}

.recipe-info {
  font-size: 0.85rem;
}

.nutrition-preview {
  background: #f8f9fa;
  padding: 0.5rem;
  border-radius: 0.25rem;
  margin-top: 0.5rem;
}

.nutrition-mini {
  font-size: 0.75rem;
  font-weight: 500;
}

.alternatives-summary {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 0.5rem;
  border-left: 4px solid #007bff;
}

.alternatives-options {
  background: #fff;
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #dee2e6;
}

.form-check-label {
  font-weight: 500;
}

.form-check-label i {
  margin-right: 0.5rem;
}

/* Modal backdrop */
.modal {
  background: rgba(0, 0, 0, 0.5);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .modal-dialog {
    margin: 0.5rem;
  }
  
  .col-md-6 {
    margin-bottom: 1rem;
  }
  
  .alternatives-grid {
    max-height: 60vh;
  }
  
  .recipe-image {
    height: 150px;
  }
}

/* Loading animation */
.spinner-border {
  width: 3rem;
  height: 3rem;
}

/* Badge styles */
.badge {
  font-size: 0.75rem;
  font-weight: 500;
}

.badge i {
  margin-right: 0.25rem;
}
</style>