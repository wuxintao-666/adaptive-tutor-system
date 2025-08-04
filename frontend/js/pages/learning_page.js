

// ==================== 主应用逻辑 ====================
let allowedTags = [];
let bridge = null;

function initMainApp() {
    const startButton = document.getElementById('startSelector');
    const stopButton = document.getElementById('stopSelector');
    const statusBadge = document.getElementById('statusBadge');
    const iframe = document.getElementById('element-selector-iframe');
    
    if (!startButton || !stopButton || !iframe) {
        console.error('必要的DOM元素未找到');
        return;
    }
    
    // 初始化知识点内容
    if (window.DocsModule && window.DocsModule.initKnowledgeContent) {
        window.DocsModule.initKnowledgeContent();
    }
    
    // 初始化
    startButton.disabled = true;
    
    // 获取允许的标签
    window.DocsModule.ApiClient.get(`/users/user123/allowed-tags`).then(data => {
        allowedTags = data.allowed_tags || [];
        iframe.src = iframe.src;
        startButton.disabled = false;
    }).catch(error => {
        console.error('获取允许标签失败:', error);
        // 如果获取失败，使用默认标签
        allowedTags = ['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'img', 'table', 'tr', 'td', 'th', 'ul', 'ol', 'li', 'form', 'input', 'button', 'textarea', 'select', 'option'];
        startButton.disabled = false;
    });
    
    // iframe加载事件
    iframe.addEventListener('load', function() {
        try {
            const doc = iframe.contentDocument || iframe.contentWindow.document;
            const html = doc.documentElement.outerHTML;
            const codeElement = document.getElementById('selectedElementCode');
            if (codeElement) codeElement.textContent = html;
        } catch (e) {
            const codeElement = document.getElementById('selectedElementCode');
            if (codeElement) codeElement.textContent = '无法获取iframe页面源码';
        }
        
        console.log('预览框架已加载:', iframe.src);
        showStatus('info', '预览页面已加载，选择器已就绪');
        initBridge();
    });
    
    // 初始化桥接
    function initBridge() {
        if (bridge) bridge.destroy();
        bridge = SelectModules.createSelectorBridge({
            iframeWindow: iframe.contentWindow,
            onChosen: handleElementSelected,
            onError: handleError
        });
        console.log('选择器桥接已初始化');
    }
    
    // 启动选择器
    startButton.addEventListener('click', function() {
        if (!bridge) {
            showStatus('error', '桥接未初始化，请刷新页面重试');
            return;
        }
        startButton.style.display = 'none';
        stopButton.style.display = 'inline-block';
        showStatus('info', '请在预览区域中选择一个元素');
        bridge.start(allowedTags);
    });
    
    // 停止选择器
    stopButton.addEventListener('click', function() {
        stopSelector();
    });
    
    // 查看已保存元素
    const viewElementsBtn = document.getElementById('viewElements');
    if (viewElementsBtn) {
        viewElementsBtn.addEventListener('click', async function() {
            try {
                const response = await window.DocsModule.ApiClient.get('/elements');
                if (response.status === 'success') {
                    showElementsList(response.data);
                } else {
                    showStatus('error', '获取元素列表失败');
                }
            } catch (error) {
                console.error('获取元素列表失败:', error);
                showStatus('error', '获取元素列表失败: ' + error.message);
            }
        });
    }
    
    // Tab切换
    const tabKnowledge = document.getElementById('tab-knowledge');
    const tabCode = document.getElementById('tab-code');
    const knowledgeContent = document.getElementById('knowledge-content');
    const codeContent = document.getElementById('code-content');
    
    if (tabKnowledge && tabCode) {
        tabKnowledge.addEventListener('click', function() {
            if (knowledgeContent) knowledgeContent.style.display = '';
            if (codeContent) codeContent.style.display = 'none';
            this.classList.add('active');
            tabCode.classList.remove('active');
        });
        
        tabCode.addEventListener('click', function() {
            if (knowledgeContent) knowledgeContent.style.display = 'none';
            if (codeContent) codeContent.style.display = '';
            this.classList.add('active');
            tabKnowledge.classList.remove('active');
        });
    }
    
    // 初始化知识点展示区
    if (window.DocsModule) {
        window.DocsModule.initKnowledgeContent();
    }
    
    // 返回源代码按钮
    const showSourceBtn = document.getElementById('showSourceBtn');
    if (showSourceBtn) {
        showSourceBtn.addEventListener('click', function() {
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
        });
    }
}

// 元素被选中的处理函数
async function handleElementSelected(info) {
    const tabKnowledge = document.getElementById('tab-knowledge');
    const tabCode = document.getElementById('tab-code');
    const codePre = document.getElementById('selectedElementCode');
    const startButton = document.getElementById('startSelector');
    const stopButton = document.getElementById('stopSelector');
    
    // 显示状态信息
    showStatus('success', `已选择 ${info.tagName} 元素`);
    
    // 显示选中的元素代码
    if (codePre) {
        codePre.textContent = info.outerHTML || '';
    }
    
    // 自动加载知识点内容
    if (info.tagName && window.DocsModule) {
        await window.DocsModule.loadDocumentForTag(info.tagName.toLowerCase());
        // 加载完知识点后切换到知识点展示tab
        if (tabKnowledge) tabKnowledge.click();
    }
    
    // 切换按钮状态
    if (startButton) startButton.style.display = 'inline-block';
    if (stopButton) stopButton.style.display = 'none';
    
    // 保存元素信息到后端
    try {
        const elementData = {
            user_id: 'user123', // 可以从用户系统获取
            element_tag: info.tagName.toLowerCase(),
            element_info: info,
            timestamp: new Date().toISOString()
        };
        
        const response = await window.DocsModule.ApiClient.post('/elements', elementData);
        if (response.status === 'success') {
            showStatus('success', `元素已保存，ID: ${response.element_id}`);
        } else if (response.status === 'forbidden') {
            showStatus('warning', response.message);
        } else {
            showStatus('error', response.message || '保存失败');
        }
    } catch (error) {
        console.error('保存元素失败:', error);
        showStatus('error', '保存元素失败: ' + error.message);
    }
}

// 停止选择器
function stopSelector() {
    if (bridge) bridge.stop();
    const startButton = document.getElementById('startSelector');
    const stopButton = document.getElementById('stopSelector');
    if (startButton) startButton.style.display = 'inline-block';
    if (stopButton) stopButton.style.display = 'none';
}

// 错误处理
function handleError(error) {
    console.error('选择器错误:', error);
    showStatus('error', '发生错误: ' + error.message);
    stopSelector();
}

// 显示状态信息
function showStatus(type, message) {
    const statusBadge = document.getElementById('statusBadge');
    if (statusBadge) {
        statusBadge.textContent = message;
        statusBadge.className = `status-badge status-${type}`;
        statusBadge.style.display = 'inline-block';
    }
}

// 显示已保存的元素列表
function showElementsList(elements) {
    const chatMessages = document.getElementById('ai-chat-messages');
    if (!chatMessages) return;
    
    let elementsHtml = `
        <div class="ai-message">
            <div class="ai-content">
                <div class="markdown-content">
                    <h3>已保存的元素列表</h3>
                    <div style="max-height: 300px; overflow-y: auto;">
    `;
    
    if (elements.length === 0) {
        elementsHtml += '<p>暂无已保存的元素</p>';
    } else {
        elements.forEach(element => {
            elementsHtml += `
                <div style="border: 1px solid #e0e0e0; margin: 8px 0; padding: 12px; border-radius: 6px;">
                    <strong>ID:</strong> ${element.id}<br>
                    <strong>标签:</strong> ${element.element_tag}<br>
                    <strong>保存时间:</strong> ${new Date(element.timestamp).toLocaleString()}<br>
                    <strong>元素信息:</strong><br>
                    <pre style="background: #f5f5f5; padding: 8px; margin: 8px 0; font-size: 12px; max-height: 100px; overflow-y: auto;">${JSON.stringify(element.element_info, null, 2)}</pre>
                </div>
            `;
        });
    }
    
    elementsHtml += `
                    </div>
                </div>
            </div>
        </div>
    `;
    
    chatMessages.insertAdjacentHTML('beforeend', elementsHtml);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 导出主要函数
window.AIHTMLPlatform = {
    initMainApp,
    handleElementSelected,
    stopSelector,
    showStatus
};

// 自动初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMainApp);
} else {
    initMainApp();
} 