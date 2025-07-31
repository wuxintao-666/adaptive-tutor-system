import { initializeConfig, AppConfig } from './js/modules/config.js';

window.addEventListener('DOMContentLoaded', async () => {
  await initializeConfig();
  // 此处可安全使用 AppConfig.model_name_for_display
  console.log('当前模型：', AppConfig.model_name_for_display);
});