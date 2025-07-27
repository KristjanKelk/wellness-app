<!-- src/components/meal-planning/SpoonacularIntegration.vue -->
<template>
  <div class="spoonacular-integration">
    <div class="integration-header">
      <h2>Spoonacular Meal Planner</h2>
      <p>Connect to Spoonacular for personalized meal planning and shopping lists</p>
    </div>

    <!-- Connection Status -->
    <div class="connection-section">
      <div v-if="!isConnected && !connecting" class="connection-prompt">
        <div class="connection-card">
          <i class="fas fa-link connection-icon"></i>
          <h3>Connect to Spoonacular</h3>
          <p>Link your account to access personalized meal plans, shopping lists, and recipe recommendations.</p>
          <button 
            @click="connectToSpoonacular" 
            class="btn btn-primary connect-btn"
            :disabled="connecting"
          >
            <i class="fas fa-plug"></i>
            Connect Account
          </button>
        </div>
      </div>

      <div v-if="connecting" class="connecting-status">
        <div class="spinner"></div>
        <p>Connecting to Spoonacular...</p>
      </div>

      <div v-if="isConnected" class="connected-status">
        <div class="status-card success">
          <i class="fas fa-check-circle"></i>
          <div class="status-info">
            <h4>Connected to Spoonacular</h4>
            <p>Username: {{ spoonacularUsername }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Spoonacular Features (only show when connected) -->
    <div v-if="isConnected" class="spoonacular-features">
      
      <!-- Meal Plan Section -->
      <div class="feature-section">
        <div class="section-header">
          <h3><i class="fas fa-calendar-alt"></i> Weekly Meal Plan</h3>
          <div class="date-selector">
            <label for="week-select">Week starting:</label>
            <input 
              id="week-select"
              type="date" 
              v-model="selectedWeekStart"
              @change="loadMealPlan"
              class="date-input"
            >
            <button @click="refreshMealPlan" class="btn btn-secondary btn-sm">
              <i class="fas fa-refresh"></i>
            </button>
          </div>
        </div>

        <div v-if="mealPlanLoading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading meal plan...</p>
        </div>

        <div v-else-if="mealPlan" class="meal-plan-grid">
          <div 
            v-for="(day, index) in mealPlan.days" 
            :key="index" 
            class="day-card"
          >
            <div class="day-header">
              <h4>{{ day.day }}</h4>
              <div class="day-nutrition">
                <span class="calories">{{ getDayCalories(day) }} cal</span>
              </div>
            </div>
            
            <div class="day-meals">
              <div v-if="day.items && day.items.length > 0" class="meals-list">
                <div 
                  v-for="item in day.items" 
                  :key="item.id"
                  class="meal-item"
                  :class="getMealSlotClass(item.slot)"
                >
                  <div class="meal-slot">{{ getMealSlotName(item.slot) }}</div>
                  <div class="meal-content">
                    <h5>{{ item.value.title }}</h5>
                    <p v-if="item.value.servings">Servings: {{ item.value.servings }}</p>
                    <img 
                      v-if="item.value.image || item.value.imageType" 
                      :src="getMealImage(item.value)"
                      :alt="item.value.title"
                      class="meal-image"
                    >
                  </div>
                </div>
              </div>
              <div v-else class="no-meals">
                <p>No meals planned</p>
                <button @click="openAddMealModal(day)" class="btn btn-outline btn-sm">
                  <i class="fas fa-plus"></i> Add Meal
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Shopping List Section -->
      <div class="feature-section">
        <div class="section-header">
          <h3><i class="fas fa-shopping-cart"></i> Shopping List</h3>
          <button @click="refreshShoppingList" class="btn btn-secondary">
            <i class="fas fa-refresh"></i> Refresh
          </button>
        </div>

        <div v-if="shoppingListLoading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading shopping list...</p>
        </div>

        <div v-else-if="shoppingList" class="shopping-list">
          <div v-if="shoppingList.aisles && shoppingList.aisles.length > 0" class="shopping-aisles">
            <div 
              v-for="aisle in shoppingList.aisles" 
              :key="aisle.aisle"
              class="aisle-section"
            >
              <h4>{{ aisle.aisle }}</h4>
              <ul class="items-list">
                <li 
                  v-for="item in aisle.items" 
                  :key="item.id"
                  class="shopping-item"
                >
                  <input 
                    type="checkbox" 
                    :id="`item-${item.id}`"
                    v-model="item.checked"
                    @change="toggleShoppingItem(item)"
                  >
                  <label :for="`item-${item.id}`" :class="{ 'checked': item.checked }">
                    {{ item.name }}
                    <span v-if="item.measures" class="item-amount">
                      ({{ formatItemAmount(item.measures) }})
                    </span>
                  </label>
                </li>
              </ul>
            </div>
          </div>
          <div v-else class="empty-shopping-list">
            <p>Your shopping list is empty</p>
            <button @click="generateShoppingList" class="btn btn-primary">
              <i class="fas fa-list"></i> Generate Shopping List
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Meal Modal -->
    <div v-if="showAddMealModal" class="modal-overlay" @click="closeAddMealModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Add Meal</h3>
          <button @click="closeAddMealModal" class="close-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="addMealToSpoonacular">
            <div class="form-group">
              <label>Meal Type:</label>
              <select v-model="newMeal.slot" required>
                <option value="1">Breakfast</option>
                <option value="2">Lunch</option>
                <option value="3">Dinner</option>
              </select>
            </div>
            <div class="form-group">
              <label>Recipe ID:</label>
              <input 
                type="number" 
                v-model="newMeal.recipeId" 
                placeholder="Enter Spoonacular recipe ID"
                required
              >
            </div>
            <div class="form-group">
              <label>Servings:</label>
              <input 
                type="number" 
                v-model="newMeal.servings" 
                min="1" 
                max="10"
                required
              >
            </div>
            <div class="form-actions">
              <button type="button" @click="closeAddMealModal" class="btn btn-secondary">
                Cancel
              </button>
              <button type="submit" class="btn btn-primary" :disabled="addingMeal">
                <i class="fas fa-plus"></i>
                {{ addingMeal ? 'Adding...' : 'Add Meal' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Error Messages -->
    <div v-if="error" class="error-message">
      <div class="alert alert-error">
        <i class="fas fa-exclamation-triangle"></i>
        {{ error }}
        <button @click="error = null" class="close-alert">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>

    <!-- Success Messages -->
    <div v-if="successMessage" class="success-message">
      <div class="alert alert-success">
        <i class="fas fa-check-circle"></i>
        {{ successMessage }}
        <button @click="successMessage = null" class="close-alert">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { mealPlanningApi } from '@/services/mealPlanningApi'

export default {
  name: 'SpoonacularIntegration',
  data() {
    return {
      isConnected: false,
      connecting: false,
      spoonacularUsername: null,
      mealPlan: null,
      mealPlanLoading: false,
      shoppingList: null,
      shoppingListLoading: false,
      selectedWeekStart: this.getCurrentWeekStart(),
      showAddMealModal: false,
      selectedDay: null,
      newMeal: {
        slot: 1,
        recipeId: null,
        servings: 2
      },
      addingMeal: false,
      error: null,
      successMessage: null
    }
  },
  async mounted() {
    await this.checkSpoonacularStatus()
    if (this.isConnected) {
      await Promise.all([
        this.loadMealPlan(),
        this.loadShoppingList()
      ])
    }
  },
  methods: {
    async checkSpoonacularStatus() {
      try {
        const response = await mealPlanningApi.getSpoonacularStatus()
        this.isConnected = response.data.connected
        this.spoonacularUsername = response.data.spoonacular_username
      } catch (error) {
        console.error('Failed to check Spoonacular status:', error)
        this.error = 'Failed to check connection status'
      }
    },

    async connectToSpoonacular() {
      this.connecting = true
      this.error = null
      
      try {
        const response = await mealPlanningApi.connectSpoonacular()
        this.isConnected = true
        this.spoonacularUsername = response.data.spoonacular_username
        this.successMessage = 'Successfully connected to Spoonacular!'
        
        // Show user their Spoonacular password for reference
        if (response.data.spoonacular_password) {
          alert(`Your Spoonacular password is: ${response.data.spoonacular_password}\nPlease save this for logging into spoonacular.com`)
        }
        
        // Load initial data
        await Promise.all([
          this.loadMealPlan(),
          this.loadShoppingList()
        ])
      } catch (error) {
        console.error('Failed to connect to Spoonacular:', error)
        this.error = error.response?.data?.details || 'Failed to connect to Spoonacular'
      } finally {
        this.connecting = false
      }
    },

    async loadMealPlan() {
      if (!this.isConnected) return
      
      this.mealPlanLoading = true
      this.error = null
      
      try {
        const response = await mealPlanningApi.getSpoonacularMealPlan(this.selectedWeekStart)
        this.mealPlan = response.data
      } catch (error) {
        console.error('Failed to load meal plan:', error)
        this.error = 'Failed to load meal plan from Spoonacular'
      } finally {
        this.mealPlanLoading = false
      }
    },

    async refreshMealPlan() {
      await this.loadMealPlan()
    },

    async loadShoppingList() {
      if (!this.isConnected) return
      
      this.shoppingListLoading = true
      this.error = null
      
      try {
        const response = await mealPlanningApi.getSpoonacularShoppingList()
        this.shoppingList = response.data
      } catch (error) {
        console.error('Failed to load shopping list:', error)
        this.error = 'Failed to load shopping list from Spoonacular'
      } finally {
        this.shoppingListLoading = false
      }
    },

    async refreshShoppingList() {
      await this.loadShoppingList()
    },

    async generateShoppingList() {
      if (!this.isConnected) return
      
      this.shoppingListLoading = true
      this.error = null
      
      try {
        const endDate = new Date(this.selectedWeekStart)
        endDate.setDate(endDate.getDate() + 6)
        
        await mealPlanningApi.generateSpoonacularShoppingList(
          this.selectedWeekStart,
          endDate.toISOString().split('T')[0]
        )
        
        // Reload the shopping list
        await this.loadShoppingList()
        this.successMessage = 'Shopping list generated successfully!'
      } catch (error) {
        console.error('Failed to generate shopping list:', error)
        this.error = 'Failed to generate shopping list'
      } finally {
        this.shoppingListLoading = false
      }
    },

    openAddMealModal(day) {
      this.selectedDay = day
      this.showAddMealModal = true
      this.newMeal = {
        slot: 1,
        recipeId: null,
        servings: 2
      }
    },

    closeAddMealModal() {
      this.showAddMealModal = false
      this.selectedDay = null
    },

    async addMealToSpoonacular() {
      if (!this.selectedDay || !this.newMeal.recipeId) return
      
      this.addingMeal = true
      this.error = null
      
      try {
        const mealData = {
          date: this.formatDateForAPI(this.selectedDay.date),
          slot: parseInt(this.newMeal.slot),
          position: 1,
          type: 'RECIPE',
          value: {
            id: parseInt(this.newMeal.recipeId),
            servings: parseInt(this.newMeal.servings)
          }
        }
        
        await mealPlanningApi.addToSpoonacularMealPlan(mealData)
        this.successMessage = 'Meal added successfully!'
        this.closeAddMealModal()
        
        // Refresh meal plan
        await this.loadMealPlan()
      } catch (error) {
        console.error('Failed to add meal:', error)
        this.error = 'Failed to add meal to plan'
      } finally {
        this.addingMeal = false
      }
    },

    toggleShoppingItem(item) {
      // Note: In a full implementation, you would call an API to mark items as purchased
      console.log(`Item ${item.name} ${item.checked ? 'checked' : 'unchecked'}`)
    },

    getCurrentWeekStart() {
      const today = new Date()
      const startOfWeek = new Date(today.setDate(today.getDate() - today.getDay()))
      return startOfWeek.toISOString().split('T')[0]
    },

    getDayCalories(day) {
      if (!day.nutritionSummary?.nutrients) return 0
      const calorieNutrient = day.nutritionSummary.nutrients.find(n => n.name === 'Calories')
      return calorieNutrient ? Math.round(calorieNutrient.amount) : 0
    },

    getMealSlotName(slot) {
      const slots = {
        1: 'Breakfast',
        2: 'Lunch', 
        3: 'Dinner'
      }
      return slots[slot] || 'Meal'
    },

    getMealSlotClass(slot) {
      return `slot-${slot}`
    },

    getMealImage(mealValue) {
      if (mealValue.image) return mealValue.image
      if (mealValue.imageType) {
        return `https://img.spoonacular.com/recipes/${mealValue.id}-312x231.${mealValue.imageType}`
      }
      return null
    },

    formatItemAmount(measures) {
      if (!measures || !measures.us) return ''
      return `${measures.us.amount} ${measures.us.unitShort}`
    },

    formatDateForAPI(timestamp) {
      const date = new Date(timestamp * 1000)
      return date.toISOString().split('T')[0]
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.spoonacular-integration {
  padding: $spacing-6;
}

.integration-header {
  text-align: center;
  margin-bottom: $spacing-8;

  h2 {
    color: $primary-dark;
    margin-bottom: $spacing-2;
  }

  p {
    color: $gray;
    font-size: 1.1rem;
  }
}

.connection-section {
  margin-bottom: $spacing-8;
}

.connection-card {
  background: $white;
  border: 2px dashed $gray-lighter;
  border-radius: $border-radius-lg;
  padding: $spacing-8;
  text-align: center;
  transition: all 0.3s ease;

  &:hover {
    border-color: $primary;
    transform: translateY(-2px);
  }

  .connection-icon {
    font-size: 3rem;
    color: $primary;
    margin-bottom: $spacing-4;
  }

  h3 {
    margin-bottom: $spacing-3;
    color: $primary-dark;
  }

  p {
    color: $gray;
    margin-bottom: $spacing-6;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
  }

  .connect-btn {
    padding: $spacing-3 $spacing-6;
    font-size: 1.1rem;
    
    i {
      margin-right: $spacing-2;
    }
  }
}

.connecting-status {
  text-align: center;
  padding: $spacing-6;

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid $gray-lighter;
    border-top: 4px solid $primary;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto $spacing-4;
  }
}

.connected-status {
  .status-card {
    background: $success-light;
    border: 1px solid $success;
    border-radius: $border-radius;
    padding: $spacing-4;
    display: flex;
    align-items: center;
    gap: $spacing-3;

    i {
      color: $success;
      font-size: 1.5rem;
    }

    .status-info {
      h4 {
        margin: 0 0 $spacing-1 0;
        color: $success-dark;
      }

      p {
        margin: 0;
        color: $gray;
        font-size: 0.9rem;
      }
    }
  }
}

.spoonacular-features {
  .feature-section {
    background: $white;
    border-radius: $border-radius-lg;
    box-shadow: $shadow;
    margin-bottom: $spacing-6;
    overflow: hidden;

    .section-header {
      background: $gray-lightest;
      padding: $spacing-4 $spacing-6;
      border-bottom: 1px solid $gray-lighter;
      display: flex;
      justify-content: space-between;
      align-items: center;

      h3 {
        margin: 0;
        color: $primary-dark;
        display: flex;
        align-items: center;
        gap: $spacing-2;

        i {
          color: $primary;
        }
      }

      .date-selector {
        display: flex;
        align-items: center;
        gap: $spacing-2;

        label {
          font-size: 0.9rem;
          color: $gray;
        }

        .date-input {
          padding: $spacing-2;
          border: 1px solid $gray-lighter;
          border-radius: $border-radius;
          font-size: 0.9rem;
        }
      }
    }
  }
}

.loading-state {
  text-align: center;
  padding: $spacing-8;

  .spinner {
    width: 30px;
    height: 30px;
    border: 3px solid $gray-lighter;
    border-top: 3px solid $primary;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto $spacing-3;
  }
}

.meal-plan-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: $spacing-4;
  padding: $spacing-6;

  .day-card {
    border: 1px solid $gray-lighter;
    border-radius: $border-radius;
    overflow: hidden;

    .day-header {
      background: $primary-light;
      padding: $spacing-3;
      display: flex;
      justify-content: space-between;
      align-items: center;

      h4 {
        margin: 0;
        color: $primary-dark;
      }

      .calories {
        color: $primary;
        font-weight: 600;
        font-size: 0.9rem;
      }
    }

    .day-meals {
      padding: $spacing-3;

      .meal-item {
        border-left: 4px solid;
        padding: $spacing-3;
        margin-bottom: $spacing-2;
        border-radius: 0 $border-radius $border-radius 0;

        &.slot-1 { border-left-color: #ffeb3b; } // Breakfast - yellow
        &.slot-2 { border-left-color: #ff9800; } // Lunch - orange  
        &.slot-3 { border-left-color: #673ab7; } // Dinner - purple

        .meal-slot {
          font-size: 0.8rem;
          font-weight: 600;
          text-transform: uppercase;
          color: $gray;
          margin-bottom: $spacing-1;
        }

        .meal-content {
          h5 {
            margin: 0 0 $spacing-1 0;
            color: $primary-dark;
          }

          p {
            margin: 0;
            color: $gray;
            font-size: 0.9rem;
          }

          .meal-image {
            width: 100%;
            max-width: 100px;
            height: auto;
            border-radius: $border-radius;
            margin-top: $spacing-2;
          }
        }
      }

      .no-meals {
        text-align: center;
        padding: $spacing-4;
        color: $gray;
      }
    }
  }
}

.shopping-list {
  padding: $spacing-6;

  .aisle-section {
    margin-bottom: $spacing-6;

    h4 {
      color: $primary-dark;
      margin-bottom: $spacing-3;
      padding-bottom: $spacing-2;
      border-bottom: 2px solid $primary-light;
    }

    .items-list {
      list-style: none;
      padding: 0;

      .shopping-item {
        display: flex;
        align-items: center;
        gap: $spacing-2;
        padding: $spacing-2 0;
        border-bottom: 1px solid $gray-lightest;

        input[type="checkbox"] {
          transform: scale(1.2);
        }

        label {
          cursor: pointer;
          flex: 1;
          transition: all 0.3s ease;

          &.checked {
            text-decoration: line-through;
            color: $gray;
          }

          .item-amount {
            color: $gray;
            font-size: 0.9rem;
          }
        }
      }
    }
  }

  .empty-shopping-list {
    text-align: center;
    padding: $spacing-8;
    color: $gray;
  }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;

  .modal-content {
    background: $white;
    border-radius: $border-radius-lg;
    width: 90%;
    max-width: 500px;
    max-height: 90vh;
    overflow-y: auto;

    .modal-header {
      padding: $spacing-4 $spacing-6;
      border-bottom: 1px solid $gray-lighter;
      display: flex;
      justify-content: space-between;
      align-items: center;

      h3 {
        margin: 0;
        color: $primary-dark;
      }

      .close-btn {
        background: none;
        border: none;
        font-size: 1.2rem;
        color: $gray;
        cursor: pointer;
        padding: $spacing-1;

        &:hover {
          color: $primary;
        }
      }
    }

    .modal-body {
      padding: $spacing-6;

      .form-group {
        margin-bottom: $spacing-4;

        label {
          display: block;
          margin-bottom: $spacing-2;
          color: $primary-dark;
          font-weight: 500;
        }

        input, select {
          width: 100%;
          padding: $spacing-3;
          border: 1px solid $gray-lighter;
          border-radius: $border-radius;
          font-size: 1rem;

          &:focus {
            outline: none;
            border-color: $primary;
          }
        }
      }

      .form-actions {
        display: flex;
        gap: $spacing-3;
        justify-content: flex-end;
        margin-top: $spacing-6;
      }
    }
  }
}

.error-message,
.success-message {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1001;

  .alert {
    padding: $spacing-3 $spacing-4;
    border-radius: $border-radius;
    display: flex;
    align-items: center;
    gap: $spacing-2;
    box-shadow: $shadow;
    min-width: 300px;

    &.alert-error {
      background: $error-light;
      color: $error-dark;
      border: 1px solid $error;
    }

    &.alert-success {
      background: $success-light;
      color: $success-dark;
      border: 1px solid $success;
    }

    .close-alert {
      background: none;
      border: none;
      color: inherit;
      cursor: pointer;
      margin-left: auto;
      padding: $spacing-1;

      &:hover {
        opacity: 0.7;
      }
    }
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

// Responsive design
@media (max-width: 768px) {
  .spoonacular-integration {
    padding: $spacing-4;
  }

  .meal-plan-grid {
    grid-template-columns: 1fr;
    padding: $spacing-4;
  }

  .section-header {
    flex-direction: column;
    gap: $spacing-3;
    align-items: stretch !important;

    .date-selector {
      justify-content: center;
    }
  }

  .modal-content {
    width: 95%;
    margin: $spacing-4;
  }
}
</style>