// 前端配置文件
const FrontendConfig = {
    // 开发环境配置
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
    
    // 获取后端URL
    getBackendUrl() {
        return this.getCurrentConfig().backendUrl;
    },
    
    // 获取API基础URL
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