// frontend/js/api_client.js
import { getParticipantId } from './modules/session.js';
import { buildBackendUrl } from './modules/config.js';

async function post(endpoint, body) {
  const participantId = getParticipantId();
  if (!participantId) {
        // 如果没有ID，说明会话已丢失，应强制返回注册页
        window.location.href = '/index.html';
        throw new Error("Session not found. Redirecting to login.");
  }

  // 自动在请求体中注入participant_id
  const fullBody = { ...body, participant_id: participantId };

  const response = await fetch(buildBackendUrl(endpoint), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(fullBody),
  });
  return response.json();
}

// ... 实现 get, put, delete 等方法
async function get(endpoint, params = {}) {
  const participantId = getParticipantId();
  if (!participantId) {
        // 如果没有ID，说明会话已丢失，应强制返回注册页
        window.location.href = '/index.html';
        throw new Error("Session not found. Redirecting to login.");
  }
  
  // 自动添加participant_id到查询参数
  params.participant_id = participantId;
  
  const queryString = new URLSearchParams(params).toString();
  const url = `${buildBackendUrl(endpoint)}?${queryString}`;
  
  const response = await fetch(url, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
  });
  return response.json();
}

// 挂载到window对象上，以便全局访问
window.apiClient = {
  post,
  get
};

// 默认导出
export default {
  post,
  get
};