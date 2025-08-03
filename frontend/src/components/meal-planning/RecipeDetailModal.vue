<!-- src/components/meal-planning/RecipeDetailModal.vue -->
<template>
  <div class="recipe-modal-overlay" @click.self="$emit('close')">
    <div class="recipe-modal" @click.stop>
      <div class="modal-header">
        <div class="header-content">
          <h2>{{ recipe.title }}</h2>
          <div class="recipe-meta">
            <span class="badge cuisine">{{ formatCuisine(recipe.cuisine) }}</span>
            <span class="badge meal-type">{{ formatMealType(recipe.meal_type) }}</span>
            <span class="badge difficulty" :class="getDifficultyClass(recipe.difficulty_level)">
              {{ formatDifficulty(recipe.difficulty_level) }}
            </span>
          </div>
        </div>
        <button class="close-btn" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>
      
      <div class="modal-body">
        <!-- Recipe Image and Quick Stats -->
        <div class="recipe-hero">
          <div class="image-wrapper" v-if="recipe.image_url">
            <img :src="recipe.image_url" :alt="recipe.title" @error="imageError" />
            <div class="image-overlay">
              <div class="recipe-stats">
                <div class="stat">
                  <i class="fas fa-clock"></i>
                  <span>{{ formatTime(recipe.total_time_minutes) }}</span>
                </div>
                <div class="stat">
                  <i class="fas fa-users"></i>
                  <span>{{ recipe.servings }} {{ recipe.servings === 1 ? 'serving' : 'servings' }}</span>
                </div>
                <div class="stat">
                  <i class="fas fa-fire"></i>
                  <span>{{ Math.round(recipe.calories_per_serving) || 'N/A' }} cal</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Nutrition Information -->
          <div class="nutrition-panel">
            <h3>Nutrition Information</h3>
            <div class="nutrition-toggle">
              <label class="toggle-label">
                <input 
                  type="checkbox" 
                  v-model="showTotalNutrition"
                  class="nutrition-toggle-input"
                />
                <span class="toggle-text">
                  {{ showTotalNutrition ? 'Total for ' + adjustedServings + ' servings' : 'Per serving' }}
                </span>
              </label>
            </div>
            <div class="nutrition-grid">
              <div class="nutrition-item calories">
                <div class="nutrition-value">{{ calculatedNutrition.calories || 'N/A' }}</div>
                <div class="nutrition-label">Calories</div>
              </div>
              <div class="nutrition-item protein">
                <div class="nutrition-value">{{ calculatedNutrition.protein }}g</div>
                <div class="nutrition-label">Protein</div>
              </div>
              <div class="nutrition-item carbs">
                <div class="nutrition-value">{{ calculatedNutrition.carbs }}g</div>
                <div class="nutrition-label">Carbs</div>
              </div>
              <div class="nutrition-item fat">
                <div class="nutrition-value">{{ calculatedNutrition.fat }}g</div>
                <div class="nutrition-label">Fat</div>
              </div>
            </div>
            
            <!-- Dietary Tags -->
            <div v-if="recipe.dietary_tags && recipe.dietary_tags.length" class="dietary-tags">
              <span v-for="tag in recipe.dietary_tags" :key="tag" class="dietary-tag">
                {{ formatTag(tag) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Serving Size Adjustment -->
        <div class="serving-adjustment-section">
          <h3>
            <i class="fas fa-utensils"></i>
            Adjust Serving Size
          </h3>
          <div class="serving-controls">
            <div class="serving-input-group">
              <label for="serving-input">Number of Servings:</label>
              <div class="serving-input-wrapper">
                <button 
                  class="serving-btn decrease" 
                  @click="decreaseServings"
                  :disabled="adjustedServings <= 1"
                >
                  <i class="fas fa-minus"></i>
                </button>
                <input 
                  id="serving-input"
                  type="number" 
                  v-model.number="adjustedServings" 
                  min="1" 
                  max="20"
                  class="serving-input"
                  @input="validateServings"
                />
                <button 
                  class="serving-btn increase" 
                  @click="increaseServings"
                  :disabled="adjustedServings >= 20"
                >
                  <i class="fas fa-plus"></i>
                </button>
              </div>
              <div class="serving-info">
                <span class="original-info">Original: {{ recipe.servings }} {{ recipe.servings === 1 ? 'serving' : 'servings' }}</span>
                <span v-if="servingMultiplier !== 1" class="multiplier-info">
                  ({{ servingMultiplier.toFixed(2) }}x {{ servingMultiplier > 1 ? 'larger' : 'smaller' }})
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Recipe Summary -->
        <div v-if="recipe.summary" class="summary-section">
          <h3>About This Recipe</h3>
          <p class="summary" v-html="cleanSummary(recipe.summary)"></p>
        </div>

        <!-- Ingredients Section -->
        <div class="ingredients-section" v-if="recipe.ingredients_data && recipe.ingredients_data.length">
          <h3>
            <i class="fas fa-list-ul"></i>
            Ingredients
            <span v-if="servingMultiplier !== 1" class="ingredients-multiplier">
              (adjusted for {{ adjustedServings }} {{ adjustedServings === 1 ? 'serving' : 'servings' }})
            </span>
          </h3>
          <div class="ingredients-grid">
            <div 
              v-for="(ing, idx) in adjustedIngredients" 
              :key="idx"
              class="ingredient-item"
            >
              <span class="ingredient-text">{{ ing.formatted }}</span>
              <span v-if="servingMultiplier !== 1 && ing.original !== ing.formatted" class="ingredient-original">
                Original: {{ ing.original }}
              </span>
            </div>
          </div>
        </div>

        <!-- Instructions Section -->
        <div class="instructions-section" v-if="normalizedInstructions.length">
          <h3>
            <i class="fas fa-clipboard-list"></i>
            Instructions
          </h3>
          <div class="instructions-list">
            <div 
              v-for="(step, idx) in normalizedInstructions" 
              :key="idx"
              class="instruction-step"
            >
              <div class="step-number">{{ idx + 1 }}</div>
              <div class="step-content">{{ step.step || step.description || step }}</div>
            </div>
          </div>
        </div>

        <!-- Source Information -->
        <div v-if="recipe.source_url || recipe.source" class="source-section">
          <div class="source-info">
            <span class="source-label">Source:</span>
            <a v-if="recipe.source_url" :href="recipe.source_url" target="_blank" class="source-link">
              View Original Recipe <i class="fas fa-external-link-alt"></i>
            </a>
            <span v-else class="source-text">{{ recipe.source || 'Recipe Database' }}</span>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="btn btn-outline" @click="$emit('close')">
          <i class="fas fa-times"></i>
          Close
        </button>
        <button 
          v-if="localRecipe"
          :class="['btn', localRecipe.is_saved_by_user ? 'btn-success' : 'btn-primary']" 
          @click="toggleSaveRecipe" 
          :disabled="saving"
        >
          <i v-if="saving" class="fas fa-spinner fa-spin"></i>
          <i v-else-if="localRecipe.is_saved_by_user" class="fas fa-heart"></i>
          <i v-else class="far fa-heart"></i>
          {{ saving ? (localRecipe.is_saved_by_user ? 'Removing...' : 'Saving...') : (localRecipe.is_saved_by_user ? 'Saved' : 'Save Recipe') }}
        </button>
        <button class="btn btn-info" @click="generateShoppingList">
          <i class="fas fa-shopping-cart"></i>
          Shopping List
        </button>
      </div>
    </div>

    <!-- Shopping List Modal -->
    <shopping-list-modal
      v-if="showShoppingListModal"
      :shopping-list="shoppingListData"
      :loading="shoppingListLoading"
      :error="shoppingListError"
      @close="closeShoppingListModal"
      @retry="generateShoppingList"
    />
  </div>
</template>

<script>
import ShoppingListModal from './ShoppingListModal.vue'

export default {
  name: 'RecipeDetailModal',
  components: {
    ShoppingListModal
  },
  props: {
    recipe: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      saving: false,
      showShoppingListModal: false,
      shoppingListData: null,
      shoppingListLoading: false,
      shoppingListError: null,
      localRecipe: null,  // Local copy to avoid mutating props
      adjustedServings: 4,  // Default serving size
      showTotalNutrition: false  // Toggle between per serving and total nutrition
    }
  },
  mounted() {
    // Create a local copy of the recipe to avoid mutating props
    this.localRecipe = { ...this.recipe }
    // Initialize serving size to recipe's original serving size
    this.adjustedServings = this.recipe.servings || 4
  },
  watch: {
    recipe: {
      handler(newRecipe) {
        // Update local copy when prop changes
        this.localRecipe = { ...newRecipe }
        // Reset serving size to recipe's original serving size
        this.adjustedServings = newRecipe.servings || 4
      },
      immediate: true
    }
  },
  computed: {
    servingMultiplier() {
      const originalServings = this.recipe.servings || 4
      return this.adjustedServings / originalServings
    },

    calculatedNutrition() {
      const multiplier = this.showTotalNutrition ? this.adjustedServings : 1
      const baseMultiplier = this.servingMultiplier * multiplier
      
      return {
        calories: Math.round((this.recipe.calories_per_serving || 0) * baseMultiplier),
        protein: Math.round((this.recipe.protein_per_serving || 0) * baseMultiplier),
        carbs: Math.round((this.recipe.carbs_per_serving || 0) * baseMultiplier),
        fat: Math.round((this.recipe.fat_per_serving || 0) * baseMultiplier),
        fiber: Math.round((this.recipe.fiber_per_serving || 0) * baseMultiplier)
      }
    },

    adjustedIngredients() {
      if (!this.recipe.ingredients_data || !Array.isArray(this.recipe.ingredients_data)) {
        return []
      }

      return this.recipe.ingredients_data.map(ingredient => {
        const original = this.formatIngredient(ingredient)
        const adjusted = this.adjustIngredientQuantity(ingredient)
        
        return {
          original: original,
          formatted: adjusted,
          raw: ingredient
        }
      })
    },

    normalizedInstructions() {
      const instr = this.recipe.instructions || []
      
      // Handle empty instructions
      if (!instr || instr.length === 0) {
        return []
      }
      
      // If it's already an array of objects with step property, use it as is
      if (instr.length && typeof instr[0] === 'object' && instr[0].step) {
        return instr
      }
      
      // If it's an array of strings, convert to objects
      if (instr.length && typeof instr[0] === 'string') {
        return instr.map((stepText, i) => ({
          number: i + 1,
          step: stepText,
          description: stepText
        }))
      }
      
      // If it's an array of objects without step property, try to extract the step text
      if (instr.length && typeof instr[0] === 'object') {
        return instr.map((stepObj, i) => ({
          number: stepObj.number || i + 1,
          step: stepObj.step || stepObj.description || stepObj.instruction || `Step ${i + 1}`,
          description: stepObj.step || stepObj.description || stepObj.instruction || `Step ${i + 1}`
        }))
      }
      
      return []
    }
  },
  methods: {
    formatIngredient(ing) {
      if (typeof ing === 'string') return ing
      
      // Handle different ingredient formats
      if (ing.original) return ing.original
      
      const amount = ing.amount || ing.quantity || ''
      const unit = ing.unit || ''
      const name = ing.name || ing.ingredient || ''
      
      if (amount && unit) {
        return `${amount} ${unit} ${name}`.trim()
      } else if (amount) {
        return `${amount} ${name}`.trim()
      }
      
      return name || 'Ingredient'
    },

    adjustIngredientQuantity(ingredient) {
      if (typeof ingredient === 'string') {
        return this.adjustStringIngredient(ingredient)
      }

      // Handle different ingredient formats
      if (ingredient.original) {
        return this.adjustStringIngredient(ingredient.original)
      }

      const amount = ingredient.amount || ingredient.quantity || ''
      const unit = ingredient.unit || ''
      const name = ingredient.name || ingredient.ingredient || ''

      if (amount && !isNaN(parseFloat(amount))) {
        const adjustedAmount = this.adjustQuantity(parseFloat(amount))
        if (unit) {
          return `${adjustedAmount} ${unit} ${name}`.trim()
        } else {
          return `${adjustedAmount} ${name}`.trim()
        }
      }

      return name || 'Ingredient'
    },

    adjustStringIngredient(ingredientStr) {
      if (!ingredientStr || this.servingMultiplier === 1) {
        return ingredientStr
      }

      // Regular expressions to match different quantity patterns
      const patterns = [
        // Fractions: 1/2, 3/4, etc.
        /^(\d+\/\d+|\d+\s+\d+\/\d+)/,
        // Decimals: 1.5, 2.25, etc.
        /^(\d+\.?\d*)/,
        // Ranges: 2-3, 1-2, etc.
        /^(\d+)-(\d+)/
      ]

      for (const pattern of patterns) {
        const match = ingredientStr.match(pattern)
        if (match) {
          const originalQuantity = match[0]
          let adjustedQuantity

          if (originalQuantity.includes('/')) {
            // Handle fractions
            adjustedQuantity = this.adjustFraction(originalQuantity)
          } else if (originalQuantity.includes('-')) {
            // Handle ranges
            const [min, max] = originalQuantity.split('-').map(num => parseFloat(num))
            const adjustedMin = this.adjustQuantity(min)
            const adjustedMax = this.adjustQuantity(max)
            adjustedQuantity = `${adjustedMin}-${adjustedMax}`
          } else {
            // Handle regular numbers
            adjustedQuantity = this.adjustQuantity(parseFloat(originalQuantity))
          }

          return ingredientStr.replace(originalQuantity, adjustedQuantity)
        }
      }

      return ingredientStr
    },

    adjustQuantity(quantity) {
      const adjusted = quantity * this.servingMultiplier
      
      // Round to appropriate precision
      if (adjusted < 0.1) {
        return adjusted.toFixed(2)
      } else if (adjusted < 1) {
        return adjusted.toFixed(1)
      } else if (adjusted < 10) {
        return Math.round(adjusted * 4) / 4  // Round to nearest quarter
      } else {
        return Math.round(adjusted)
      }
    },

    adjustFraction(fractionStr) {
      // Convert fraction to decimal, adjust, then convert back to fraction if reasonable
      const parts = fractionStr.trim().split(/\s+/)
      let decimal = 0

      for (const part of parts) {
        if (part.includes('/')) {
          const [num, den] = part.split('/').map(n => parseInt(n))
          decimal += num / den
        } else {
          decimal += parseInt(part)
        }
      }

      const adjusted = decimal * this.servingMultiplier
      return this.decimalToFraction(adjusted)
    },

    decimalToFraction(decimal) {
      // Convert decimal back to a readable fraction or mixed number
      const tolerance = 1.0E-6
      let num = decimal
      let den = 1

      // Find the fraction representation
      while (Math.abs(num - Math.round(num)) > tolerance) {
        num *= 10
        den *= 10
      }

      num = Math.round(num)

      // Simplify the fraction
      const gcd = this.findGCD(num, den)
      num /= gcd
      den /= gcd

      // Convert to mixed number if appropriate
      if (num >= den) {
        const whole = Math.floor(num / den)
        const remainder = num % den
        if (remainder === 0) {
          return whole.toString()
        } else {
          return `${whole} ${remainder}/${den}`
        }
      } else if (den === 1) {
        return num.toString()
      } else {
        return `${num}/${den}`
      }
    },

    findGCD(a, b) {
      // Greatest Common Divisor using Euclidean algorithm
      return b === 0 ? a : this.findGCD(b, a % b)
    },

    increaseServings() {
      if (this.adjustedServings < 20) {
        this.adjustedServings++
      }
    },

    decreaseServings() {
      if (this.adjustedServings > 1) {
        this.adjustedServings--
      }
    },

    validateServings() {
      if (this.adjustedServings < 1) {
        this.adjustedServings = 1
      } else if (this.adjustedServings > 20) {
        this.adjustedServings = 20
      }
    },

    formatTime(minutes) {
      if (!minutes) return 'N/A'
      if (minutes < 60) return `${minutes}min`
      const hours = Math.floor(minutes / 60)
      const remainingMins = minutes % 60
      return remainingMins > 0 ? `${hours}h ${remainingMins}min` : `${hours}h`
    },

    formatCuisine(cuisine) {
      if (!cuisine) return ''
      return cuisine.charAt(0).toUpperCase() + cuisine.slice(1)
    },

    formatMealType(mealType) {
      const formats = {
        'breakfast': 'Breakfast',
        'lunch': 'Lunch',
        'dinner': 'Dinner',
        'snack': 'Snack',
        'dessert': 'Dessert'
      }
      return formats[mealType] || mealType
    },

    formatDifficulty(difficulty) {
      const formats = {
        'easy': 'Easy',
        'medium': 'Medium',
        'hard': 'Hard'
      }
      return formats[difficulty] || 'Medium'
    },

    getDifficultyClass(difficulty) {
      return `difficulty-${difficulty || 'medium'}`
    },

    formatTag(tag) {
      return tag.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    },

    cleanSummary(summary) {
      if (!summary) return ''
      // Remove HTML tags but keep line breaks
      return summary.replace(/<[^>]*>/g, '').replace(/\n/g, '<br>')
    },

    imageError(event) {
      // Instead of hiding the image, show a placeholder
      event.target.src = this.getPlaceholderImage()
      event.target.style.background = '#f8f9fa'
      event.target.style.border = '2px dashed #dee2e6'
      event.target.style.color = '#6c757d'
      event.target.style.display = 'flex'
      event.target.style.alignItems = 'center'
      event.target.style.justifyContent = 'center'
      event.target.style.fontSize = '14px'
      event.target.onerror = null // Prevent infinite loop
    },

    getPlaceholderImage() {
      // Return a data URL for a simple placeholder image
      return 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDMwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjRjhGOUZBIiBzdHJva2U9IiNERUUyRTYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWRhc2hhcnJheT0iNSA1Ii8+Cjx0ZXh0IHg9IjE1MCIgeT0iMTAwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjNkM3NTdEIiBmb250LWZhbWlseT0iLWFwcGxlLXN5c3RlbSwgQmxpbmtNYWNTeXN0ZW1Gb250LCBTZWdvZSBVSSwgUm9ib3RvLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjE0cHgiPk5vIEltYWdlPC90ZXh0Pgo8cGF0aCBkPSJNMTIwIDgwSDEzMFY5MEgxMjBWODBaTTE0MCA4MEgxNTBWOTBIMTQwVjgwWk0xNjAgODBIMTcwVjkwSDE2MFY4MFoiIGZpbGw9IiM2Qzc1N0QiLz4KPC9zdmc+'
    },

    async toggleSaveRecipe() {
      if (!this.localRecipe) {
        console.warn('No recipe provided to toggle')
        return
      }
      
      this.saving = true
      try {
        console.log('Toggling save status for recipe:', this.localRecipe)
        
        // Import the API service
        const { mealPlanningApi } = await import('@/services/mealPlanningApi')
        
        let response
        
        if (this.localRecipe.is_saved_by_user) {
          // Remove from saved recipes
          if (!this.localRecipe.id) {
            throw new Error('Cannot remove recipe: No recipe ID found')
          }
          
          // Check if this is a fallback recipe ID
          const isFallbackRecipe = this.localRecipe.id.toString().startsWith('fallback_')
          if (isFallbackRecipe) {
            throw new Error('Cannot remove fallback recipe: Not saved in database')
          }
          
          response = await mealPlanningApi.removeRecipeFromMyCollection(this.localRecipe.id)
          
          // Update local state
          this.localRecipe.is_saved_by_user = false
          
          const message = response.data?.message || 'Recipe removed from your collection!'
          this.$toast?.success?.(message) || alert(message)
        } else {
          // Save recipe - handle different recipe types
          const isFallbackRecipe = this.localRecipe.id && this.localRecipe.id.toString().startsWith('fallback_')
          
          if (this.localRecipe.spoonacular_id && !this.localRecipe.created_by) {
            // This is a spoonacular recipe from meal plan
            response = await mealPlanningApi.saveRecipeFromMealPlan(this.localRecipe)
          } else if (this.localRecipe.id && !isFallbackRecipe && this.localRecipe.created_by) {
            // This is an existing recipe in the database created by a user
            response = await mealPlanningApi.saveRecipeToMyCollection(this.localRecipe.id)
          } else {
            // This is recipe data that needs to be saved (fallback recipes, new recipes, etc.)
            response = await mealPlanningApi.saveRecipeFromMealPlan(this.localRecipe)
          }
          
          // Update local state
          this.localRecipe.is_saved_by_user = true
          
          const message = response.data?.message || 'Recipe saved to your collection!'
          this.$toast?.success?.(message) || alert(message)
          
          // Emit the saved recipe
          this.$emit('recipe-saved', response.data.recipe || this.localRecipe)
        }
        
      } catch (error) {
        console.error('Error toggling recipe save status:', error)
        
        let errorMessage = 'An error occurred while saving the recipe'
        
        if (!navigator.onLine) {
          errorMessage = 'No internet connection. Please check your network and try again.'
        } else if (error.response?.status === 404) {
          errorMessage = 'Recipe not found. This may be a temporary recipe that cannot be saved.'
        } else if (error.response?.status === 403) {
          errorMessage = 'You don\'t have permission to perform this action. Please log in again.'
        } else if (error.response?.status === 500) {
          errorMessage = 'Server error. Please try again in a moment.'
        } else if (error.response?.status === 400) {
          errorMessage = error.response?.data?.message || 'Invalid recipe data. Please try again.'
        } else if (error.response?.data?.error) {
          errorMessage = error.response.data.error
        } else if (error.response?.data?.message) {
          errorMessage = error.response.data.message
        } else if (error.message?.includes('Network Error')) {
          errorMessage = 'Network error. Please check your connection and try again.'
        } else if (error.message) {
          errorMessage = error.message
        }
        
        this.$toast?.error?.(errorMessage) || alert(`Error: ${errorMessage}`)
        
        // Reset the save state if it was changed optimistically
        if (this.localRecipe.is_saved_by_user) {
          this.localRecipe.is_saved_by_user = false
        }
      } finally {
        this.saving = false
      }
    },

    async generateShoppingList() {
      try {
        this.shoppingListLoading = true
        this.shoppingListError = null
        this.showShoppingListModal = true

        // Check if this is a fallback recipe
        const recipeId = this.localRecipe?.id || this.recipe?.id
        const isFallbackRecipe = recipeId && recipeId.toString().startsWith('fallback_')
        
        if (isFallbackRecipe) {
          // Generate shopping list from recipe data directly for fallback recipes
          const ingredients = this.adjustedIngredients || []
          this.shoppingListData = {
            recipe_title: this.localRecipe.title || 'Recipe',
            total_servings: this.adjustedServings,
            items: ingredients.map(ingredient => ({
              ingredient: ingredient.formatted || ingredient.original || 'Unknown ingredient',
              quantity: 1,
              unit: '',
              category: 'Other'
            }))
          }
          this.shoppingListLoading = false
          this.$toast?.success?.('Shopping list generated successfully!') ||
          console.log('Shopping list generated successfully!')
          return
        }

        const response = await fetch(`/api/meal-planning/recipes/${recipeId}/generate_shopping_list/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.$store.state.auth.token}`
          },
          body: JSON.stringify({
            servings_multiplier: this.servingMultiplier,
            adjusted_servings: this.adjustedServings
          })
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        this.shoppingListData = data.shopping_list
        this.shoppingListLoading = false

        // Show success message
        this.$toast?.success?.('Shopping list generated successfully!') ||
        console.log('Shopping list generated successfully!')

      } catch (error) {
        console.error('Error generating shopping list:', error)
        this.shoppingListError = error.message || 'Failed to generate shopping list'
        this.shoppingListLoading = false
        
        // Show error message
        this.$toast?.error?.(`Error: ${this.shoppingListError}`) ||
        alert(`Error generating shopping list: ${this.shoppingListError}`)
      }
    },

    closeShoppingListModal() {
      this.showShoppingListModal = false
      this.shoppingListData = null
      this.shoppingListError = null
      this.shoppingListLoading = false  // Reset loading state
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.recipe-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: flex-start;
  z-index: 1000;
  padding: 20px;
  overflow-y: auto;
  backdrop-filter: blur(5px);
}

.recipe-modal {
  background: $white;
  border-radius: 20px;
  max-width: 900px;
  width: 100%;
  max-height: 95vh;
  overflow-y: auto;
  box-shadow: $shadow-lg;
  margin: 20px 0;
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 32px 32px 24px;
  border-bottom: 1px solid $gray-lighter;
  background: linear-gradient(135deg, $primary-light 0%, $primary 100%);
  color: $white;
  border-radius: 20px 20px 0 0;

  .header-content {
    flex: 1;

    h2 {
      margin: 0 0 12px 0;
      font-size: 2rem;
      font-weight: 700;
      line-height: 1.2;
    }
  }

  .recipe-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .badge {
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 0.8rem;
    font-weight: 600;
    background: rgba($white, 0.2);
    color: $white;

    &.difficulty-easy { background: rgba($success, 0.8); }
    &.difficulty-medium { background: rgba($warning, 0.8); }
    &.difficulty-hard { background: rgba($error, 0.8); }
  }

  .close-btn {
    background: rgba($white, 0.2);
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 12px;
    border-radius: 50%;
    color: $white;
    transition: all 0.2s ease;
    margin-left: 16px;

    &:hover {
      background: rgba($white, 0.3);
      transform: scale(1.1);
    }
  }
}

.modal-body {
  padding: 0;
}

.recipe-hero {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 0;
  background: $white;

  @include responsive('md') {
    grid-template-columns: 1fr;
  }
}

.image-wrapper {
  position: relative;
  height: 300px;
  overflow: hidden;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .image-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(transparent, rgba(0,0,0,0.8));
    padding: 20px;
    color: $white;
  }

  .recipe-stats {
    display: flex;
    justify-content: space-around;
    gap: 16px;
  }

  .stat {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.9rem;
    font-weight: 600;

    i {
      font-size: 1rem;
      color: $primary-light;
    }
  }
}

.nutrition-panel {
  padding: 24px;
  background: $gray-lighter;
  border-left: 1px solid $gray-lighter;

  @include responsive('md') {
    border-left: none;
    border-top: 1px solid $gray-lighter;
  }

  h3 {
    margin: 0 0 16px 0;
    font-size: 1.2rem;
    color: $primary-dark;
  }

  .nutrition-toggle {
    margin-bottom: 16px;

    .toggle-label {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      font-size: 0.9rem;
      color: $gray-dark;

      .nutrition-toggle-input {
        width: 16px;
        height: 16px;
        cursor: pointer;
      }

      .toggle-text {
        font-weight: 500;
      }
    }
  }
}

.nutrition-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.nutrition-item {
  text-align: center;
  padding: 12px;
  background: $white;
  border-radius: 12px;
  box-shadow: $shadow-sm;

  .nutrition-value {
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 4px;
  }

  .nutrition-label {
    font-size: 0.8rem;
    color: $gray;
    text-transform: uppercase;
    font-weight: 600;
  }

  &.calories .nutrition-value { color: #e74c3c; }
  &.protein .nutrition-value { color: #3498db; }
  &.carbs .nutrition-value { color: #f39c12; }
  &.fat .nutrition-value { color: #9b59b6; }
}

.dietary-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;

  .dietary-tag {
    padding: 4px 8px;
    background: $primary;
    color: $white;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
  }
}

.serving-adjustment-section {
  padding: 24px 32px;
  border-bottom: 1px solid $gray-lighter;

  h3 {
    margin: 0 0 16px 0;
    font-size: 1.3rem;
    color: $primary-dark;
    display: flex;
    align-items: center;
    gap: 8px;

    i {
      color: $primary;
    }
  }
}

.serving-controls {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-top: 10px;

  .serving-input-group {
    display: flex;
    align-items: center;
    gap: 10px;

    label {
      font-size: 0.9rem;
      color: $gray-dark;
      font-weight: 600;
    }

    .serving-input-wrapper {
      display: flex;
      align-items: center;
      border: 1px solid $gray-light;
      border-radius: 8px;
      overflow: hidden;
      width: 120px;

      .serving-btn {
        background: $gray-light;
        border: none;
        padding: 8px 12px;
        cursor: pointer;
        color: $gray-dark;
        font-size: 1rem;
        transition: all 0.2s ease;
        flex: 1;

        &:hover:not(:disabled) {
          background: $gray;
          color: $white;
        }

        &:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        i {
          font-size: 0.8rem;
        }
      }

      .serving-input {
        flex: 1;
        border: none;
        padding: 8px 10px;
        text-align: center;
        font-size: 1rem;
        font-weight: 600;
        color: $gray-dark;
        background: transparent;
        outline: none;
      }
    }

    .serving-info {
      font-size: 0.8rem;
      color: $gray;
      margin-top: 5px;

      .original-info {
        margin-right: 5px;
      }

      .multiplier-info {
        font-style: italic;
      }
    }
  }
}

.summary-section,
.ingredients-section,
.instructions-section,
.source-section {
  padding: 24px 32px;
  border-bottom: 1px solid $gray-lighter;

  h3 {
    margin: 0 0 16px 0;
    font-size: 1.3rem;
    color: $primary-dark;
    display: flex;
    align-items: center;
    gap: 8px;

    i {
      color: $primary;
    }

    .ingredients-multiplier {
      font-size: 0.9rem;
      font-weight: 400;
      color: $primary;
      font-style: italic;
      margin-left: 8px;
    }
  }
}

.summary {
  font-size: 1rem;
  line-height: 1.6;
  color: $gray-dark;
  margin: 0;
}

.ingredients-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.ingredient-item {
  padding: 12px 16px;
  background: $gray-lighter;
  border-radius: 8px;
  border-left: 3px solid $primary;
  display: flex;
  flex-direction: column;
  gap: 4px;

  .ingredient-text {
    font-weight: 500;
    color: $gray-dark;
  }

  .ingredient-original {
    font-size: 0.8rem;
    color: $gray;
    font-style: italic;
  }
}

.instructions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.instruction-step {
  display: flex;
  gap: 16px;
  align-items: flex-start;

  .step-number {
    min-width: 32px;
    height: 32px;
    background: $primary;
    color: $white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.9rem;
  }

  .step-content {
    flex: 1;
    font-size: 1rem;
    line-height: 1.6;
    color: $gray-dark;
    padding-top: 4px;
  }
}

.source-section {
  border-bottom: none;

  .source-info {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 0.9rem;

    .source-label {
      font-weight: 600;
      color: $gray;
    }

    .source-link {
      color: $primary;
      text-decoration: none;
      font-weight: 500;

      &:hover {
        text-decoration: underline;
      }

      i {
        margin-left: 4px;
        font-size: 0.8rem;
      }
    }
  }
}

.modal-footer {
  padding: 24px 32px;
  background: $gray-lighter;
  border-radius: 0 0 20px 20px;
}

.footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: wrap;

  @include responsive('sm') {
    justify-content: center;
  }
}

.btn {
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  cursor: pointer;
  border: 2px solid;
  font-size: 0.9rem;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &.btn-outline {
    background: transparent;
    color: $gray-dark;
    border-color: $gray-lighter;

    &:hover:not(:disabled) {
      background: $gray-lighter;
      border-color: $gray;
    }
  }

  &.btn-primary {
    background: $primary;
    color: $white;
    border-color: $primary;

    &:hover:not(:disabled) {
      background: $primary-dark;
      border-color: $primary-dark;
      transform: translateY(-1px);
    }
  }

  &.btn-success {
    background: $success;
    color: $white;
    border-color: $success;

    &:hover:not(:disabled) {
      background: darken($success, 10%);
      border-color: darken($success, 10%);
      transform: translateY(-1px);
    }
  }

  &.btn-outline-danger {
    background: transparent;
    color: $error;
    border-color: $error;

    &:hover:not(:disabled) {
      background: $error;
      color: $white;
      border-color: $error;
      transform: translateY(-1px);
    }

    i.fas.fa-heart {
      color: $error;
    }
  }
}

// Mobile responsive adjustments
@include responsive('sm') {
  .recipe-modal {
    margin: 10px;
    max-height: 98vh;
  }

  .modal-header {
    padding: 20px;

    .header-content h2 {
      font-size: 1.5rem;
    }
  }

  .modal-body {
    .summary-section,
    .ingredients-section,
    .instructions-section,
    .source-section {
      padding: 20px;
    }
  }

  .nutrition-panel {
    padding: 20px;
  }

  .modal-footer {
    padding: 20px;
  }
}
</style>
