// ==================== 文档模块 ====================
import { AppConfig } from './config.js';

const DIFFICULTY = [
    { key: 'basic', label: '基础介绍', category: 'basic' },
    { key: 'intermediate', label: '语法和基本用法', category: 'basic' },
    { key: 'advanced', label: '实际应用', category: 'advanced' },
    { key: 'expert', label: '深入原理', category: 'advanced' }
];

let docsModuleState = {
    currentTag: null,
    currentLevelIndex: 0,
    contents: {},
    basicTimer: 0,
    advancedTimer: 0,
    basicInterval: null,
    advancedInterval: null,
    currentTopicData: null  // 存储当前主题的完整数据
};

// API客户端
const ApiClient = {
    async get(endpoint) {
        try {
            // 使用配置中的API基础URL
            const response = await fetch(`${window.FrontendConfig.getApiBaseUrl()}${endpoint}`);
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
            const response = await fetch(`${window.FrontendConfig.getApiBaseUrl()}${endpoint}`, {
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

// 加载文档内容
async function loadDocumentForTag(tagName) {
    try {
        // 使用后端API获取学习内容
        const response = await ApiClient.get(`/learning-content/${tagName}`);
        
        if (response.status !== 'success') {
            throw new Error(response.message || '未找到内容');
        }
        
        docsModuleState.currentTag = { id: tagName, title: `${tagName} 组件` };
        docsModuleState.currentLevelIndex = 0;
        
        // 将学习内容转换为原来的格式
        const contentData = response.data;
        docsModuleState.contents = {
            basic: contentData.content || `${tagName} 标签是HTML中常用的元素。`,
            intermediate: contentData.content || `${tagName} 标签的基本语法：<${tagName}>内容</${tagName}>`,
            advanced: contentData.content || `${tagName} 标签可以包含其他HTML元素和文本内容。`,
            expert: contentData.content || `${tagName} 标签支持各种属性，如class、id、style等。`
        };
        
        renderDocContent();
        startTimer();
    } catch (e) {
        // 如果后端API失败，使用默认内容
        console.warn('无法从后端获取内容，使用默认内容:', e.message);
        
        docsModuleState.currentTag = { id: tagName, title: `${tagName} 组件` };
        docsModuleState.currentLevelIndex = 0;
        
        // 生成默认的HTML标签说明
        const defaultContents = {
            basic: `${tagName} 标签是HTML中常用的元素。`,
            intermediate: `${tagName} 标签的基本语法：<${tagName}>内容</${tagName}>`,
            advanced: `${tagName} 标签可以包含其他HTML元素和文本内容。`,
            expert: `${tagName} 标签支持各种属性，如class、id、style等。`
        };
        
        docsModuleState.contents = defaultContents;
        renderDocContent();
        startTimer();
    }
}

// 加载主题内容（新函数）
async function loadTopicContent(topicId) {
    try {
        // 使用后端API获取主题内容
        const response = await ApiClient.get(`/learning-content/${topicId}`);
        
        if (response.code !== 200) {
            throw new Error(response.message || '未找到主题内容');
        }
        
        const topicData = response.data;
        docsModuleState.currentTopicData = topicData;
        docsModuleState.currentTag = { id: topicId, title: topicData.title || `主题 ${topicId}` };
        
        // 直接渲染四个等级的内容
        renderTopicContent();
        startTimer();
        
    } catch (e) {
        console.warn('无法从后端获取主题内容，使用默认内容:', e.message);
        
        // 使用默认内容
        docsModuleState.currentTag = { id: topicId, title: `主题 ${topicId}` };
        docsModuleState.currentTopicData = {
            title: `主题 ${topicId}`,
            levels: [
                { level: 1, description: "基础概念：适合零基础入门，掌握核心概念与基本语法。" },
                { level: 2, description: "详细解析：理解常见场景与组合用法，提升实践能力。" },
                { level: 3, description: "实际应用：深入机制与性能优化，形成系统化认知。" },
                { level: 4, description: "原理分析：综合实战与拓展题，检验与突破现有水平。" }
            ]
        };
        
        renderTopicContent();
        startTimer();
    }
}

// 渲染主题内容（新函数）
function renderTopicContent() {
    const knowledgeContent = document.getElementById('knowledge-content');
    if (!knowledgeContent || !docsModuleState.currentTopicData) return;
    
    const topicData = docsModuleState.currentTopicData;
    const levels = topicData.levels || [];
    
    // 构建四个等级的内容
    const levelCards = levels.map((level, index) => {
        const levelLabels = ['基础', '进阶', '高级', '挑战'];
        const levelLabel = levelLabels[index] || `Level ${level.level}`;
        
        return `
            <div class="level-card">
                <h3>Level ${level.level} · ${levelLabel}</h3>
                <p class="content-text">${level.description || '暂无内容'}</p>
            </div>
        `;
    }).join('');
    
    // 添加箭头分隔符
    const arrows = Array(levels.length - 1).fill('<div class="arrow" aria-hidden="true">➜</div>').join('');
    
    knowledgeContent.innerHTML = `
        <div class="levels-flow">
            ${levelCards}
            ${arrows}
        </div>
    `;
    
    // 更新页面标题
    const headerTitle = document.querySelector('.header-title');
    if (headerTitle && topicData.title) {
        headerTitle.textContent = topicData.title;
    }
    
    startTimer();
    updateTimeDisplay();
}

// 渲染文档内容（保持原有功能，用于兼容性）
function renderDocContent() {
    const tagTitle = document.getElementById('tag-title');
    const tagContent = document.getElementById('tag-content');
    if (!docsModuleState.currentTag) {
        if (tagTitle) tagTitle.textContent = '请选择组件';
        if (tagContent) tagContent.innerHTML = '';
        return;
    }
    
    const level = DIFFICULTY[docsModuleState.currentLevelIndex];
    let content = docsModuleState.contents[level.key] || `暂无${level.label}内容。`;
    
    if (tagTitle) tagTitle.textContent = `${docsModuleState.currentTag.title}`;
    if (tagContent) {
        tagContent.innerHTML = `
            <div class="level-block">
                <h3>${level.label}</h3>
                <pre class="content-text">${content}</pre>
                <div class="level-btns">
                    <button id="prev-btn" ${docsModuleState.currentLevelIndex===0?'disabled':''}>上一级</button>
                    <button id="next-btn" ${docsModuleState.currentLevelIndex===DIFFICULTY.length-1?'disabled':''}>下一级</button>
                    ${docsModuleState.currentLevelIndex===3 ? '<button id="complete-btn">阅读完毕</button>' : ''}
                </div>
            </div>
        `;
        
        // 绑定按钮事件
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const completeBtn = document.getElementById('complete-btn');
        
        if (prevBtn) {
            prevBtn.onclick = function() {
                if (docsModuleState.currentLevelIndex > 0) {
                    docsModuleState.currentLevelIndex--;
                    renderDocContent();
                }
            };
        }
        
        if (nextBtn) {
            nextBtn.onclick = function() {
                if (docsModuleState.currentLevelIndex < DIFFICULTY.length-1) {
                    docsModuleState.currentLevelIndex++;
                    renderDocContent();
                }
            };
        }
        
        if (completeBtn) {
            completeBtn.onclick = async function(e) {
                e.preventDefault();
                stopTimer();
                await sendTimeToBackend();
                this.textContent = '您已完成此组件学习';
                this.disabled = true;
            };
        }
    }
    
    startTimer();
    updateTimeDisplay();
}

// 计时器相关函数
function startTimer() {
    stopTimer();
    const level = DIFFICULTY[docsModuleState.currentLevelIndex];
    if (level.category === 'basic') {
        docsModuleState.basicInterval = setInterval(() => {
            docsModuleState.basicTimer++;
            updateTimeDisplay();
        }, 1000);
    } else {
        docsModuleState.advancedInterval = setInterval(() => {
            docsModuleState.advancedTimer++;
            updateTimeDisplay();
        }, 1000);
    }
}

function stopTimer() {
    clearInterval(docsModuleState.basicInterval);
    clearInterval(docsModuleState.advancedInterval);
}

function updateTimeDisplay() {
    const basicTime = document.getElementById('basic-time');
    const advancedTime = document.getElementById('advanced-time');
    if (basicTime) basicTime.textContent = formatTime(docsModuleState.basicTimer);
    if (advancedTime) advancedTime.textContent = formatTime(docsModuleState.advancedTimer);
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

async function sendTimeToBackend() {
    // 只在前端显示，不向后端传输数据
    console.log('学习时间记录（仅前端显示）:', {
        basic_time: docsModuleState.basicTimer,
        advanced_time: docsModuleState.advancedTimer
    });
    
    // 重置本地计时器
    docsModuleState.basicTimer = 0;
    docsModuleState.advancedTimer = 0;
    updateTimeDisplay();
    
    console.log('学习时间已重置');
}

// 错误显示
function showError(msg) {
    let statusDiv = document.getElementById('statusContainer');
    if (!statusDiv) {
        statusDiv = document.createElement('div');
        statusDiv.id = 'statusContainer';
        statusDiv.className = 'status info';
        const tagContent = document.getElementById('tag-content');
        if (tagContent) tagContent.prepend(statusDiv);
    }
    statusDiv.textContent = msg;
    statusDiv.style.display = 'block';
    setTimeout(() => { statusDiv.style.display = 'none'; }, 3000);
}

// 初始化知识点内容
function initKnowledgeContent() {
    const knowledgeContent = document.getElementById('knowledge-content');
    if (!knowledgeContent) return;
    
    knowledgeContent.innerHTML = `
        <div class="levels-flow">
            <div class="level-card">
                <h3>Level 1 · 基础</h3>
                <p class="content-text">适合零基础入门，掌握核心概念与基本语法。</p>
            </div>
            <div class="arrow" aria-hidden="true">➜</div>
            <div class="level-card">
                <h3>Level 2 · 进阶</h3>
                <p class="content-text">理解常见场景与组合用法，提升实践能力。</p>
            </div>
            <div class="arrow" aria-hidden="true">➜</div>
            <div class="level-card">
                <h3>Level 3 · 高级</h3>
                <p class="content-text">深入机制与性能优化，形成系统化认知。</p>
            </div>
            <div class="arrow" aria-hidden="true">➜</div>
            <div class="level-card">
                <h3>Level 4 · 挑战</h3>
                <p class="content-text">综合实战与拓展题，检验与突破现有水平。</p>
            </div>
        </div>
    `;
}

// 导出模块
window.DocsModule = {
    loadDocumentForTag,
    loadTopicContent,  // 新增函数
    renderDocContent,
    renderTopicContent,  // 新增函数
    startTimer,
    stopTimer,
    updateTimeDisplay,
    sendTimeToBackend,
    showError,
    initKnowledgeContent,
    ApiClient,
    DIFFICULTY,
    docsModuleState
}; 