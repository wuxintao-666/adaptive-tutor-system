// 前端配置文件
// 注意：这个配置文件主要用于向后兼容，新的配置应该使用 modules/config.js 中的 AppConfig
const FrontendConfig = {
    // 开发环境配置（使用默认值，会被后端配置覆盖）
    development: {
        backendUrl: 'http://localhost:8000',
        apiBaseUrl: 'http://localhost:8000/api/v1'
    },
    
    // 生产环境配置
    production: {
        backendUrl: '', // 生产环境URL
        apiBaseUrl: '/api/v1'
    },
    
    // 获取当前环境配置
    getCurrentConfig() {
        // 根据当前域名判断环境
        const hostname = window.location.hostname;
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return this.development;
        } else {
            return this.production;
        }
    },
    
    // 获取后端URL（已废弃，请使用 modules/config.js 中的 buildBackendUrl）
    getBackendUrl() {
        return this.getCurrentConfig().backendUrl;
    },
    
    // 获取API基础URL（已废弃，请使用 modules/config.js 中的 AppConfig.api_base_url）
    getApiBaseUrl() {
        return this.getCurrentConfig().apiBaseUrl;
    }
};

// 导出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FrontendConfig;
} else {
    window.FrontendConfig = FrontendConfig;
} 