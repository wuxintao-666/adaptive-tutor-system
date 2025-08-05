// frontend/js/modules/config.js

// A globally accessible object to hold configuration.
export const AppConfig = {
  api_base_url: "/api/v1",
  model_name_for_display: "Qwen-Turbo (魔搭)"
};

/**
 * Fetches configuration from the backend.
 * Should be called once when the application starts.
 */
export async function initializeConfig() {
  try {
    const response = await fetch('/api/v1/config/config');
    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message);
    }

    Object.assign(AppConfig, result.data);
    console.log("Frontend configuration loaded:", AppConfig);
  } catch (error) {
    console.error("Could not initialize frontend configuration:", error);
    // 使用默认配置，不抛出错误
    console.log("Using default configuration:", AppConfig);
  }
}

// 不自动初始化，只在明确调用时初始化
// 这样可以避免在模块导入时就尝试加载配置