<!-- src/components/meal-planning/NutritionalAnalysisModal.vue -->
<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content analysis-modal" @click.stop>
      <div class="modal-header">
        <div class="header-content">
          <h2>
            <i class="fas fa-chart-line"></i>
            AI Nutritional Analysis
          </h2>
          <p>{{ formatPlanType(mealPlan.plan_type) }} Plan - {{ formatDateRange(mealPlan.start_date, mealPlan.end_date) }}</p>
        </div>
        <button @click="$emit('close')" class="close-btn">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="modal-body">
        <!-- Loading State -->
        <div v-if="analysis.loading" class="loading-state">
          <div class="loading-spinner"></div>
          <h3>AI is Analyzing Your Meal Plan</h3>
          <p>{{ analysis.message }}</p>
        </div>

        <!-- Error State -->
        <div v-else-if="analysis.error" class="error-state">
          <i class="fas fa-exclamation-triangle"></i>
          <h3>Analysis Unavailable</h3>
          <p>{{ analysis.message }}</p>
        </div>

        <!-- Analysis Results -->
        <div v-else class="analysis-results">
          <!-- Overall Score -->
          <div class="overall-score-section">
            <div class="score-circle">
              <svg viewBox="0 0 100 100" class="circular-progress">
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  class="circle-bg"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  class="circle-progress"
                  :style="`stroke-dasharray: ${analysis.overall_score * 2.827}, 282.7`"
                />
              </svg>
              <div class="score-content">
                <span class="score-number">{{ analysis.overall_score || 0 }}</span>
                <span class="score-label">Overall Score</span>
              </div>
            </div>
            <div class="score-description">
              <h3>Nutritional Quality Assessment</h3>
              <p>{{ getScoreDescription(analysis.overall_score) }}</p>
            </div>
          </div>

          <!-- Nutritional Adequacy -->
          <div class="analysis-section">
            <h3>
              <i class="fas fa-balance-scale"></i>
              Nutritional Adequacy
            </h3>
            <div class="adequacy-grid" v-if="analysis.nutritional_adequacy">
              <div
                v-for="(nutrient, key) in analysis.nutritional_adequacy"
                :key="key"
                class="nutrient-card"
                :class="getAdequacyClass(nutrient.status)"
              >
                <div class="nutrient-header">
                  <span class="nutrient-name">{{ formatNutrientName(key) }}</span>
                  <span class="nutrient-status">{{ formatStatus(nutrient.status) }}</span>
                </div>
                <div class="nutrient-progress">
                  <div class="progress-bar">
                    <div
                      class="progress-fill"
                      :style="`width: ${Math.min(nutrient.percentage_of_target || 0, 150)}%`"
                    ></div>
                  </div>
                  <span class="percentage">{{ nutrient.percentage_of_target || 0 }}% of target</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Meal Distribution -->
          <div class="analysis-section" v-if="analysis.meal_distribution">
            <h3>
              <i class="fas fa-clock"></i>
              Meal Distribution
            </h3>
            <div class="distribution-chart">
              <div class="distribution-bars">
                <div class="meal-bar">
                  <span class="meal-label">Breakfast</span>
                  <div class="bar">
                    <div
                      class="bar-fill breakfast"
                      :style="`width: ${analysis.meal_distribution.breakfast_percentage || 0}%`"
                    ></div>
                  </div>
                  <span class="percentage">{{ analysis.meal_distribution.breakfast_percentage || 0 }}%</span>
                </div>
                <div class="meal-bar">
                  <span class="meal-label">Lunch</span>
                  <div class="bar">
                    <div
                      class="bar-fill lunch"
                      :style="`width: ${analysis.meal_distribution.lunch_percentage || 0}%`"
                    ></div>
                  </div>
                  <span class="percentage">{{ analysis.meal_distribution.lunch_percentage || 0 }}%</span>
                </div>
                <div class="meal-bar">
                  <span class="meal-label">Dinner</span>
                  <div class="bar">
                    <div
                      class="bar-fill dinner"
                      :style="`width: ${analysis.meal_distribution.dinner_percentage || 0}%`"
                    ></div>
                  </div>
                  <span class="percentage">{{ analysis.meal_distribution.dinner_percentage || 0 }}%</span>
                </div>
              </div>
              <div class="distribution-rating">
                <span class="rating-label">Balance Rating:</span>
                <span class="rating-value" :class="getRatingClass(analysis.meal_distribution.balance_rating)">
                  {{ formatRating(analysis.meal_distribution.balance_rating) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Variety Analysis -->
          <div class="analysis-section" v-if="analysis.variety_analysis">
            <h3>
              <i class="fas fa-seedling"></i>
              Variety & Diversity
            </h3>
            <div class="variety-metrics">
              <div class="variety-item">
                <span class="metric-label">Cuisine Diversity:</span>
                <span class="metric-badge" :class="getVarietyClass(analysis.variety_analysis.cuisine_diversity)">
                  {{ formatRating(analysis.variety_analysis.cuisine_diversity) }}
                </span>
              </div>
              <div class="variety-item">
                <span class="metric-label">Ingredient Variety:</span>
                <span class="metric-badge" :class="getVarietyClass(analysis.variety_analysis.ingredient_variety)">
                  {{ formatRating(analysis.variety_analysis.ingredient_variety) }}
                </span>
              </div>
              <div class="variety-item">
                <span class="metric-label">Cooking Methods:</span>
                <span class="metric-badge" :class="getVarietyClass(analysis.variety_analysis.cooking_method_diversity)">
                  {{ formatRating(analysis.variety_analysis.cooking_method_diversity) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Health Highlights -->
          <div class="analysis-section" v-if="analysis.health_highlights && analysis.health_highlights.length">
            <h3>
              <i class="fas fa-star"></i>
              Health Highlights
            </h3>
            <div class="highlights-list">
              <div
                v-for="(highlight, index) in analysis.health_highlights"
                :key="index"
                class="highlight-item"
              >
                <i class="fas fa-check-circle"></i>
                <span>{{ highlight }}</span>
              </div>
            </div>
          </div>

          <!-- Recommendations -->
          <div class="analysis-section" v-if="analysis.recommendations && analysis.recommendations.length">
            <h3>
              <i class="fas fa-lightbulb"></i>
              AI Recommendations
            </h3>
            <div class="recommendations-list">
              <div
                v-for="(recommendation, index) in analysis.recommendations"
                :key="index"
                class="recommendation-item"
              >
                <i class="fas fa-arrow-right"></i>
                <span>{{ recommendation }}</span>
              </div>
            </div>
          </div>

          <!-- Areas for Improvement -->
          <div class="analysis-section" v-if="analysis.areas_for_improvement && analysis.areas_for_improvement.length">
            <h3>
              <i class="fas fa-target"></i>
              Areas for Improvement
            </h3>
            <div class="improvements-list">
              <div
                v-for="(improvement, index) in analysis.areas_for_improvement"
                :key="index"
                class="improvement-item"
              >
                <i class="fas fa-exclamation-circle"></i>
                <span>{{ improvement }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="$emit('close')" class="btn btn-secondary">Close Analysis</button>
        <button @click="downloadReport" class="btn btn-primary" :disabled="analysis.loading || analysis.error">
          <i class="fas fa-download"></i>
          Download Report
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NutritionalAnalysisModal',
  props: {
    analysis: {
      type: Object,
      required: true
    },
    mealPlan: {
      type: Object,
      required: true
    }
  },
  emits: ['close'],
  methods: {
    formatPlanType(type) {
      return type.charAt(0).toUpperCase() + type.slice(1)
    },

    formatDateRange(startDate, endDate) {
      const start = new Date(startDate).toLocaleDateString()
      const end = new Date(endDate).toLocaleDateString()

      if (startDate === endDate) {
        return start
      }
      return `${start} - ${end}`
    },

    getScoreDescription(score) {
      if (score >= 90) return "Excellent nutritional balance! Your meal plan meets all dietary guidelines."
      if (score >= 80) return "Very good nutritional quality with minor areas for optimization."
      if (score >= 70) return "Good nutritional foundation with some room for improvement."
      if (score >= 60) return "Adequate nutrition but several areas could be enhanced."
      return "Significant nutritional improvements recommended."
    },

    formatNutrientName(key) {
      const names = {
        'calories': 'Calories',
        'protein': 'Protein',
        'carbs': 'Carbohydrates',
        'fat': 'Fat',
        'fiber': 'Fiber',
        'sodium': 'Sodium'
      }
      return names[key] || key.charAt(0).toUpperCase() + key.slice(1)
    },

    formatStatus(status) {
      const statuses = {
        'adequate': 'Adequate',
        'insufficient': 'Low',
        'excessive': 'High',
        'too_high': 'Too High',
        'too_low': 'Too Low',
        'within_range': 'Good',
        'balanced': 'Balanced'
      }
      return statuses[status] || status.replace('_', ' ').toUpperCase()
    },

    formatRating(rating) {
      if (!rating) return 'N/A'
      return rating.charAt(0).toUpperCase() + rating.slice(1)
    },

    getAdequacyClass(status) {
      const classes = {
        'adequate': 'adequate',
        'within_range': 'adequate',
        'balanced': 'adequate',
        'insufficient': 'insufficient',
        'too_low': 'insufficient',
        'excessive': 'excessive',
        'too_high': 'excessive'
      }
      return classes[status] || 'neutral'
    },

    getRatingClass(rating) {
      const classes = {
        'excellent': 'excellent',
        'very_good': 'very-good',
        'good': 'good',
        'fair': 'fair',
        'poor': 'poor'
      }
      return classes[rating] || 'neutral'
    },

    getVarietyClass(variety) {
      const classes = {
        'excellent': 'excellent',
        'very_good': 'very-good',
        'good': 'good',
        'fair': 'fair',
        'poor': 'poor'
      }
      return classes[variety] || 'neutral'
    },

    downloadReport() {
      // Generate a simple text report
      let report = `AI Nutritional Analysis Report\n`
      report += `================================\n\n`
      report += `Meal Plan: ${this.formatPlanType(this.mealPlan.plan_type)} Plan\n`
      report += `Date Range: ${this.formatDateRange(this.mealPlan.start_date, this.mealPlan.end_date)}\n`
      report += `Generated: ${new Date().toLocaleDateString()}\n\n`

      report += `Overall Score: ${this.analysis.overall_score || 'N/A'}/100\n\n`

      if (this.analysis.health_highlights && this.analysis.health_highlights.length) {
        report += `Health Highlights:\n`
        this.analysis.health_highlights.forEach(highlight => {
          report += `• ${highlight}\n`
        })
        report += `\n`
      }

      if (this.analysis.recommendations && this.analysis.recommendations.length) {
        report += `AI Recommendations:\n`
        this.analysis.recommendations.forEach(rec => {
          report += `• ${rec}\n`
        })
        report += `\n`
      }

      if (this.analysis.areas_for_improvement && this.analysis.areas_for_improvement.length) {
        report += `Areas for Improvement:\n`
        this.analysis.areas_for_improvement.forEach(improvement => {
          report += `• ${improvement}\n`
        })
      }

      // Create and download the file
      const blob = new Blob([report], { type: 'text/plain' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `nutrition-analysis-${this.mealPlan.start_date}.txt`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    }
  }
}
</script>

<style lang="scss" scoped>
$primary: #007bff;
$success: #28a745;
$warning: #ffc107;
$danger: #dc3545;
$info: #17a2b8;
$gray: #6c757d;
$gray-light: #adb5bd;
$gray-lighter: #e9ecef;
$white: #ffffff;

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
  padding: 20px;
}

.analysis-modal {
  background: $white;
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
  align-items: flex-start;
  padding: 24px 32px;
  border-bottom: 1px solid $gray-lighter;
  background: linear-gradient(135deg, rgba($primary, 0.05), rgba($primary, 0.02));

  .header-content {
    h2 {
      margin: 0 0 8px 0;
      font-size: 1.6rem;
      color: #333;
      display: flex;
      align-items: center;
      gap: 12px;

      i {
        color: $primary;
      }
    }

    p {
      margin: 0;
      color: $gray;
      font-size: 1rem;
    }
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 8px;
    border-radius: 8px;
    color: $gray;
    transition: all 0.2s ease;

    &:hover {
      background: rgba($gray, 0.1);
      color: #333;
    }
  }
}

.modal-body {
  padding: 32px;
}

// Loading State
.loading-state {
  text-align: center;
  padding: 60px 20px;

  .loading-spinner {
    width: 50px;
    height: 50px;
    border: 4px solid $gray-lighter;
    border-left: 4px solid $primary;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 24px;
  }

  h3 {
    margin: 0 0 12px 0;
    color: #333;
    font-size: 1.3rem;
  }

  p {
    margin: 0;
    color: $gray;
    font-size: 1rem;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

// Error State
.error-state {
  text-align: center;
  padding: 60px 20px;

  i {
    font-size: 3rem;
    color: $warning;
    margin-bottom: 24px;
    display: block;
  }

  h3 {
    margin: 0 0 12px 0;
    color: #333;
    font-size: 1.3rem;
  }

  p {
    margin: 0;
    color: $gray;
    font-size: 1rem;
  }
}

// Analysis Results
.analysis-results {
  .analysis-section {
    margin-bottom: 40px;

    &:last-child {
      margin-bottom: 0;
    }

    h3 {
      margin: 0 0 20px 0;
      font-size: 1.2rem;
      color: #333;
      display: flex;
      align-items: center;
      gap: 12px;
      padding-bottom: 12px;
      border-bottom: 2px solid $gray-lighter;

      i {
        color: $primary;
        font-size: 1.1rem;
      }
    }
  }
}

// Overall Score Section
.overall-score-section {
  display: flex;
  align-items: center;
  gap: 32px;
  margin-bottom: 40px;
  padding: 24px;
  background: linear-gradient(135deg, rgba($success, 0.05), rgba($primary, 0.05));
  border-radius: 12px;
  border: 1px solid rgba($primary, 0.1);
}

.score-circle {
  position: relative;
  width: 120px;
  height: 120px;
  flex-shrink: 0;

  .circular-progress {
    width: 100%;
    height: 100%;
    transform: rotate(-90deg);

    .circle-bg {
      fill: none;
      stroke: $gray-lighter;
      stroke-width: 8;
    }

    .circle-progress {
      fill: none;
      stroke: $success;
      stroke-width: 8;
      stroke-linecap: round;
      transition: stroke-dasharray 0.6s ease;
    }
  }

  .score-content {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;

    .score-number {
      display: block;
      font-size: 2rem;
      font-weight: 700;
      color: $success;
      line-height: 1;
    }

    .score-label {
      display: block;
      font-size: 0.8rem;
      color: $gray;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-top: 4px;
    }
  }
}

.score-description {
  flex: 1;

  h3 {
    margin: 0 0 12px 0;
    font-size: 1.3rem;
    color: #333;
  }

  p {
    margin: 0;
    color: $gray;
    font-size: 1rem;
    line-height: 1.5;
  }
}

// Nutritional Adequacy
.adequacy-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.nutrient-card {
  padding: 20px;
  border-radius: 12px;
  border: 2px solid;
  transition: all 0.3s ease;

  &.adequate {
    border-color: rgba($success, 0.3);
    background: rgba($success, 0.05);
  }

  &.insufficient {
    border-color: rgba($warning, 0.3);
    background: rgba($warning, 0.05);
  }

  &.excessive {
    border-color: rgba($danger, 0.3);
    background: rgba($danger, 0.05);
  }

  &.neutral {
    border-color: $gray-lighter;
    background: rgba($gray, 0.03);
  }

  .nutrient-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .nutrient-name {
      font-weight: 600;
      color: #333;
      font-size: 1rem;
    }

    .nutrient-status {
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.5px;

      .adequate & {
        background: $success;
        color: white;
      }

      .insufficient & {
        background: $warning;
        color: white;
      }

      .excessive & {
        background: $danger;
        color: white;
      }

      .neutral & {
        background: $gray;
        color: white;
      }
    }
  }

  .nutrient-progress {
    .progress-bar {
      height: 8px;
      background: rgba(0, 0, 0, 0.1);
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 8px;

      .progress-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.6s ease;

        .adequate & { background: $success; }
        .insufficient & { background: $warning; }
        .excessive & { background: $danger; }
        .neutral & { background: $gray; }
      }
    }

    .percentage {
      font-size: 0.9rem;
      color: $gray;
      font-weight: 500;
    }
  }
}

// Meal Distribution
.distribution-chart {
  .distribution-bars {
    margin-bottom: 20px;
  }

  .meal-bar {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 12px;

    .meal-label {
      min-width: 80px;
      font-weight: 500;
      color: #333;
      font-size: 0.9rem;
    }

    .bar {
      flex: 1;
      height: 24px;
      background: $gray-lighter;
      border-radius: 12px;
      overflow: hidden;
      position: relative;

      .bar-fill {
        height: 100%;
        border-radius: 12px;
        transition: width 0.6s ease;

        &.breakfast { background: linear-gradient(90deg, #FF6B6B, #FF8E53); }
        &.lunch { background: linear-gradient(90deg, #4ECDC4, #44A08D); }
        &.dinner { background: linear-gradient(90deg, #A8EDEA, #FED6E3); }
      }
    }

    .percentage {
      min-width: 50px;
      text-align: right;
      font-weight: 500;
      color: #333;
      font-size: 0.9rem;
    }
  }

  .distribution-rating {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    background: rgba($primary, 0.05);
    border-radius: 8px;

    .rating-label {
      font-weight: 500;
      color: #333;
    }

    .rating-value {
      padding: 4px 12px;
      border-radius: 6px;
      font-weight: 600;
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 0.5px;

      &.excellent { background: $success; color: white; }
      &.very-good { background: #20c997; color: white; }
      &.good { background: $info; color: white; }
      &.fair { background: $warning; color: white; }
      &.poor { background: $danger; color: white; }
      &.neutral { background: $gray; color: white; }
    }
  }
}

// Variety Analysis
.variety-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.variety-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba($primary, 0.03);
  border-radius: 8px;
  border: 1px solid rgba($primary, 0.1);
  flex: 1;
  min-width: 200px;

  .metric-label {
    font-weight: 500;
    color: #333;
  }

  .metric-badge {
    padding: 4px 12px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;

    &.excellent { background: $success; color: white; }
    &.very-good { background: #20c997; color: white; }
    &.good { background: $info; color: white; }
    &.fair { background: $warning; color: white; }
    &.poor { background: $danger; color: white; }
    &.neutral { background: $gray; color: white; }
  }
}

// Lists
.highlights-list, .recommendations-list, .improvements-list {
  .highlight-item, .recommendation-item, .improvement-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 16px;
    margin-bottom: 8px;
    border-radius: 8px;
    transition: background-color 0.2s ease;

    &:hover {
      background: rgba($primary, 0.03);
    }

    i {
      margin-top: 2px;
      flex-shrink: 0;
    }

    span {
      color: #333;
      line-height: 1.5;
    }
  }
}

.highlights-list .highlight-item i {
  color: $success;
}

.recommendations-list .recommendation-item i {
  color: $primary;
}

.improvements-list .improvement-item i {
  color: $warning;
}

// Modal Footer
.modal-footer {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 24px 32px;
  border-top: 1px solid $gray-lighter;
  background: rgba($gray, 0.02);

  .btn {
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 500;
    font-size: 0.95rem;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 8px;

    &.btn-secondary {
      background: $gray-lighter;
      color: #333;

      &:hover {
        background: darken($gray-lighter, 10%);
      }
    }

    &.btn-primary {
      background: $primary;
      color: white;

      &:hover:not(:disabled) {
        background: darken($primary, 10%);
        transform: translateY(-1px);
      }

      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
    }

    i {
      font-size: 0.9rem;
    }
  }
}

// Responsive Design
@media (max-width: 768px) {
  .modal-overlay {
    padding: 10px;
  }

  .analysis-modal {
    max-height: 95vh;
  }

  .modal-header {
    padding: 20px 24px;

    .header-content h2 {
      font-size: 1.4rem;
    }
  }

  .modal-body {
    padding: 24px 20px;
  }

  .overall-score-section {
    flex-direction: column;
    text-align: center;
    gap: 20px;
  }

  .adequacy-grid {
    grid-template-columns: 1fr;
  }

  .variety-metrics {
    flex-direction: column;
  }

  .variety-item {
    min-width: auto;
  }

  .modal-footer {
    padding: 20px 24px;
    flex-direction: column;

    .btn {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>