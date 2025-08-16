// ==================== 文档模块 ====================
import { AppConfig, buildBackendUrl } from './config.js';

// 统一的模块状态管理
const ModuleState = {
    currentTopicData: null,  // 存储当前主题的完整数据
    isInitialized: false,    // 防重复初始化标志
    initPromise: null        // 初始化Promise，防止重复调用
};

// API客户端
const ApiClient = {
    async get(endpoint) {
        try {
            // 使用配置中的API基础URL
            const response = await fetch(buildBackendUrl(endpoint));
            if (!response.ok) throw new Error(`API错误: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error(`请求失败: ${endpoint}`, error);
            throw error;
        }
    },
    
    async post(endpoint, data) {
        try {
            // 使用配置中的API基础URL
            const response = await fetch(buildBackendUrl(endpoint), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`API错误: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error(`请求失败: ${endpoint}`, error);
            throw error;
        }
    }
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
            // 使用后端API获取主题内容
            const response = await ApiClient.get(`/learning-content/${topicId}`);
            
            if (response.code !== 200) {
                throw new Error(response.message || '未找到主题内容');
            }
            
            const topicData = response.data;
            ModuleState.currentTopicData = topicData;
            
            // 直接渲染四个等级的内容
            renderTopicContent();
            
            // 返回加载的数据
            return topicData;
            
        } catch (e) {
            console.warn('无法从后端获取主题内容，使用默认内容:', e.message);
            
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
    
    // 更新页面标题
    const headerTitle = document.querySelector('.header-title');
    if (headerTitle && topicData.title) {
        headerTitle.textContent = topicData.title;
        console.log('[DocsModule] 页面标题已更新:', topicData.title);
    }
    
    // 注意：事件绑定由主应用负责，这里不重复绑定
    // 避免与learning_page.js中的事件绑定冲突
    console.log('[DocsModule] 主题内容渲染完成，事件绑定由主应用处理');
}

// 初始化知识点内容
function initKnowledgeContent() {
    // 防止重复初始化
    if (ModuleState.isInitialized) {
        console.log('[DocsModule] 知识点内容已经初始化过，跳过重复初始化');
        return;
    }
    
    const knowledgeContent = document.getElementById('knowledge-content');
    if (!knowledgeContent) {
        console.warn('[DocsModule] knowledge-content 元素不存在');
        return;
    }
    
    // 创建默认知识点内容
    knowledgeContent.innerHTML = `
        <div class="levels-flow">
            <div class="level-card collapsed" data-level="1">
                <div class="level-header">
                    <h3>Level 1 · 基础</h3>
                </div>
                <div class="level-content">
                    <p class="content-text">适合零基础入门，掌握核心概念与基本语法。这个等级主要关注基础知识的建立，为后续学习打下坚实基础。</p>
                </div>
                <div class="click-hint">点击进入学习</div>
            </div>
            <div class="arrow" aria-hidden="true">➜</div>
            <div class="level-card collapsed" data-level="2">
                <div class="level-header">
                    <h3>Level 2 · 进阶</h3>
                </div>
                <div class="level-content">
                    <p class="content-text">理解常见场景与组合用法，提升实践能力。在这个等级中，学习者将接触到更复杂的应用场景。</p>
                </div>
                <div class="click-hint">点击进入学习</div>
            </div>
            <div class="arrow" aria-hidden="true">➜</div>
            <div class="level-card collapsed" data-level="3">
                <div class="level-header">
                    <h3>Level 3 · 高级</h3>
                </div>
                <div class="level-content">
                    <p class="content-text">深入机制与性能优化，形成系统化认知。高级等级专注于深层次理解和性能优化技巧。</p>
                </div>
                <div class="click-hint">点击进入学习</div>
            </div>
            <div class="arrow" aria-hidden="true">➜</div>
            <div class="level-card collapsed" data-level="4">
                <div class="level-header">
                    <h3>Level 4 · 挑战</h3>
                </div>
                <div class="level-content">
                    <p class="content-text">综合实战与拓展题，检验与突破现有水平。挑战等级包含复杂的综合应用和高级技巧。</p>
                </div>
                <div class="click-hint">点击进入学习</div>
            </div>
        </div>
    `;
    
    // 标记为已初始化
    ModuleState.isInitialized = true;
    console.log('[DocsModule] 默认知识点内容初始化完成');
}

// 重置模块状态（用于重新初始化）
function resetModuleState() {
    ModuleState.currentTopicData = null;
    ModuleState.isInitialized = false;
    ModuleState.initPromise = null;
    console.log('[DocsModule] 模块状态已重置');
}

// 导出模块
window.DocsModule = {
    loadTopicContent,
    renderTopicContent,
    initKnowledgeContent,
    resetModuleState,
    ApiClient,
    ModuleState
}; 