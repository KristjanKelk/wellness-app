import apiClient from './http.service';

class AssistantService {
  sendMessage({ sessionId, message, mode = 'concise' }) {
    const payload = { message, mode };
    if (sessionId) payload.session_id = sessionId;
    return apiClient.post('assistant/message/', payload).then(res => res.data);
  }
}

export default new AssistantService();