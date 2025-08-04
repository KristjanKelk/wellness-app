<template>
  <div class="shopping-list-modal">
    <div class="modal-overlay" @click="$emit('close')"></div>
    <div class="modal-content">
      <div class="modal-header">
        <h2 class="modal-title">
          <i class="fas fa-shopping-cart"></i>
          Shopping List
        </h2>
        <div class="modal-actions">
          <button 
            @click="printShoppingList" 
            class="btn btn-secondary"
            title="Print Shopping List"
          >
            <i class="fas fa-print"></i>
          </button>
          <button @click="$emit('close')" class="btn btn-ghost">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>

      <div class="modal-body">
        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>Generating your shopping list...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="error-state">
          <div class="error-icon">
            <i class="fas fa-exclamation-triangle"></i>
          </div>
          <h3>Unable to Generate Shopping List</h3>
          <p>{{ error }}</p>
          <button @click="retry" class="btn btn-primary">
            <i class="fas fa-redo"></i>
            Try Again
          </button>
        </div>

        <!-- Shopping List Content -->
        <div v-else-if="shoppingList" class="shopping-list-content">
          <!-- Metadata -->
          <div class="shopping-list-meta">
            <div class="meta-item">
              <i class="fas fa-info-circle"></i>
              <span>{{ shoppingList.metadata.total_items }} items</span>
            </div>
            <div class="meta-item" v-if="shoppingList.metadata.recipe_names">
              <i class="fas fa-utensils"></i>
              <span>{{ shoppingList.metadata.recipe_names.length }} recipes</span>
            </div>
            <div class="meta-item" v-if="shoppingList.metadata.generated_from === 'meal_plan'">
              <i class="fas fa-calendar"></i>
              <span>{{ formatDateRange() }}</span>
            </div>
          </div>

          <!-- Shopping Categories -->
          <div class="shopping-categories">
            <div 
              v-for="(category, categoryKey) in sortedCategories" 
              :key="categoryKey"
              class="shopping-category"
              :class="{ 'category-completed': isCategoryCompleted(category) }"
            >
              <div class="category-header" @click="toggleCategory(categoryKey)">
                <div class="category-info">
                  <span class="category-icon">{{ category.icon }}</span>
                  <h3 class="category-name">{{ category.name }}</h3>
                  <span class="item-count">({{ getCompletedCount(category) }}/{{ category.item_count }})</span>
                </div>
                <div class="category-toggle">
                  <i class="fas" :class="collapsedCategories[categoryKey] ? 'fa-chevron-down' : 'fa-chevron-up'"></i>
                </div>
              </div>

              <div 
                v-show="!collapsedCategories[categoryKey]"
                class="category-items"
              >
                <div 
                  v-for="(item, itemIndex) in category.items" 
                  :key="itemIndex"
                  class="shopping-item"
                  :class="{ 'item-checked': item.checked }"
                >
                  <label class="item-checkbox">
                    <input 
                      type="checkbox" 
                      v-model="item.checked"
                      @change="updateProgress"
                    >
                    <span class="checkmark"></span>
                  </label>
                  <div class="item-details">
                    <span class="item-name" :class="{ 'strikethrough': item.checked }">
                      {{ item.name }}
                    </span>
                    <span class="item-quantity">{{ item.quantity }}</span>
                    <div v-if="item.notes && item.notes.length > 0" class="item-notes">
                      <small>Additional: {{ item.notes.join(', ') }}</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Progress Bar -->
          <div class="progress-section">
            <div class="progress-info">
              <span>Progress: {{ completedItems }}/{{ totalItems }} items</span>
              <span class="progress-percentage">{{ progressPercentage }}%</span>
            </div>
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: progressPercentage + '%' }"
              ></div>
            </div>
          </div>

          <!-- Recipe Names (if from recipes) -->
          <div v-if="shoppingList.metadata.recipe_names" class="recipe-list">
            <h4>Recipes included:</h4>
            <div class="recipe-chips">
              <span 
                v-for="recipeName in shoppingList.metadata.recipe_names" 
                :key="recipeName"
                class="recipe-chip"
              >
                {{ recipeName }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ShoppingListModal',
  props: {
    shoppingList: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      collapsedCategories: {},
      completedItems: 0,
      totalItems: 0
    }
  },
  computed: {
    sortedCategories() {
      if (!this.shoppingList?.categories) return {}
      
      // Sort categories by their order property
      const categories = this.shoppingList.categories
      return Object.keys(categories)
        .sort((a, b) => categories[a].order - categories[b].order)
        .reduce((sorted, key) => {
          sorted[key] = categories[key]
          return sorted
        }, {})
    },
    progressPercentage() {
      if (this.totalItems === 0) return 0
      return Math.round((this.completedItems / this.totalItems) * 100)
    }
  },
  watch: {
    shoppingList: {
      handler() {
        this.updateProgress()
        this.initializeCategories()
      },
      immediate: true
    }
  },
  methods: {
    initializeCategories() {
      if (!this.shoppingList?.categories) return
      
      // Initialize collapsed state for categories
      Object.keys(this.shoppingList.categories).forEach(categoryKey => {
        if (!(categoryKey in this.collapsedCategories)) {
          this.collapsedCategories[categoryKey] = false
        }
      })
    },
    
    toggleCategory(categoryKey) {
      this.collapsedCategories[categoryKey] = !this.collapsedCategories[categoryKey]
    },
    
    updateProgress() {
      if (!this.shoppingList?.categories) return
      
      let completed = 0
      let total = 0
      
      Object.values(this.shoppingList.categories).forEach(category => {
        category.items.forEach(item => {
          total++
          if (item.checked) completed++
        })
      })
      
      this.completedItems = completed
      this.totalItems = total
    },
    
    isCategoryCompleted(category) {
      return category.items.every(item => item.checked)
    },
    
    getCompletedCount(category) {
      return category.items.filter(item => item.checked).length
    },
    
    formatDateRange() {
      if (!this.shoppingList?.metadata) return ''
      
      const start = new Date(this.shoppingList.metadata.start_date).toLocaleDateString()
      const end = new Date(this.shoppingList.metadata.end_date).toLocaleDateString()
      
      if (start === end) {
        return start
      }
      return `${start} - ${end}`
    },
    
    printShoppingList() {
      const printContent = this.generatePrintContent()
      const printWindow = window.open('', '_blank')
      
      printWindow.document.write(`
        <html>
          <head>
            <title>Shopping List</title>
            <style>
              body { font-family: Arial, sans-serif; margin: 20px; }
              h1 { color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px; }
              h2 { color: #374151; margin-top: 25px; margin-bottom: 10px; }
              .category-section { margin-bottom: 20px; }
              .item { margin: 5px 0; padding: 5px; }
              .item-name { font-weight: 500; }
              .item-quantity { color: #6b7280; margin-left: 10px; }
              .meta-info { background: #f3f4f6; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
              ul { list-style-type: none; padding-left: 0; }
              li { margin: 8px 0; }
              .checkbox { width: 15px; height: 15px; border: 1px solid #ccc; display: inline-block; margin-right: 10px; }
              @media print {
                .no-print { display: none; }
              }
            </style>
          </head>
          <body>
            ${printContent}
          </body>
        </html>
      `)
      
      printWindow.document.close()
      printWindow.print()
      printWindow.close()
    },
    
    generatePrintContent() {
      if (!this.shoppingList) return ''
      
      let html = '<h1>🛒 Shopping List</h1>'
      
      // Metadata
      if (this.shoppingList.metadata) {
        html += '<div class="meta-info">'
        html += `<p><strong>Total Items:</strong> ${this.shoppingList.metadata.total_items}</p>`
        
        if (this.shoppingList.metadata.recipe_names) {
          html += `<p><strong>Recipes:</strong> ${this.shoppingList.metadata.recipe_names.join(', ')}</p>`
        }
        
        if (this.shoppingList.metadata.generated_from === 'meal_plan') {
          html += `<p><strong>Meal Plan Period:</strong> ${this.formatDateRange()}</p>`
        }
        
        html += '</div>'
      }
      
      // Categories
      Object.entries(this.sortedCategories).forEach(([, category]) => {
        html += `<div class="category-section">`
        html += `<h2>${category.icon} ${category.name}</h2>`
        html += '<ul>'
        
        category.items.forEach(item => {
          html += '<li>'
          html += '<span class="checkbox"></span>'
          html += `<span class="item-name">${item.name}</span>`
          html += `<span class="item-quantity">${item.quantity}</span>`
          if (item.notes && item.notes.length > 0) {
            html += `<br><small>Additional: ${item.notes.join(', ')}</small>`
          }
          html += '</li>'
        })
        
        html += '</ul></div>'
      })
      
      return html
    },
    
    retry() {
      this.$emit('retry')
    }
  }
}
</script>

<style scoped>
.shopping-list-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(5px);
}

.modal-content {
  position: relative;
  background: white;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  color: white;
}

.modal-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-actions {
  display: flex;
  gap: 8px;
}

.modal-body {
  flex: 1;
  overflow: auto;
  padding: 24px;
}

/* Loading State */
.loading-state {
  text-align: center;
  padding: 60px 20px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top: 4px solid #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Error State */
.error-state {
  text-align: center;
  padding: 60px 20px;
}

.error-icon {
  font-size: 3rem;
  color: #ef4444;
  margin-bottom: 20px;
}

.error-state h3 {
  color: #374151;
  margin-bottom: 12px;
}

.error-state p {
  color: #6b7280;
  margin-bottom: 24px;
}

/* Shopping List Content */
.shopping-list-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #475569;
  font-size: 0.875rem;
}

.meta-item i {
  color: #2563eb;
}

/* Shopping Categories */
.shopping-categories {
  margin-bottom: 24px;
}

.shopping-category {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 16px;
  overflow: hidden;
  transition: all 0.2s ease;
}

.category-completed {
  background: #f0fdf4;
  border-color: #16a34a;
}

.category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: #f9fafb;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.category-header:hover {
  background: #f3f4f6;
}

.category-completed .category-header {
  background: #dcfce7;
}

.category-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.category-icon {
  font-size: 1.25rem;
}

.category-name {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #374151;
}

.item-count {
  color: #6b7280;
  font-size: 0.875rem;
}

.category-toggle i {
  color: #6b7280;
  transition: transform 0.2s ease;
}

.category-items {
  padding: 0 16px 16px;
}

/* Shopping Items */
.shopping-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 6px;
  transition: background-color 0.2s ease;
  margin-bottom: 8px;
}

.shopping-item:hover {
  background: #f8fafc;
}

.item-checked {
  background: #f0fdf4;
}

.item-checkbox {
  position: relative;
  cursor: pointer;
  margin-top: 2px;
}

.item-checkbox input[type="checkbox"] {
  opacity: 0;
  position: absolute;
}

.checkmark {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid #d1d5db;
  border-radius: 4px;
  position: relative;
  transition: all 0.2s ease;
}

.item-checkbox input[type="checkbox"]:checked + .checkmark {
  background: #16a34a;
  border-color: #16a34a;
}

.item-checkbox input[type="checkbox"]:checked + .checkmark::after {
  content: "✓";
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.item-details {
  flex: 1;
}

.item-name {
  display: block;
  font-weight: 500;
  color: #374151;
  margin-bottom: 4px;
  transition: all 0.2s ease;
}

.strikethrough {
  text-decoration: line-through;
  color: #9ca3af;
}

.item-quantity {
  color: #6b7280;
  font-size: 0.875rem;
}

.item-notes {
  margin-top: 4px;
  color: #6b7280;
  font-size: 0.75rem;
}

/* Progress Section */
.progress-section {
  margin-bottom: 24px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 0.875rem;
  color: #374151;
}

.progress-percentage {
  font-weight: 600;
  color: #2563eb;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #2563eb 0%, #16a34a 100%);
  transition: width 0.3s ease;
}

/* Recipe List */
.recipe-list {
  padding: 16px;
  background: #fef3c7;
  border-radius: 8px;
  border: 1px solid #f59e0b;
}

.recipe-list h4 {
  margin: 0 0 12px 0;
  color: #92400e;
  font-size: 0.875rem;
  font-weight: 600;
}

.recipe-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.recipe-chip {
  background: #fbbf24;
  color: #92400e;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 0.75rem;
  font-weight: 500;
}

/* Buttons */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn:hover {
  transform: translateY(-1px);
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-secondary {
  background: #6b7280;
  color: white;
}

.btn-secondary:hover {
  background: #4b5563;
}

.btn-ghost {
  background: transparent;
  color: white;
}

.btn-ghost:hover {
  background: rgba(255, 255, 255, 0.1);
}

/* Responsive Design */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    max-height: 95vh;
  }
  
  .modal-header {
    padding: 16px;
  }
  
  .modal-title {
    font-size: 1.25rem;
  }
  
  .modal-body {
    padding: 16px;
  }
  
  .shopping-list-meta {
    flex-direction: column;
    gap: 8px;
  }
  
  .category-header {
    padding: 12px;
  }
  
  .category-name {
    font-size: 1rem;
  }
  
  .shopping-item {
    padding: 8px;
  }
}
</style>