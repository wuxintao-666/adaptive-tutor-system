// frontend/js/pages/registration.js
import { saveParticipantId, checkAndRedirect } from '../modules/session.js';

// 页面加载时先检查是否已有会话
checkAndRedirect();

const startButton = document.getElementById('start-button');
const usernameInput = document.getElementById('username-input');

startButton.addEventListener('click', async () => {
  // ... (按钮禁用、输入校验等UI逻辑) ...
  const username = usernameInput.value.trim();
  const response = await fetch('/api/v1/session/initiate', { 
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username }),
  });
  const result = await response.json();

  if (result.code === 200 || result.code === 201) {
        saveParticipantId(result.data.participant_id);
        // 注册成功后，跳转到“前测问卷”页面，这是科研流程的一部分
        window.location.href = `/survey.html?type=pre-test`;
  } else {
        alert(result.message);
  }
});