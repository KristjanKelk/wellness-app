<template>
  <div class="progress-chart">
    <div class="chart-header">
      <h3>{{ title }}</h3>
      <div class="chart-controls">
        <select v-model="selectedPeriod" @change="updateChart">
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
          <option value="90">Last 90 days</option>
        </select>
      </div>
    </div>
    
    <div class="chart-container" v-if="chartData && chartData.length > 0">
      <canvas ref="chartCanvas" :width="chartWidth" :height="chartHeight"></canvas>
    </div>
    
    <div class="empty-state" v-else>
      <div class="empty-icon">📊</div>
      <p>No data available for the selected period</p>
      <p class="empty-hint">Start tracking your progress to see charts here!</p>
    </div>
    
    <div class="chart-stats" v-if="chartData && chartData.length > 0">
      <div class="stat-item">
        <span class="stat-label">Current:</span>
        <span class="stat-value">{{ currentValue }}{{ unit }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Goal:</span>
        <span class="stat-value">{{ goalValue }}{{ unit }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Progress:</span>
        <span class="stat-value" :class="progressClass">{{ progressText }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ProgressChart',
  props: {
    title: {
      type: String,
      default: 'Progress Chart'
    },
    data: {
      type: Array,
      default: () => []
    },
    goalValue: {
      type: Number,
      default: 0
    },
    unit: {
      type: String,
      default: ''
    },
    chartType: {
      type: String,
      default: 'line', // 'line' or 'bar'
      validator: value => ['line', 'bar'].includes(value)
    },
    color: {
      type: String,
      default: '#3b82f6'
    }
  },
  data() {
    return {
      selectedPeriod: 30,
      chartWidth: 400,
      chartHeight: 200,
      chart: null
    }
  },
  computed: {
    chartData() {
      const now = new Date();
      const cutoffDate = new Date(now.getTime() - (this.selectedPeriod * 24 * 60 * 60 * 1000));
      
      return this.data
        .filter(item => new Date(item.date) >= cutoffDate)
        .sort((a, b) => new Date(a.date) - new Date(b.date));
    },
    currentValue() {
      if (!this.chartData || this.chartData.length === 0) return 0;
      const latest = this.chartData[this.chartData.length - 1];
      return latest.value || 0;
    },
    progressText() {
      if (!this.goalValue || !this.currentValue) return 'No goal set';
      
      const diff = this.currentValue - this.goalValue;
      const percentage = Math.abs((diff / this.goalValue) * 100).toFixed(1);
      
      if (Math.abs(diff) < 0.1) {
        return 'Goal achieved! 🎉';
      } else if (diff > 0) {
        return `${percentage}% above goal`;
      } else {
        return `${percentage}% below goal`;
      }
    },
    progressClass() {
      if (!this.goalValue || !this.currentValue) return '';
      
      const diff = Math.abs(this.currentValue - this.goalValue);
      const tolerance = this.goalValue * 0.05; // 5% tolerance
      
      if (diff <= tolerance) {
        return 'progress-success';
      } else if (this.currentValue < this.goalValue) {
        return 'progress-warning';
      } else {
        return 'progress-info';
      }
    }
  },
  mounted() {
    this.initChart();
    window.addEventListener('resize', this.handleResize);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize);
    if (this.chart) {
      this.chart.destroy();
    }
  },
  watch: {
    chartData: {
      handler() {
        this.$nextTick(() => {
          this.updateChart();
        });
      },
      deep: true
    }
  },
  methods: {
    initChart() {
      const canvas = this.$refs.chartCanvas;
      if (!canvas) return;
      
      const ctx = canvas.getContext('2d');
      this.updateCanvasSize();
      this.drawChart(ctx);
    },
    
    updateCanvasSize() {
      const container = this.$refs.chartCanvas?.parentElement;
      if (container) {
        this.chartWidth = container.offsetWidth - 40;
        this.chartHeight = Math.min(250, Math.max(200, this.chartWidth * 0.4));
      }
    },
    
    drawChart(ctx) {
      if (!this.chartData || this.chartData.length === 0) return;
      
      const canvas = ctx.canvas;
      const padding = 40;
      const chartArea = {
        left: padding,
        right: canvas.width - padding,
        top: padding,
        bottom: canvas.height - padding
      };
      
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Calculate data bounds
      const values = this.chartData.map(d => d.value);
      const minValue = Math.min(...values, this.goalValue);
      const maxValue = Math.max(...values, this.goalValue);
      const valueRange = maxValue - minValue || 1;
      
      // Helper functions
      const getX = (index) => {
        return chartArea.left + (index / (this.chartData.length - 1)) * (chartArea.right - chartArea.left);
      };
      
      const getY = (value) => {
        return chartArea.bottom - ((value - minValue) / valueRange) * (chartArea.bottom - chartArea.top);
      };
      
      // Draw grid lines
      ctx.strokeStyle = '#e5e7eb';
      ctx.lineWidth = 1;
      for (let i = 0; i <= 5; i++) {
        const y = chartArea.top + (i / 5) * (chartArea.bottom - chartArea.top);
        ctx.beginPath();
        ctx.moveTo(chartArea.left, y);
        ctx.lineTo(chartArea.right, y);
        ctx.stroke();
      }
      
      // Draw goal line
      if (this.goalValue) {
        const goalY = getY(this.goalValue);
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(chartArea.left, goalY);
        ctx.lineTo(chartArea.right, goalY);
        ctx.stroke();
        ctx.setLineDash([]);
        
        // Goal label
        ctx.fillStyle = '#ef4444';
        ctx.font = '12px sans-serif';
        ctx.fillText(`Goal: ${this.goalValue}${this.unit}`, chartArea.right - 80, goalY - 5);
      }
      
      // Draw data line/bars
      if (this.chartType === 'line') {
        ctx.strokeStyle = this.color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        this.chartData.forEach((point, index) => {
          const x = getX(index);
          const y = getY(point.value);
          
          if (index === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        });
        ctx.stroke();
        
        // Draw points
        ctx.fillStyle = this.color;
        this.chartData.forEach((point, index) => {
          const x = getX(index);
          const y = getY(point.value);
          
          ctx.beginPath();
          ctx.arc(x, y, 4, 0, 2 * Math.PI);
          ctx.fill();
        });
      } else {
        // Bar chart
        const barWidth = (chartArea.right - chartArea.left) / this.chartData.length * 0.8;
        ctx.fillStyle = this.color;
        
        this.chartData.forEach((point, index) => {
          const x = getX(index) - barWidth / 2;
          const y = getY(point.value);
          const height = chartArea.bottom - y;
          
          ctx.fillRect(x, y, barWidth, height);
        });
      }
      
      // Draw axes labels
      ctx.fillStyle = '#6b7280';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      
      // X-axis labels (dates)
      this.chartData.forEach((point, index) => {
        if (index % Math.ceil(this.chartData.length / 5) === 0) {
          const x = getX(index);
          const date = new Date(point.date);
          const label = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
          ctx.fillText(label, x, chartArea.bottom + 20);
        }
      });
      
      // Y-axis labels
      ctx.textAlign = 'right';
      for (let i = 0; i <= 5; i++) {
        const value = minValue + (i / 5) * valueRange;
        const y = chartArea.top + (i / 5) * (chartArea.bottom - chartArea.top);
        ctx.fillText(value.toFixed(1) + this.unit, chartArea.left - 10, y + 4);
      }
    },
    
    updateChart() {
      this.$nextTick(() => {
        const canvas = this.$refs.chartCanvas;
        if (canvas) {
          const ctx = canvas.getContext('2d');
          this.updateCanvasSize();
          this.drawChart(ctx);
        }
      });
    },
    
    handleResize() {
      this.updateChart();
    }
  }
}
</script>

<style scoped>
.progress-chart {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.chart-controls select {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  font-size: 14px;
  color: #374151;
  cursor: pointer;
}

.chart-controls select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.chart-container {
  margin: 20px 0;
  overflow: hidden;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #6b7280;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 8px 0;
}

.empty-hint {
  font-size: 0.875rem;
  color: #9ca3af;
}

.chart-stats {
  display: flex;
  justify-content: space-around;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.stat-value {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
}

.stat-value.progress-success {
  color: #059669;
}

.stat-value.progress-warning {
  color: #d97706;
}

.stat-value.progress-info {
  color: #3b82f6;
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .chart-stats {
    flex-direction: column;
    gap: 12px;
  }
  
  .stat-item {
    flex-direction: row;
    justify-content: space-between;
  }
}
</style>