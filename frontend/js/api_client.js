// frontend/js/api_client.js
import { getParticipantId } from './modules/session.js';
import { AppConfig } from './modules/config.js';

async function post(endpoint, body) {
  const participantId = getParticipantId();
  if (!participantId) {
        // 如果没有ID，说明会话已丢失，应强制返回注册页
        window.location.href = '/index.html';
        throw new Error("Session not found. Redirecting to login.");
  }

  // 自动在请求体中注入participant_id
  const fullBody = { ...body, participant_id: participantId };

  const response = await fetch(`${AppConfig.api_base_url}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(fullBody),
  });
  return response.json();
}
// ... 实现 get, put, delete 等方法
async function get(endpoint) {
  const participantId = getParticipantId();
  if (!participantId) {
        // 如果没有ID，说明会话已丢失，应强制返回注册页
        window.location.href = '/index.html';
        throw new Error("Session not found. Redirecting to login.");
  }
  const response = await fetch(`${AppConfig.api_base_url}${endpoint}?participant_id=${participantId}`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
  });
  return response.json();
}
// TODO:实现put, delete等方法