import { encryptWithTimestamp, decryptWithTimestamp, simpleParamDecode } from './encryption.js';

/**
 * 安全的页面跳转
 * @param {string} url - 目标URL
 * @param {string} id - 要传递的参数
 * @param {boolean} encryptData - 是否加密参数
 */
export function navigateTo(url, id = null, encryptData = true) {
    let targetUrl = url;
    
    if (id) {
        let paramValue;
        if (encryptData) {
            paramValue = encryptWithTimestamp(id);
        } else {
            // 未加密时使用简单的时间戳
            paramValue = btoa(`${id}|${Date.now()}`);
        }
        targetUrl += `?topic=${encodeURIComponent(paramValue)}`;
    }
    
    window.location.href = targetUrl;
}

/**
 * 获取URL参数
 * @param {string} name - 参数名
 * @param {boolean} decryptData - 是否尝试解密参数
 * @returns {Object|string} 参数值
 */
export function getUrlParam(name, decryptData = true) {
    const urlParams = new URLSearchParams(window.location.search);
    const param = urlParams.get(name);
    
    if (!param) return null;
    
    if (decryptData) {
        try {
            // 先解码URL编码
            const decodedParam = decodeURIComponent(param);
            
            // 尝试解密
            const result = decryptWithTimestamp(decodedParam);
            
            if (result.isValid) {
                return result;
            } else {
                // 如果解密失败或过期，尝试备用解析方法
                console.warn('解密失败或参数过期，尝试备用解析');
                return simpleParamDecode(decodedParam);
            }
        } catch (error) {
            console.warn('参数解密失败，使用备用解析:', error);
            return simpleParamDecode(param);
        }
    }
    
    // 不解密时直接返回
    return param;
}

/**
 * 返回上一页
 */
export function goBack() {
    if (window.history.length > 1) {
        window.history.back();
    } else {
        // 如果没有历史记录，跳转到首页
        window.location.href = '/index.html';
    }
}

/**
 * 设置标题点击事件
 * @param {string} targetUrl - 点击标题后跳转的URL
 */
export function setupHeaderTitle(targetUrl) {
    const headerTitle = document.getElementById('headerTitle');
    if (headerTitle) {
        headerTitle.style.cursor = 'pointer';
        headerTitle.addEventListener('click', () => {
            navigateTo(targetUrl);
        });
    }
}

/**
 * 设置返回按钮
 */
export function setupBackButton() {
    const backButton = document.getElementById('backButton');
    if (backButton) {
        backButton.addEventListener('click', goBack);
    }
}

/**
 * 调试函数：显示当前URL参数信息
 */
export function debugUrlParams() {
    const params = new URLSearchParams(window.location.search);
    console.log('URL参数:', Object.fromEntries(params.entries()));
}