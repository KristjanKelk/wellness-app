// services/aiAssistantService.js
import api from './http.service';

const AI_ASSISTANT_BASE_URL = '/ai-assistant';

export default {
  // Conversation Management
  async getActiveConversation() {
    const response = await api.get(`${AI_ASSISTANT_BASE_URL}/conversations/active/`);
    return response.data;
  },

  async sendMessage(message, conversationId = null) {
    const response = await api.post(`${AI_ASSISTANT_BASE_URL}/conversations/send_message/`, {
      message,
      conversation_id: conversationId
    });
    return response.data;
  },

  async getConversationHistory(conversationId, limit = 50) {
    const response = await api.get(`${AI_ASSISTANT_BASE_URL}/conversations/${conversationId}/history/`, {
      params: { limit }
    });
    return response.data;
  },

  async clearConversation(conversationId) {
    const response = await api.post(`${AI_ASSISTANT_BASE_URL}/conversations/${conversationId}/clear/`);
    return response.data;
  },

  // User Preferences
  async getPreferences() {
    const response = await api.get(`${AI_ASSISTANT_BASE_URL}/preferences/current/`);
    return response.data;
  },

  async updatePreferences(preferences) {
    const response = await api.post(`${AI_ASSISTANT_BASE_URL}/preferences/current/`, preferences);
    return response.data;
  },

  // Examples
  async getExamples() {
    const response = await api.get(`${AI_ASSISTANT_BASE_URL}/examples/examples/`);
    return response.data;
  },

  // Visualizations
  async generateVisualization(request, timePeriod = 'month') {
    // If caller passes a known chart type, send as chart_type for more reliable server routing
    const knownTypes = new Set(['weight_trend', 'protein_comparison', 'macronutrient_breakdown', 'calorie_trend', 'activity_summary', 'wellness_score']);
    const payload = {
      request,
      time_period: timePeriod
    };
    if (typeof request === 'string' && knownTypes.has(request)) {
      payload.chart_type = request;
    }
    const response = await api.post(`${AI_ASSISTANT_BASE_URL}/visualizations/generate/`, payload);
    return response.data;
  },

  async getAvailableCharts() {
    const response = await api.get(`${AI_ASSISTANT_BASE_URL}/visualizations/available_charts/`);
    return response.data;
  }
};