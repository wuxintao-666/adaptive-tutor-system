// ==================== 文档模块 ====================
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
    advancedInterval: null
};

// API客户端
const ApiClient = {
    async get(endpoint) {
        try {
            const response = await fetch(`http://localhost:8000/api/v1${endpoint}`);
            if (!response.ok) throw new Error(`API错误: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error(`请求失败: ${endpoint}`, error);
            throw error;
        }
    },
    
    async post(endpoint, data) {
        try {
            const response = await fetch(`http://localhost:8000/api/v1${endpoint}`, {
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
        // 使用后端API获取标签内容
        const response = await ApiClient.post('/docs/tag-content', {
            tag_name: tagName
        });
        
        if (response.status !== 'success') {
            throw new Error(response.message || '未找到内容');
        }
        
        docsModuleState.currentTag = { id: tagName, title: `${tagName} 组件` };
        docsModuleState.currentLevelIndex = 0;
        docsModuleState.contents = response.data.contents;
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

// 渲染文档内容
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
    try {
        const response = await ApiClient.post('/docs/record-time', {
            action: 'record_time',
            base_time: docsModuleState.basicTimer,
            advanced_time: docsModuleState.advancedTimer
        });
        
        docsModuleState.basicTimer = 0;
        docsModuleState.advancedTimer = 0;
        updateTimeDisplay();
        
        if (response.status !== 'success') {
            showError(response.message || '时间记录失败');
        } else {
            console.log('学习时间已成功记录');
        }
    } catch (e) {
        // 如果后端不可用，只重置本地计时器
        console.warn('后端不可用，仅重置本地计时器:', e.message);
        docsModuleState.basicTimer = 0;
        docsModuleState.advancedTimer = 0;
        updateTimeDisplay();
    }
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
        <div class="input-row">
            <input type="text" id="tag-id" placeholder="知识点分组ID">
            <button id="tag-btn">获取分组标签</button>
            <input type="text" id="tag-input" placeholder="组件名称">
            <button id="test-btn">查找组件</button>
        </div>
        <div id="tag-select-container" style="margin: 12px 0;"></div>
        <div class="card-container">
            <div id="card-content" class="card">
                <h2 id="tag-title" class="card-title">请选择组件</h2>
                <div id="tag-content"></div>
            </div>
        </div>
        <div class="timer-display">
            <div class="timer-item"><span class="timer-label">基础内容：</span><span id="basic-time">00:00</span></div>
            <div class="timer-item"><span class="timer-label">进阶内容：</span><span id="advanced-time">00:00</span></div>
        </div>
    `;
    
    // 绑定事件
    document.getElementById('tag-btn').onclick = async function() {
        const tagId = document.getElementById('tag-id').value.trim();
        if (!tagId) {
            showError('请输入知识点分组ID');
            return;
        }
        try {
            // 使用后端API获取目录
            const response = await ApiClient.get('/docs/catalog');
            if (response.status !== 'active') {
                throw new Error('获取目录失败');
            }
            
            const catalog = response.data.catalog;
            const tags = catalog[tagId];
            if (!tags || tags.length === 0) {
                throw new Error('未找到相关标签');
            }
            renderTagSelect(tags);
        } catch (e) {
            showError(e.message);
        }
    };
    
    document.getElementById('test-btn').onclick = function() {
        const tagName = document.getElementById('tag-input').value.trim();
        if (!tagName) {
            showError('请输入组件名称');
            return;
        }
        loadDocumentForTag(tagName);
    };
}

// 渲染标签选择
function renderTagSelect(tags) {
    const container = document.getElementById('tag-select-container');
    if (!container) return;
    
    container.innerHTML = `
        <div style="margin-bottom: 12px;">
            <label for="tag-select" style="font-weight:bold;">请选择标签：</label>
            <select id="tag-select"><option value="">-- 请选择 --</option>${tags.map(tag => `<option value="${tag}">${tag}</option>`).join('')}</select>
        </div>
    `;
    
    const tagSelect = document.getElementById('tag-select');
    if (tagSelect) {
        tagSelect.onchange = function(e) {
            if (e.target.value) loadDocumentForTag(e.target.value);
        };
    }
}

// 导出模块
window.DocsModule = {
    loadDocumentForTag,
    renderDocContent,
    startTimer,
    stopTimer,
    updateTimeDisplay,
    sendTimeToBackend,
    showError,
    initKnowledgeContent,
    renderTagSelect,
    ApiClient,
    DIFFICULTY,
    docsModuleState
}; 