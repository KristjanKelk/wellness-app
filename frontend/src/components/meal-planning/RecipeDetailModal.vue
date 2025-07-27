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
            <h3>Nutrition per Serving</h3>
            <div class="nutrition-grid">
              <div class="nutrition-item calories">
                <div class="nutrition-value">{{ Math.round(recipe.calories_per_serving) || 'N/A' }}</div>
                <div class="nutrition-label">Calories</div>
              </div>
              <div class="nutrition-item protein">
                <div class="nutrition-value">{{ Math.round(recipe.protein_per_serving) || 0 }}g</div>
                <div class="nutrition-label">Protein</div>
              </div>
              <div class="nutrition-item carbs">
                <div class="nutrition-value">{{ Math.round(recipe.carbs_per_serving) || 0 }}g</div>
                <div class="nutrition-label">Carbs</div>
              </div>
              <div class="nutrition-item fat">
                <div class="nutrition-value">{{ Math.round(recipe.fat_per_serving) || 0 }}g</div>
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
          </h3>
          <div class="ingredients-grid">
            <div 
              v-for="(ing, idx) in recipe.ingredients_data" 
              :key="idx"
              class="ingredient-item"
            >
              <span class="ingredient-text">{{ formatIngredient(ing) }}</span>
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
        <div class="footer-actions">
          <button class="btn btn-outline" @click="$emit('close')">
            <i class="fas fa-times"></i>
            Close
          </button>
          <button class="btn btn-primary" @click="saveRecipe" :disabled="saving">
            <i v-if="saving" class="fas fa-spinner fa-spin"></i>
            <i v-else class="fas fa-heart"></i>
            {{ saving ? 'Saving...' : 'Save Recipe' }}
          </button>
          <button class="btn btn-success" @click="addToMealPlan">
            <i class="fas fa-plus"></i>
            Add to Meal Plan
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RecipeDetailModal',
  props: {
    recipe: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      saving: false
    }
  },
  computed: {
    normalizedInstructions() {
      const instr = this.recipe.instructions || []
      if (instr.length && typeof instr[0] === 'object') {
        return instr
      }
      return instr.map((s, i) => ({ description: s, step: `Step ${i + 1}` }))
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
      event.target.style.display = 'none'
    },

    async saveRecipe() {
      this.saving = true
      try {
        // Here you would make an API call to save the recipe
        console.log('Saving recipe:', this.recipe)
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        this.$toast?.success?.('Recipe saved to your collection!') ||
        alert('Recipe saved to your collection!')
        
      } catch (error) {
        console.error('Error saving recipe:', error)
        this.$toast?.error?.('Failed to save recipe') ||
        alert('Failed to save recipe')
      } finally {
        this.saving = false
      }
    },

    addToMealPlan() {
      console.log('Adding recipe to meal plan:', this.recipe)
      this.$toast?.success?.('Recipe added to meal plan!') ||
      alert('Recipe added to meal plan!')
      this.$emit('add-to-meal-plan', this.recipe)
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

  .ingredient-text {
    font-weight: 500;
    color: $gray-dark;
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
