// ==================== 文档模块 ====================

// 统一的模块状态管理
const ModuleState = {
    currentTopicData: null,  // 存储当前主题的完整数据
    isInitialized: false,    // 防重复初始化标志
    initPromise: null        // 初始化Promise，防止重复调用
};

// 加载主题内容
async function loadTopicContent(topicId) {
    // 防止重复调用
    if (ModuleState.initPromise) {
        console.log('[DocsModule] 主题内容正在加载中，等待完成');
        return ModuleState.initPromise;
    }
    
    // 创建加载Promise
    ModuleState.initPromise = (async () => {
        try {
            // 优先从全局数据存储获取数据
            if (window.GlobalDataStore && window.GlobalDataStore.isDataLoaded('topicContent')) {
                console.log('[DocsModule] 从全局数据存储获取主题内容');
                const topicData = window.GlobalDataStore.getData('topicContent');
                ModuleState.currentTopicData = topicData;
                renderTopicContent();
                return topicData;
            }
            
            // 检查是否有原始API响应数据
            if (window.GlobalDataStore && window.GlobalDataStore.isDataLoaded('rawApiResponse')) {
                console.log('[DocsModule] 从全局数据存储的原始响应中获取主题内容');
                const rawResponse = window.GlobalDataStore.getData('rawApiResponse');
                
                if (rawResponse && rawResponse.code === 200 && rawResponse.data) {
                    const topicData = rawResponse.data;
                    ModuleState.currentTopicData = topicData;
                    
                    // 将数据存储到全局存储中，避免重复解析
                    window.GlobalDataStore.setData('topicContent', topicData);
                    
                    renderTopicContent();
                    return topicData;
                }
            }
            
            // 如果全局数据存储中完全没有数据，使用默认内容
            console.log('[DocsModule] 全局数据存储中完全没有数据，使用默认内容');
            
            // 使用默认内容
            const defaultTopicData = {
                title: `主题 ${topicId}`,
                levels: [
                    { level: 1, description: "基础概念：适合零基础入门，掌握核心概念与基本语法。" },
                    { level: 2, description: "详细解析：理解常见场景与组合用法，提升实践能力。" },
                    { level: 3, description: "实际应用：深入机制与性能优化，形成系统化认知。" },
                    { level: 4, description: "原理分析：综合实战与拓展题，检验与突破现有水平。" }
                ]
            };
            
            ModuleState.currentTopicData = defaultTopicData;
            renderTopicContent();
            
            // 返回默认数据
            return defaultTopicData;
            
        } catch (e) {
            console.warn('无法获取主题内容，使用默认内容:', e.message);
            
            // 使用默认内容
            const defaultTopicData = {
                title: `主题 ${topicId}`,
                levels: [
                    { level: 1, description: "基础概念：适合零基础入门，掌握核心概念与基本语法。" },
                    { level: 2, description: "详细解析：理解常见场景与组合用法，提升实践能力。" },
                    { level: 3, description: "实际应用：深入机制与性能优化，形成系统化认知。" },
                    { level: 4, description: "原理分析：综合实战与拓展题，检验与突破现有水平。" }
                ]
            };
            
            ModuleState.currentTopicData = defaultTopicData;
            renderTopicContent();
            
            // 返回默认数据
            return defaultTopicData;
        } finally {
            // 清除Promise，允许重新调用
            ModuleState.initPromise = null;
        }
    })();
    
    return ModuleState.initPromise;
}

// 渲染主题内容
function renderTopicContent() {
    console.log('[DocsModule] 开始渲染主题内容');
    
    const knowledgeContent = document.getElementById('knowledge-content');
    if (!knowledgeContent) {
        console.warn('[DocsModule] knowledge-content 元素不存在');
        return;
    }
    
    // 如果没有主题数据，不清空现有内容
    if (!ModuleState.currentTopicData) {
        console.log('[DocsModule] 没有主题数据，保持现有内容');
        return;
    }
    
    const topicData = ModuleState.currentTopicData;
    const levels = topicData.levels || [];
    
    console.log('[DocsModule] 主题数据:', topicData);
    console.log('[DocsModule] 等级数据:', levels);
    
    // 如果没有等级数据，不清空现有内容
    if (levels.length === 0) {
        console.log('[DocsModule] 没有等级数据，保持现有内容');
        return;
    }
    
    // 更新现有卡片的内容文本
    levels.forEach((level, index) => {
        console.log(`[DocsModule] 更新等级 ${level.level} 的内容:`, level.description);
        
        const card = knowledgeContent.querySelector(`.level-card[data-level="${level.level}"]`);
        if (card) {
            const contentText = card.querySelector('.content-text');
            if (contentText) {
                contentText.textContent = level.description || '暂无内容';
                console.log(`[DocsModule] 等级 ${level.level} 内容更新成功`);
            } else {
                console.warn(`[DocsModule] 等级 ${level.level} 的 content-text 元素未找到`);
            }
        } else {
            console.warn(`[DocsModule] 等级 ${level.level} 的卡片元素未找到`);
        }
    });
    
    // 页面标题更新由主应用负责，这里不再重复更新
    // 避免与learning_page.js中的标题更新冲突
    
    // 注意：事件绑定由主应用负责，这里不重复绑定
    // 避免与learning_page.js中的事件绑定冲突
    console.log('[DocsModule] 主题内容渲染完成，事件绑定由主应用处理');
}

// 初始化知识点内容（已移除，因为HTML中已有结构）
function initKnowledgeContent() {
    console.log('[DocsModule] initKnowledgeContent 已废弃，HTML中已有知识点结构');
    return;
}

// 重置模块状态（用于重新初始化）
function resetModuleState() {
    ModuleState.currentTopicData = null;
    ModuleState.isInitialized = false;
    ModuleState.initPromise = null;
    console.log('[DocsModule] 模块状态已重置');
}

// 导出模块
export {
    loadTopicContent,
    renderTopicContent,
    initKnowledgeContent,
    resetModuleState,
    ModuleState
};

// 同时保持向后兼容
window.DocsModule = {
    loadTopicContent,
    renderTopicContent,
    initKnowledgeContent,
    resetModuleState,
    ModuleState
}; 