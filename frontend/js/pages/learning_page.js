
// ==================== 导入和初始化 ====================
//导入tracker，初始化，为了记录元素选择的行为ceq
// import tracker from '../modules/behavior_tracker.js';

console.log('learning_page.js 开始加载...');

// 全局错误处理，捕获runtime.lastError
if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.lastError) {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        if (chrome.runtime.lastError) {
            console.warn('Chrome runtime error:', chrome.runtime.lastError);
        }
    });
}

// 全局postMessage错误处理
window.addEventListener('message', (event) => {
    // 静默处理postMessage错误
}, { passive: true });

// ==================== 全局变量定义 ====================
let bridge = null;
let allowedElements = {
    cumulative: [],
    current: []
};
let currentTopicId = '1_1'; // 默认主题ID

// 模块实例
let chatModule = null;
let knowledgeModule = null;

// 统一的初始化状态管理
const AppState = {
    isInitialized: false,
    isDataLoaded: false,
    initPromise: null
};

// ==================== 聊天模块 ====================
// AI模块已注释，用于测试其他模块
/*
class ChatModule {
    constructor(options = {}) {
        this.messageInput = null;
        this.sendButton = null;
        this.chatMessages = null;
        this.isLoading = false;
        this.options = {
            participantId: 'user123',
            apiEndpoint: '/chat/ai/chat',
            ...options
        };
        
        this.init();
    }
    
    // 初始化聊天模块
    init() {
        this.messageInput = document.getElementById('user-message');
        this.sendButton = document.getElementById('send-message');
        this.chatMessages = document.getElementById('ai-chat-messages');
        
        if (this.messageInput && this.sendButton) {
            this.bindEvents();
        }
    }
    
    // 绑定事件监听器
    bindEvents() {
        // 发送按钮点击事件
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // 回车键发送事件
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }
    
    // 发送消息到AI
    async sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message) {
            alert('请输入消息内容');
            return;
        }
        
        if (this.isLoading) {
            return;
        }
        
        this.setLoadingState(true);
        
        try {
            // 添加用户消息到聊天界面
            this.addMessageToChat('user', message);
            
            // 发送消息到后端API
            const response = await fetch(`${window.buildBackendUrl(this.options.apiEndpoint)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    participant_id: this.options.participantId,
                    user_message: message,
                    conversation_history: []
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.code === 200 && result.data) {
                // 添加AI回复到聊天界面
                this.addMessageToChat('ai', result.data.ai_response);
            } else {
                throw new Error(result.message || 'AI回复失败');
            }
            
        } catch (error) {
            console.error('发送消息失败:', error);
            this.addMessageToChat('ai', '抱歉，我暂时无法回复，请稍后再试。');
        } finally {
            this.setLoadingState(false);
            // 清空输入框
            this.messageInput.value = '';
        }
    }
    
    // 设置加载状态
    setLoadingState(loading) {
        this.isLoading = loading;
        const originalText = this.sendButton.textContent;
        
        if (loading) {
            this.sendButton.disabled = true;
            this.sendButton.textContent = '发送中...';
        } else {
            this.sendButton.disabled = false;
            this.sendButton.textContent = originalText === '发送中...' ? '发送信息' : originalText;
        }
    }
    
    // 添加消息到聊天界面
    addMessageToChat(role, content) {
        if (!this.chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = role === 'user' ? 'user-message' : 'ai-message';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = role === 'user' ? 'user-content' : 'ai-content';
        
        if (role === 'ai') {
            const markdownDiv = document.createElement('div');
            markdownDiv.className = 'markdown-content';
            markdownDiv.innerHTML = content.replace(/\n/g, '<br>');
            contentDiv.appendChild(markdownDiv);
        } else {
            contentDiv.textContent = content;
        }
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        
        // 滚动到底部
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    // 静态方法，用于全局调用
    static sendMessage() {
        if (window.chatModule) {
            window.chatModule.sendMessage();
        }
    }
}
*/

// ==================== 知识点管理模块 ====================
class KnowledgeModule {
    constructor(options = {}) {
        this.levelCards = [];
        this.knowledgePanel = null;
        this.options = {
            ...options
        };
        
        this.init();
    }
    
    // 初始化知识点模块
    init() {
        console.log('[KnowledgeModule] 开始初始化知识点模块');
        
        // 获取知识点面板和卡片元素
        this.knowledgePanel = document.querySelector('.knowledge-panel');
        this.levelCards = document.querySelectorAll('.level-card');
        
        console.log('[KnowledgeModule] 找到知识点面板:', this.knowledgePanel);
        console.log('[KnowledgeModule] 找到卡片数量:', this.levelCards.length);
        
        if (!this.knowledgePanel) {
            console.error('[KnowledgeModule] 知识点面板元素未找到');
            return;
        }
        
        if (this.levelCards.length === 0) {
            console.warn('[KnowledgeModule] 未找到知识点卡片');
            return;
        }
        
        // 绑定事件监听器
        this.bindEvents();
        
        // 绑定键盘事件
        this.bindKeyboardEvents();
        
        console.log('[KnowledgeModule] 知识点模块初始化完成');
    }
    
    // 绑定事件监听器
    bindEvents() {
        console.log('[KnowledgeModule] 开始绑定事件，找到卡片数量:', this.levelCards.length);
        
        this.levelCards.forEach((card, index) => {
            console.log(`[KnowledgeModule] 为卡片 ${index + 1} (level ${card.dataset.level}) 绑定点击事件`);
            
            card.addEventListener('click', (event) => {
                console.log(`[KnowledgeModule] 卡片 ${index + 1} 被点击了！`);
                event.preventDefault();
                event.stopPropagation();
                this.handleCardClick(card);
            });
        });
        
        console.log('[KnowledgeModule] 事件绑定完成');
    }
    
    // 绑定键盘事件
    bindKeyboardEvents() {
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                const isExpanded = this.knowledgePanel.classList.contains('expanded');
                if (isExpanded) {
                    console.log('[KnowledgeModule] 检测到ESC键，退出展开模式');
                    // 收起所有卡片
                    this.levelCards.forEach(card => {
                        card.classList.remove('expanded');
                        card.classList.add('collapsed');
                    });
                    // 收起知识点面板
                    this.knowledgePanel.classList.remove('expanded');
                }
            }
        });
    }
    
    // 处理卡片点击事件
    handleCardClick(clickedCard) {
        console.log('[KnowledgeModule] 处理卡片点击事件');
        console.log('[KnowledgeModule] 被点击的卡片:', clickedCard);
        console.log('[KnowledgeModule] 卡片当前类名:', clickedCard.className);
        console.log('[KnowledgeModule] 卡片等级:', clickedCard.dataset.level);
        
        const isExpanded = this.knowledgePanel.classList.contains('expanded');
        console.log('[KnowledgeModule] 知识点面板是否已展开:', isExpanded);
        
        if (!isExpanded) {
            // 进入单卡片展开模式
            console.log('[KnowledgeModule] 进入单卡片展开模式');
            
            // 先收起所有卡片
            this.levelCards.forEach(card => {
                card.classList.remove('expanded');
                card.classList.add('collapsed');
                console.log(`[KnowledgeModule] 收起卡片 ${card.dataset.level}:`, card.className);
            });
            
            // 展开被点击的卡片
            clickedCard.classList.remove('collapsed');
            clickedCard.classList.add('expanded');
            console.log(`[KnowledgeModule] 展开卡片 ${clickedCard.dataset.level}:`, clickedCard.className);
            
            // 展开整个知识点面板
            this.knowledgePanel.classList.add('expanded');
            console.log('[KnowledgeModule] 知识点面板类名:', this.knowledgePanel.className);
            
            console.log('[KnowledgeModule] 单卡片展开模式已激活');
        } else {
            // 退出单卡片展开模式
            console.log('[KnowledgeModule] 退出单卡片展开模式');
            
            // 收起所有卡片
            this.levelCards.forEach(card => {
                card.classList.remove('expanded');
                card.classList.add('collapsed');
                console.log(`[KnowledgeModule] 收起卡片 ${card.dataset.level}:`, card.className);
            });
            
            // 收起知识点面板
            this.knowledgePanel.classList.remove('expanded');
            console.log('[KnowledgeModule] 知识点面板类名:', this.knowledgePanel.className);
            
            console.log('[KnowledgeModule] 已退出单卡片展开模式，返回选择界面');
        }
    }
    
    // 展开指定等级的卡片
    expandLevel(level) {
        const targetCard = document.querySelector(`.level-card[data-level="${level}"]`);
        if (targetCard) {
            this.handleCardClick(targetCard);
        }
    }
    
    // 收起所有卡片
    collapseAll() {
        this.levelCards.forEach(card => {
            card.classList.remove('expanded');
            card.classList.add('collapsed');
        });
        
        if (this.knowledgePanel) {
            this.knowledgePanel.classList.remove('expanded');
        }
    }
}

// ==================== 主应用初始化 ====================
async function initMainApp() {
    // 防止重复初始化的检查
    if (AppState.isInitialized) {
        console.log('主应用已经初始化过，跳过重复初始化');
        return;
    }
    
    // 如果正在初始化，等待完成
    if (AppState.initPromise) {
        console.log('主应用正在初始化中，等待完成');
        return AppState.initPromise;
    }
    
    // 创建初始化Promise
    AppState.initPromise = (async () => {
        try {
            // 标记为已初始化（立即设置，防止重复执行）
            AppState.isInitialized = true;
            
            console.log('开始初始化主应用...');
            
            const startButton = document.getElementById('startSelector');
            const stopButton = document.getElementById('stopSelector');
            const iframe = document.getElementById('element-selector-iframe');

            if (!startButton || !stopButton || !iframe) {
                console.error('必要的DOM元素未找到');
                return;
            }
            
            // 从URL获取topicId
            const urlParams = new URLSearchParams(window.location.search);
            const topicId = urlParams.get('topic');
            
            if (topicId) {
                currentTopicId = topicId;
                // 更新页面标题
                const headerTitle = document.querySelector('.header-title');
                if (headerTitle) {
                    headerTitle.textContent = `学习 - ${topicId}`;
                }
            }
            
            // 初始化按钮状态
            startButton.disabled = true;
            
            try {
                // 一次性加载所有数据
                console.log('开始加载所有数据...');
                console.log('[MainApp] 当前topicId:', currentTopicId);
                
                // 使用统一的API调用，避免重复
                const [progressData, elementsData, topicContent] = await Promise.all([
                    // 1. 获取用户进度
                    window.DocsModule.ApiClient.get(`/progress/participants/user123/progress`),
                    // 2. 获取可选元素数据（使用iframe-selector模块的函数）
                    window.SelectModules.loadAllowedElementsFromAPI(currentTopicId),
                    // 3. 加载主题内容（使用docs模块的函数）
                    window.DocsModule.loadTopicContent(currentTopicId)
                ]);
                
                console.log('[MainApp] API调用结果:');
                console.log('[MainApp] 进度数据:', progressData);
                console.log('[MainApp] 元素数据:', elementsData);
                console.log('[MainApp] 主题内容:', topicContent);
                
                // 设置可选元素数据
                allowedElements = elementsData;
                
                // 处理用户进度（可选功能）
                if (progressData && progressData.data && progressData.data.completed_topics) {
                    console.log('用户已完成主题:', progressData.data.completed_topics);
                }
                
                // 检查主题内容是否加载成功
                if (topicContent && topicContent.levels && topicContent.levels.length > 0) {
                    console.log('主题内容加载成功:', topicContent.title);
                } else {
                    console.warn('主题内容加载失败或为空，使用默认知识点内容');
                }
                
                // 数据加载完成后再初始化知识点模块
                console.log('[MainApp] 开始初始化知识点模块...');
                knowledgeModule = new KnowledgeModule();
                window.knowledgeModule = knowledgeModule;
                console.log('[MainApp] 知识点模块初始化完成:', knowledgeModule);
                
                console.log('所有数据加载完成:', { 
                    progress: progressData, 
                    elements: allowedElements,
                    topicContent: topicContent 
                });
                
                // 标记数据已加载
                AppState.isDataLoaded = true;
                
                // 启用按钮
                startButton.disabled = false;
                
            } catch (error) {
                console.error('数据加载失败:', error);
                // 如果获取失败，使用默认元素
                allowedElements = {
                    cumulative: ['div', 'span', 'p', 'h1', 'h2', 'h3'],
                    current: ['div', 'span', 'p']
                };
                startButton.disabled = false;
                
                // 初始化知识点模块（即使数据加载失败）
                console.log('[MainApp] 数据加载失败，但仍初始化知识点模块...');
                knowledgeModule = new KnowledgeModule();
                window.knowledgeModule = knowledgeModule;
                console.log('[MainApp] 知识点模块初始化完成（失败后）:', knowledgeModule);
            }

            // 初始化iframe事件监听（只绑定一次）
            initIframeEvents(iframe);
            
            // 初始化所有事件监听器
            initEventListeners();
            
            // 初始化iframe选择器
            if (typeof window.SelectModules.initIframeSelector === 'function') {
                window.SelectModules.initIframeSelector();
            }
            
            console.log('主应用初始化完成');
            
        } catch (error) {
            console.error('主应用初始化失败:', error);
            // 重置初始化状态，允许重试
            AppState.isInitialized = false;
            AppState.initPromise = null;
            throw error;
        }
    })();
    
    return AppState.initPromise;
}

// ==================== iframe事件初始化 ====================
function initIframeEvents(iframe) {
    // 只绑定一次
    if (iframe.hasAttribute('data-load-event-bound')) {
        return;
    }
    
    iframe.setAttribute('data-load-event-bound', 'true');
    
    iframe.addEventListener('load', function () {
        // 防止重复处理iframe加载事件
        if (window.iframeLoadProcessed) {
            console.log('iframe加载事件已处理过，跳过重复处理');
            return;
        }
        
        // 标记为已处理（立即设置，防止重复执行）
        window.iframeLoadProcessed = true;
        
        console.log('预览框架已加载:', iframe.src);
        showStatus('info', '预览页面已加载，选择器已就绪');
        
        // 初始化桥接
        setTimeout(() => {
            initBridge();
            // 行为追踪器已注释，跳过初始化
            // initBehaviorTracker();
        }, 100);
    });
    
    // 检查iframe是否已经加载完成
    if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {
        window.iframeLoadProcessed = true;
        setTimeout(() => {
            initBridge();
            // 行为追踪器已注释，跳过初始化
            // initBehaviorTracker();
        }, 100);
    }
}

// ==================== 事件监听器初始化 ====================
function initEventListeners() {
    const startButton = document.getElementById('startSelector');
    const stopButton = document.getElementById('stopSelector');
    const cumulativeToggle = document.getElementById('cumulativeToggle');
    const showSourceBtn = document.getElementById('showSourceBtn');
    const tabKnowledge = document.getElementById('tab-knowledge');
    const tabCode = document.getElementById('tab-code');
    const knowledgeContent = document.getElementById('knowledge-content');
    const codeContent = document.getElementById('code-content');

    // 启动选择器
    if (startButton) {
        startButton.addEventListener('click', handleStartSelector);
    }

    // 停止选择器
    if (stopButton) {
        stopButton.addEventListener('click', stopSelector);
    }
    
    // 初始化开关事件监听器
    if (cumulativeToggle) {
        cumulativeToggle.addEventListener('change', handleCumulativeToggle);
    }

    // Tab切换
    if (tabKnowledge && tabCode) {
        tabKnowledge.addEventListener('click', () => {
            if (knowledgeContent) knowledgeContent.style.display = '';
            if (codeContent) codeContent.style.display = 'none';
            tabKnowledge.classList.add('active');
            tabCode.classList.remove('active');
        });

        tabCode.addEventListener('click', () => {
            if (knowledgeContent) knowledgeContent.style.display = 'none';
            if (codeContent) codeContent.style.display = '';
            tabCode.classList.add('active');
            tabKnowledge.classList.remove('active');
        });
    }

    // 返回源代码按钮
    if (showSourceBtn) {
        showSourceBtn.addEventListener('click', handleShowSource);
    }
}

// ==================== 元素选择器相关函数 ====================
// 启动选择器处理函数
function handleStartSelector() {
    if (!bridge) {
        showStatus('error', '桥接未初始化，请刷新页面重试');
        return;
    }
    
    // 获取开关状态
    const cumulativeToggle = document.getElementById('cumulativeToggle');
    const useCumulative = cumulativeToggle ? cumulativeToggle.checked : false;
    
    // 根据开关状态选择元素列表
    const elementsToUse = useCumulative ? allowedElements.cumulative : allowedElements.current;
    
    const startButton = document.getElementById('startSelector');
    const stopButton = document.getElementById('stopSelector');
    
    if (startButton) startButton.style.display = 'none';
    if (stopButton) stopButton.style.display = 'inline-block';
    
    const statusMessage = useCumulative 
        ? `可选择当前及之前章节的元素 (${elementsToUse.length}个)`
        : `仅可选择当前章节的元素 (${elementsToUse.length}个)`;
    
    showStatus('info', statusMessage);
    bridge.start([], elementsToUse);
}

// 停止选择器
function stopSelector() {
    if (bridge) bridge.stop();
    const startButton = document.getElementById('startSelector');
    const stopButton = document.getElementById('stopSelector');
    if (startButton) startButton.style.display = 'inline-block';
    if (stopButton) stopButton.style.display = 'none';
}

// 初始化桥接
function initBridge() {
    const iframe = document.getElementById('element-selector-iframe');
    
    // 检查是否已经初始化过
    if (bridge && bridge.isInitialized) {
        console.log('选择器桥接已经初始化过，跳过重复初始化');
        return;
    }
    
    // 检查iframe是否准备就绪
    if (!iframe || !iframe.contentWindow) {
        console.warn('iframe未准备就绪，延迟初始化桥接');
        setTimeout(() => initBridge(), 100);
        return;
    }
    
    try {
        if (bridge) bridge.destroy();
        bridge = window.SelectModules.createSelectorBridge({
            iframeWindow: iframe.contentWindow,
            onChosen: handleElementSelected,
            onError: handleError
        });
        
        // 标记为已初始化
        if (bridge) {
            bridge.isInitialized = true;
        }
        
        console.log('选择器桥接已初始化');
    } catch (error) {
        console.error('初始化桥接失败:', error);
        // 如果初始化失败，延迟重试
        setTimeout(() => initBridge(), 200);
    }
}

// 元素被选中的处理函数
async function handleElementSelected(info) {
    const tabKnowledge = document.getElementById('tab-knowledge');
    const codePre = document.getElementById('selectedElementCode');
    const startButton = document.getElementById('startSelector');
    const stopButton = document.getElementById('stopSelector');

    // 显示状态信息
    showStatus('success', `已选择 ${info.tagName} 元素`);

    // 显示选中的元素代码
    if (codePre) {
        codePre.textContent = info.outerHTML || '';
    }

    // 注意：不再自动加载知识点内容，因为主界面使用卡片式布局
    // 用户可以通过点击知识点卡片来查看相关内容

    // 切换按钮状态
    if (startButton) startButton.style.display = 'inline-block';
    if (stopButton) stopButton.style.display = 'none';
}

// ==================== 事件处理函数 ====================
// 累积开关处理函数
function handleCumulativeToggle() {
    const isChecked = this.checked;
    const currentCount = allowedElements.current.length;
    const cumulativeCount = allowedElements.cumulative.length;
    
    const statusMessage = isChecked 
        ? `已开启：可选择当前及之前章节的元素 (${cumulativeCount}个)`
        : `已关闭：仅可选择当前章节的元素 (${currentCount}个)`;
    
    showStatus('info', statusMessage);
}

// 显示源代码处理函数
function handleShowSource() {
    const iframe = document.getElementById('element-selector-iframe');
    const tabCode = document.getElementById('tab-code');
    
    try {
        const doc = iframe.contentDocument || iframe.contentWindow.document;
        const html = doc.documentElement.outerHTML;
        const codeElement = document.getElementById('selectedElementCode');
        if (codeElement) codeElement.textContent = html;
        if (tabCode) tabCode.click();
    } catch (e) {
        const codeElement = document.getElementById('selectedElementCode');
        if (codeElement) codeElement.textContent = '无法获取iframe页面源码';
    }
}

// 错误处理
function handleError(error) {
    console.error('选择器错误:', error);
    showStatus('error', '发生错误: ' + error.message);
    stopSelector();
}

// ==================== 工具函数 ====================
// 显示状态信息
function showStatus(type, message) {
    const statusBadge = document.getElementById('statusBadge');
    if (statusBadge) {
        statusBadge.textContent = message;
        statusBadge.className = `status-badge status-${type}`;
        statusBadge.style.display = 'inline-block';
        
        setTimeout(() => {
            statusBadge.style.display = 'none';
        }, 3000);
    }
}

// ==================== 导出和自动初始化 ====================
// 导出主要函数
window.AIHTMLPlatform = {
    initMainApp,
    handleElementSelected,
    stopSelector,
    showStatus
}; 