// frontend/js/modules/config.js

// A globally accessible object to hold configuration.
export const AppConfig = {
  api_base_url: "/api/v1",
  backend_port: 8000,  // 默认端口，会被后端配置覆盖
  //  model_name_for_display:null
};

/**
 * Fetches configuration from the backend.
 * Should be called once when the application starts.
 */
export async function initializeConfig() {
  try {
    // We construct the URL manually here for the initial config fetch
    // 明确指定后端端口，而不是依赖可能未定义的AppConfig.backend_port
    const backendPort = 8000;
    const configUrl = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
      ? `http://localhost:${backendPort}/api/v1/config`
      : '/api/v1/config';
      
    const response = await fetch(configUrl);
    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message);
    }

    Object.assign(AppConfig, result.data);
    console.log("Frontend configuration loaded:", AppConfig);
  } catch (error) {
    console.error("Could not initialize frontend configuration:", error);
    // Fallback to default port if config load fails in development
    // 确保即使配置加载失败，也有默认值
    if (!AppConfig.backend_port) {
      AppConfig.backend_port = 8000;
    }
  }
}

/**
 * 构建完整的后端API URL
 * @param {string} endpoint - API endpoint (e.g., /chat/completions)
 * @returns {string} 完整的API URL
 */
export function buildBackendUrl(endpoint = '') {
  const path = `${AppConfig.api_base_url}${endpoint}`;
  
  // 对于相对路径，构建完整的URL
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // 开发环境，使用配置的端口，确保有默认值
    const backendPort = AppConfig.backend_port || 8000;
    return `http://localhost:${backendPort}${path}`;
  } else {
    // 生产环境，使用相对路径
    return path;
  }
}

// 将函数添加到全局window对象，以便在非模块脚本中使用
window.buildBackendUrl = buildBackendUrl;