<!-- src/components/meal-planning/RecipeDetailModal.vue -->
<template>
  <div class="recipe-modal-overlay" @click.self="$emit('close')">
    <div class="recipe-modal" @click.stop>
      <div class="modal-header">
        <h2>{{ recipe.title }}</h2>
        <button class="close-btn" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div class="modal-body">
        <div class="image-wrapper" v-if="recipe.image_url">
          <img :src="recipe.image_url" :alt="recipe.title" @error="imageError" />
        </div>
        <p class="summary" v-if="recipe.summary" v-html="recipe.summary"></p>
        <div class="ingredients-section" v-if="recipe.ingredients_data">
          <h3>Ingredients</h3>
          <ul>
            <li v-for="(ing, idx) in recipe.ingredients_data" :key="idx">
              {{ formatIngredient(ing) }}
            </li>
          </ul>
        </div>
        <div class="instructions-section" v-if="normalizedInstructions.length">
          <h3>Instructions</h3>
          <ol>
            <li v-for="(step, idx) in normalizedInstructions" :key="idx">
              {{ step.description || step }}
            </li>
          </ol>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" @click="$emit('close')">Close</button>
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
      const qty = ing.quantity !== undefined ? ing.quantity : ''
      const unit = ing.unit || ''
      return `${qty}${unit ? ' ' + unit : ''} ${ing.name}`.trim()
    },
    imageError(event) {
      event.target.style.display = 'none'
    }
  }
}
</script>

<style lang="scss" scoped>
.recipe-modal-overlay {
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
  padding: 20px;
}

.recipe-modal {
  background: #fff;
  border-radius: 16px;
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  border-bottom: 1px solid #e9ecef;

  h2 {
    margin: 0;
    font-size: 1.6rem;
    color: #333;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 8px;
    border-radius: 8px;
    color: #6c757d;
    transition: all 0.2s ease;

    &:hover {
      background: rgba(0, 0, 0, 0.05);
      color: #333;
    }
  }
}

.modal-body {
  padding: 32px;

  .image-wrapper {
    text-align: center;
    margin-bottom: 16px;

    img {
      max-width: 100%;
      border-radius: 12px;
    }
  }

  .summary {
    margin-bottom: 24px;
  }

  .ingredients-section,
  .instructions-section {
    margin-bottom: 24px;

    h3 {
      margin-bottom: 8px;
      font-size: 1.2rem;
    }

    ul,
    ol {
      margin: 0;
      padding-left: 20px;
    }
  }
}

.modal-footer {
  padding: 16px 32px;
  border-top: 1px solid #e9ecef;
  text-align: right;
}
</style>
