<template>
  <div class="ai-assistant-container">
    <!-- Floating Chat Button -->
    <transition name="fade">
      <button
        v-if="!isChatOpen"
        @click="openChat"
        class="chat-button"
        aria-label="Open AI Assistant"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M8 10H8.01M12 10H12.01M16 10H16.01M9 16H5C3.89543 16 3 15.1046 3 14V6C3 4.89543 3.89543 4 5 4H19C20.1046 4 21 4.89543 21 6V14C21 15.1046 20.1046 16 19 16H14L9 21V16Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span class="notification-dot" v-if="hasNewMessage"></span>
      </button>
    </transition>

    <!-- Chat Window -->
    <transition name="slide-up">
      <div v-if="isChatOpen" class="chat-window">
        <!-- Chat Header -->
        <div class="chat-header">
          <div class="header-left">
            <div class="assistant-avatar" aria-hidden="true">
              <i class="fa-solid fa-heart-pulse"></i>
            </div>
            <div class="header-content">
              <h3>Wellness Assistant</h3>
              <p class="header-subtitle">Ask me about your health & nutrition</p>
            </div>
          </div>
          <div class="header-actions">
            <button @click="toggleResponseMode" class="mode-toggle" :title="preferences.response_mode === 'concise' ? 'Response mode: concise (fast summaries)' : 'Response mode: detailed (in-depth answers)'"><i v-if="preferences.response_mode === 'concise'" class="fa-solid fa-bolt"></i><i v-else class="fa-solid fa-file-lines"></i></button>
            <button @click="clearConversation" class="clear-button" title="Delete conversation"><i class="fa-solid fa-trash-can"></i></button>
            <button @click="closeChat" class="close-button" aria-label="Close chat">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M6 14L14 6M6 6L14 14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Chat Messages -->
        <div class="chat-messages" ref="messagesContainer">
          <!-- Welcome Message -->
          <div v-if="messages.length === 0" class="welcome-message">
            <h4>Hello {{ userName }}! 👋</h4>
            <p>I'm your wellness assistant. I can help you with:</p>
            <div class="example-categories">
              <button 
                v-for="category in exampleCategories.slice(0, 4)" 
                :key="category.name"
                @click="sendExampleMessage(category.examples[0])"
                class="example-chip"
              >
                {{ category.name }}
              </button>
            </div>
          </div>

          <!-- Messages -->
          <div v-for="message in messages" :key="message.id" :class="['message', message.role]">
            <div class="message-content">
              <div v-html="formatMessage(message.content)" class="message-text"></div>
              <div v-if="message.chart" class="chart-container">
                <div :id="'chart-' + message.chart.id" class="chart"></div>
                <p class="chart-summary">{{ message.chart.summary }}</p>
              </div>
              <div class="message-time">{{ formatTime(message.created_at) }}</div>
            </div>
          </div>

          <!-- Visualization Suggestions -->
          <div v-if="visualizationSuggestions.length > 0" class="viz-suggestions">
            <p>Would you like to see a visualization?</p>
            <button 
              v-for="(suggestion, index) in visualizationSuggestions" 
              :key="index"
              @click="generateVisualization(suggestion.type)"
              class="viz-button"
            >
              {{ suggestion.prompt }}
            </button>
          </div>



          <!-- Loading Indicator -->
          <div v-if="isLoading" class="loading-message">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>

        <!-- Input Area -->
        <div class="chat-input">
          <textarea
            v-model="inputMessage"
            @keydown.enter.prevent="handleEnterKey"
            placeholder="Ask about your health, nutrition, or wellness..."
            class="message-input"
            :disabled="isLoading"
            rows="1"
          ></textarea>
          <button 
            @click="sendMessage" 
            :disabled="!inputMessage.trim() || isLoading"
            class="send-button"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M2 10L8 4L7 10H13L7 16L8 10H2Z" fill="currentColor"/>
            </svg>
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import aiAssistantService from '@/services/aiAssistantService';
import Plotly from 'plotly.js-basic-dist';

export default {
  name: 'AIAssistant',
  data() {
    return {
      isChatOpen: false,
      isLoading: false,
      inputMessage: '',
      messages: [],
      conversationId: null,
      hasNewMessage: false,
      preferences: {
        response_mode: 'concise'
      },
      exampleCategories: [],
      visualizationSuggestions: [],
      chartIdCounter: 0
    };
  },
  computed: {
    ...mapGetters(['user']),
    userName() {
      return this.user?.first_name || this.user?.username || 'there';
    }
  },
  mounted() {
    this.loadExamples();
    this.loadPreferences();
  },
  methods: {
    openChat() {
      this.isChatOpen = true;
      this.hasNewMessage = false;
      this.loadActiveConversation();
      this.$nextTick(() => {
        this.scrollToBottom();
      });
    },
    
    closeChat() {
      this.isChatOpen = false;
    },
    
    async clearConversation() {
      if (!confirm('Are you sure you want to clear this conversation?')) {
        return;
      }
      
      try {
        if (this.conversationId) {
          const response = await aiAssistantService.clearConversation(this.conversationId);
          this.conversationId = response.new_conversation.id;
        }
        this.messages = [];
        this.visualizationSuggestions = [];
      } catch (error) {
        console.error('Error clearing conversation:', error);
      }
    },
    
    async loadActiveConversation() {
      try {
        const conversation = await aiAssistantService.getActiveConversation();
        this.conversationId = conversation.id;
        
        if (conversation.message_count > 0) {
          const history = await aiAssistantService.getConversationHistory(conversation.id);
          this.messages = history.messages;
        }
      } catch (error) {
        console.error('Error loading conversation:', error);
      }
    },
    
    async loadExamples() {
      try {
        const response = await aiAssistantService.getExamples();
        this.exampleCategories = response.categories;
      } catch (error) {
        console.error('Error loading examples:', error);
      }
    },
    
    async loadPreferences() {
      try {
        const prefs = await aiAssistantService.getPreferences();
        this.preferences = prefs;
      } catch (error) {
        console.error('Error loading preferences:', error);
      }
    },
    
    async toggleResponseMode() {
      const newMode = this.preferences.response_mode === 'concise' ? 'detailed' : 'concise';
      try {
        const updated = await aiAssistantService.updatePreferences({ response_mode: newMode });
        this.preferences = updated;
      } catch (error) {
        console.error('Error updating preferences:', error);
      }
    },
    
    handleEnterKey(event) {
      if (!event.shiftKey) {
        this.sendMessage();
      }
    },
    
    sendExampleMessage(example) {
      this.inputMessage = example;
      this.sendMessage();
    },
    
    async sendMessage() {
      if (!this.inputMessage.trim() || this.isLoading) {
        return;
      }
      
      const userMessage = {
        id: Date.now(),
        role: 'user',
        content: this.inputMessage,
        created_at: new Date().toISOString()
      };
      
      this.messages.push(userMessage);
      this.inputMessage = '';
      this.isLoading = true;
      this.visualizationSuggestions = [];
      this.scrollToBottom();
      
      try {
        const response = await aiAssistantService.sendMessage(
          userMessage.content,
          this.conversationId
        );
        
        if (response.success) {
          this.conversationId = response.conversation_id;
          
          const assistantMessage = {
            id: response.message_id || Date.now() + 1,
            role: 'assistant',
            content: response.message,
            created_at: new Date().toISOString()
          };
          
          this.messages.push(assistantMessage);
          
          // Handle visualization suggestions
          if (response.visualization_suggestions) {
            this.visualizationSuggestions = response.visualization_suggestions;
          }
          
          if (!this.isChatOpen) {
            this.hasNewMessage = true;
          }
        } else if (response.message) {
          this.showError(response.message);
        } else {
          this.showError('An error occurred');
        }
      } catch (error) {
        console.error('Error sending message:', error);
        this.showError('Failed to send message. Please try again.');
      } finally {
        this.isLoading = false;
        this.scrollToBottom();
      }
    },
    
    async generateVisualization(type) {
      this.isLoading = true;
      this.visualizationSuggestions = [];
      
      try {
        const chartData = await aiAssistantService.generateVisualization(type);
        
        if (chartData.chart_config) {
          this.chartIdCounter++;
          const chartMessage = {
            id: Date.now() + this.chartIdCounter,
            role: 'assistant',
            content: chartData.description || 'Here’s your visualization.',
            created_at: new Date().toISOString(),
            chart: {
              id: this.chartIdCounter,
              config: chartData.chart_config,
              summary: chartData.summary
            }
          };
          this.messages.push(chartMessage);
          
          this.$nextTick(() => {
            const chartDiv = document.getElementById(`chart-${chartMessage.chart.id}`);
            if (chartDiv) {
              Plotly.newPlot(chartDiv, chartMessage.chart.config.data, chartMessage.chart.config.layout, {
                responsive: true,
                displayModeBar: false,
                displaylogo: false
              });
            }
            this.scrollToBottom();
          });
        }
      } catch (error) {
        console.error('Error generating visualization:', error);
        this.showError('Failed to generate chart. Please try again.');
      } finally {
        this.isLoading = false;
      }
    },
    
    showError(message) {
      const errorMessage = {
        id: Date.now() + 2,
        role: 'assistant',
        content: `${message}`,
        created_at: new Date().toISOString()
      };
      this.messages.push(errorMessage);
    },
    
    formatMessage(content) {
      // Convert markdown-style formatting to HTML
      return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>')
        .replace(/•/g, '&bull;')
        .replace(/- /g, '&bull; ');
    },
    
    formatTime(timestamp) {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      });
    },
    
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer;
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      });
    }
  }
};
</script>

<style scoped>
.ai-assistant-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
}

/* Floating Chat Button */
.chat-button {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  position: relative;
}

.chat-button:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.2);
}

.notification-dot {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 12px;
  height: 12px;
  background: #ef4444;
  border-radius: 50%;
  border: 2px solid white;
}

/* Chat Window */
.chat-window {
  position: fixed;
  bottom: 90px;
  right: 20px;
  width: 400px;
  height: 600px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

@media (max-width: 768px) {
  .chat-window {
    bottom: 0;
    right: 0;
    width: 100%;
    height: 100vh;
    border-radius: 0;
  }
}

/* Chat Header */
.chat-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.assistant-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.header-content h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-subtitle {
  margin: 4px 0 0 0;
  font-size: 14px;
  opacity: 0.9;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-actions button {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: white;
}

.header-actions button:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Chat Messages */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f8f9fa;
}

.welcome-message {
  text-align: center;
  padding: 40px 20px;
}

.welcome-message h4 {
  margin: 0 0 12px 0;
  font-size: 20px;
  color: #1f2937;
}

.welcome-message p {
  margin: 0 0 20px 0;
  color: #6b7280;
}

.example-categories {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.example-chip {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  padding: 8px 16px;
  font-size: 14px;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.2s;
}

.example-chip:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

/* Messages */
.message {
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease;
}

.message.user .message-content {
  background: #667eea;
  color: white;
  margin-left: auto;
  max-width: 80%;
}

.message.assistant .message-content {
  background: white;
  color: #1f2937;
  max-width: 80%;
}

.message-content {
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.message-text {
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
}

.message-text strong {
  font-weight: 600;
}

.message-time {
  font-size: 11px;
  opacity: 0.7;
  margin-top: 4px;
}

/* Visualization Suggestions */
.viz-suggestions {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.viz-suggestions p {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #4b5563;
}

.viz-button {
  display: block;
  width: 100%;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 8px;
  font-size: 14px;
  color: #1f2937;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.viz-button:hover {
  background: #e5e7eb;
}

/* Chart Container */
.chart-container {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
}

.chart {
  width: 100%;
  height: 340px;
}

.chart-summary {
  margin: 12px 0 0 0;
  font-size: 13px;
  color: #6b7280;
  text-align: center;
}

/* Loading Indicator */
.loading-message {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 16px;
}

.typing-indicator {
  background: white;
  padding: 16px 20px;
  border-radius: 12px;
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #9ca3af;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

/* Chat Input */
.chat-input {
  padding: 16px;
  background: white;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 14px;
  resize: none;
  outline: none;
  transition: border-color 0.2s;
  min-height: 40px;
  max-height: 120px;
}

.message-input:focus {
  border-color: #667eea;
}

.send-button {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: #667eea;
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.send-button:hover:not(:disabled) {
  background: #5a67d8;
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Animations */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(20px);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>