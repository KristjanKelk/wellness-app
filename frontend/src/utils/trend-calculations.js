// src/utils/trend-calculations.js

/**
 * Simple linear regression implementation for calculating trend lines
 */
export class LinearRegression {
  constructor(x, y) {
    this.x = x;
    this.y = y;
    this.m = 0; // slope
    this.b = 0; // y-intercept
  }

  /**
   * Train the model to find the best fit line
   */
  train() {
    if (this.x.length <= 1 || this.y.length <= 1) {
      console.warn('Not enough data points for regression');
      return;
    }

    // Calculate means
    const meanX = this.x.reduce((sum, val) => sum + val, 0) / this.x.length;
    const meanY = this.y.reduce((sum, val) => sum + val, 0) / this.y.length;

    // Calculate slope and y-intercept
    let numerator = 0;
    let denominator = 0;

    for (let i = 0; i < this.x.length; i++) {
      numerator += (this.x[i] - meanX) * (this.y[i] - meanY);
      denominator += (this.x[i] - meanX) ** 2;
    }

    if (denominator === 0) {
      console.warn('Cannot calculate slope (denominator is zero)');
      return;
    }

    this.m = numerator / denominator;
    this.b = meanY - this.m * meanX;
  }

  /**
   * Predict y value for a given x
   * @param {number} x - The x value to predict
   * @returns {number} - The predicted y value
   */
  predict(x) {
    return this.m * x + this.b;
  }

  /**
   * Calculate the coefficient of determination (R²)
   * @returns {number} - R² value between 0 and 1
   */
  calculateR2() {
    if (this.x.length <= 1 || this.y.length <= 1) {
      return 0;
    }

    const meanY = this.y.reduce((sum, val) => sum + val, 0) / this.y.length;

    let ssRes = 0; // Sum of squares of residuals
    let ssTot = 0; // Total sum of squares

    for (let i = 0; i < this.x.length; i++) {
      const prediction = this.predict(this.x[i]);
      ssRes += (this.y[i] - prediction) ** 2;
      ssTot += (this.y[i] - meanY) ** 2;
    }

    if (ssTot === 0) {
      return 1; // Perfect fit if all values are the same
    }

    return 1 - (ssRes / ssTot);
  }
}

/**
 * Calculate the average rate of change over a period
 * @param {Array} data - Array of data points with x and y values
 * @param {number} periodDays - Period in days to calculate rate
 * @returns {number} - Average change rate per period
 */
export function calculateRateOfChange(data, periodDays) {
  if (!data || data.length < 2) return 0;

  // Sort data by x (timestamp)
  const sortedData = [...data].sort((a, b) => a.x - b.x);

  // Calculate total time span in days
  const timeSpanDays = (sortedData[sortedData.length - 1].x - sortedData[0].x) / (1000 * 60 * 60 * 24);

  // If time span is too short, return 0
  if (timeSpanDays < 1) return 0;

  // Calculate total change
  const totalChange = sortedData[sortedData.length - 1].y - sortedData[0].y;

  // Calculate daily change rate
  const dailyRate = totalChange / timeSpanDays;

  // Return rate for specified period
  return dailyRate * periodDays;
}

/**
 * Estimate time to reach a target value based on current trend
 * @param {Array} data - Array of data points with x and y values
 * @param {number} targetValue - Target y value to reach
 * @returns {Date|null} - Estimated date to reach target or null if not possible
 */
export function estimateTimeToTarget(data, targetValue) {
  if (!data || data.length < 2) return null;

  // Create regression model
  const x = data.map(point => point.x);
  const y = data.map(point => point.y);

  const regression = new LinearRegression(x, y);
  regression.train();

  // Check if the slope is near zero or in wrong direction
  const latestY = y[y.length - 1];
  const isTargetHigher = targetValue > latestY;

  // If slope is too small or trending in wrong direction
  if (Math.abs(regression.m) < 0.000001 ||
      (isTargetHigher && regression.m < 0) ||
      (!isTargetHigher && regression.m > 0)) {
    return null;
  }

  // Calculate time to reach target
  const latestX = x[x.length - 1];
  const timeToTarget = (targetValue - regression.predict(latestX)) / regression.m;

  // Create estimated date
  return new Date(latestX + timeToTarget);
}