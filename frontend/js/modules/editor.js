/** 
 * Monaco编辑器初始化和管理
 */
import { buildBackendUrl } from './config.js';

document.addEventListener('DOMContentLoaded', function() {
    // 检查页面是否包含Monaco编辑器容器，如果不存在则不执行任何操作
    if (!document.getElementById('monaco-editor')) {
        return;
    }

    // 从本地存储中获取现有会话ID（如果有）
    const savedSessionId = localStorage.getItem('editorSessionId');
    console.log(savedSessionId ? `从本地存储中恢复会话ID: ${savedSessionId}` : '未找到本地存储的会话ID');
    
    // 默认代码内容
    const defaultHTML = `<!DOCTYPE html>\n<html>\n<head>\n    <title>示例页面</title>\n</head>\n<body>\n    <h1>欢迎使用代码编辑器</h1>\n    <p>在这里编写你的HTML代码</p>\n    <button id="demo-button">点击我</button>\n    \n    <script src="script.js"></script>\n</body>\n</html>`;
    
    const defaultCSS = `body {\n    font-family: Arial, sans-serif;\n    max-width: 800px;\n    margin: 0 auto;\n    padding: 20px;\n}\n\nh1 {\n    color: #10a37f;\n}\n\nbutton {\n    background-color: #10a37f;\n    color: white;\n    border: none;\n    padding: 10px 20px;\n    border-radius: 4px;\n    cursor: pointer;\n}\n\nbutton:hover {\n    background-color: #0e906f;\n}`;
    
    const defaultJS = `document.getElementById('demo-button').addEventListener('click', function() {\n    alert('按钮被点击了！');\n});`;
    
    // 编辑器配置和状态
window.editorState = {
    html: defaultHTML,
    css: defaultCSS,
    js: defaultJS,
    // 使用动态构建的后端URL
    get backendUrl() {
        return buildBackendUrl('/api/ide');
    }
};

// 添加一个函数来设置初始代码
window.setInitialCode = function(startCode) {
    if (startCode && typeof startCode === 'object') {
        window.editorState.htmlValue = startCode.html !== undefined ? startCode.html : defaultHTML;
        window.editorState.cssValue = startCode.css !== undefined ? startCode.css : defaultCSS;
        window.editorState.jsValue = startCode.js !== undefined ? startCode.js : defaultJS;
    }
};

    // 编辑器实例
    let editor = null;
    let editorCSS = null;
    let editorJS = null;

    // 初始化Monaco编辑器
    require(['vs/editor/editor.main'], function() {
        // 引入编程语言支持
        const jsDefaults = monaco.languages.typescript.javascriptDefaults;
        
        // 配置JS语言特性
        jsDefaults.setCompilerOptions({
            target: monaco.languages.typescript.ScriptTarget.ES2016,
            allowNonTsExtensions: true,
            moduleResolution: monaco.languages.typescript.ModuleResolutionKind.NodeJs,
            module: monaco.languages.typescript.ModuleKind.CommonJS,
            noEmit: true,
            typeRoots: ["node_modules/@types"],
            jsx: monaco.languages.typescript.JsxEmit.React
        });

        // 启用JS语言的语法和语义验证
        jsDefaults.setDiagnosticsOptions({
            noSemanticValidation: false,
            noSyntaxValidation: false,
            diagnosticCodesToIgnore: [1005, 1068, 1109]
        });

        // 添加DOM类型定义
        jsDefaults.addExtraLib(
        `declare var document: {\n            createElement(tagName: string): HTMLElement;\n            querySelector(selectors: string): HTMLElement;\n            querySelectorAll(selectors: string): HTMLElement[];\n            getElementById(elementId: string): HTMLElement;\n            body: HTMLElement;\n        };\n\n        interface HTMLElement {\n            appendChild(node: HTMLElement): HTMLElement;\n            innerHTML: string;\n            style: any;\n            onclick: Function;\n            value: string;\n            addEventListener(event: string, listener: Function): void;\n        };\n\n        declare var console: {\n            log(...args: any[]): void;\n            error(...args: any[]): void;\n            warn(...args: any[]): void;\n        };\n\n        declare var window: {\n            alert(message: string): void;\n            addEventListener(event: string, listener: Function): void;\n        };
        `, 'ts:dom.d.ts');
        
        // 配置编辑器主题
        monaco.editor.defineTheme('myCustomTheme', {
            base: 'vs',
            inherit: true,
            rules: [
                { token: 'comment', foreground: '008800', fontStyle: 'italic' },
                { token: 'keyword', foreground: '0000ff', fontStyle: 'bold' },
                { token: 'string', foreground: 'aa6600' },
                { token: 'number', foreground: '116644' },
                { token: 'identifier', foreground: '000000' },
                { token: 'type', foreground: '267f99' },
                { token: 'delimiter', foreground: '000000' },
                { token: 'delimiter.parenthesis', foreground: '000000' },
                { token: 'delimiter.curly', foreground: '000000' },
                { token: 'operator', foreground: '000000' },
                { token: 'function', foreground: '795e26' }
            ],
            colors: {
                'editor.background': '#f9f9f9',
                'editor.lineHighlightBackground': '#f0f0f0',
                'editorLineNumber.foreground': '#999999',
                'editor.selectionBackground': '#c0ddff',
                'editor.inactiveSelectionBackground': '#e5ebf1',
                'editorError.foreground': '#ff0000',
                'editorWarning.foreground': '#ffa500',
                'editorInfo.foreground': '#008800'
            }
        });

        // 创建各个编辑器实例
        // HTML 编辑器
        editor = monaco.editor.create(document.getElementById('monaco-editor'), {
            value: editorState.htmlValue || defaultHTML,
            language: 'html',
            theme: 'myCustomTheme',
            automaticLayout: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            renderLineHighlight: 'all',
            renderWhitespace: 'none',
            lineNumbers: 'on',
            tabSize: 2,
            formatOnPaste: true,
            formatOnType: true,
            autoIndent: 'full',
            semanticHighlighting: true,
            suggestOnTriggerCharacters: true,
            acceptSuggestionOnCommitCharacter: true,
            wordBasedSuggestions: true,
            parameterHints: { enabled: true },
            folding: true,
            renderValidationDecorations: 'on',
            fontSize: 14,
            fontFamily: "'Fira Code', Consolas, 'Courier New', monospace",
            fontLigatures: true,
            cursorBlinking: 'smooth'
        });
        
        // CSS 编辑器
        editorCSS = monaco.editor.create(document.getElementById('monaco-editor-css'), {
            value: editorState.cssValue || defaultCSS,
            language: 'css',
            theme: 'myCustomTheme',
            automaticLayout: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            renderLineHighlight: 'all',
            renderWhitespace: 'none',
            lineNumbers: 'on',
            tabSize: 2,
            formatOnPaste: true,
            formatOnType: true,
            autoIndent: 'full',
            semanticHighlighting: true,
            suggestOnTriggerCharacters: true,
            acceptSuggestionOnCommitCharacter: true,
            wordBasedSuggestions: true,
            parameterHints: { enabled: true },
            folding: true,
            renderValidationDecorations: 'on',
            fontSize: 14,
            fontFamily: "'Fira Code', Consolas, 'Courier New', monospace",
            fontLigatures: true,
            cursorBlinking: 'smooth'
        });
        
        // JavaScript 编辑器
        editorJS = monaco.editor.create(document.getElementById('monaco-editor-js'), {
            value: editorState.jsValue || defaultJS,
            language: 'javascript',
            theme: 'myCustomTheme',
            automaticLayout: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            renderLineHighlight: 'all',
            renderWhitespace: 'none',
            lineNumbers: 'on',
            tabSize: 2,
            formatOnPaste: true,
            formatOnType: true,
            autoIndent: 'full',
            semanticHighlighting: true,
            suggestOnTriggerCharacters: true,
            acceptSuggestionOnCommitCharacter: true,
            wordBasedSuggestions: true,
            parameterHints: { enabled: true },
            folding: true,
            renderValidationDecorations: 'on',
            fontSize: 14,
            fontFamily: "'Fira Code', Consolas, 'Courier New', monospace",
            fontLigatures: true,
            cursorBlinking: 'smooth'
        });

        // 监听编辑器内容变化
        editor.onDidChangeModelContent(function(e) {
            // 保存当前编辑器内容到状态
            editorState.html = editor.getValue();
            
            // 添加防抖，避免频繁请求
            clearTimeout(window.staticCheckTimer);
            window.staticCheckTimer = setTimeout(function() {
                performStaticCheck();
            }, 1000); // 1秒后执行静态检查
        });
        
        editorCSS.onDidChangeModelContent(function(e) {
            // 保存当前编辑器内容到状态
            editorState.css = editorCSS.getValue();
            
            // 添加防抖，避免频繁请求
            clearTimeout(window.staticCheckTimer);
            window.staticCheckTimer = setTimeout(function() {
                performStaticCheck();
            }, 1000); // 1秒后执行静态检查
        });
        
        editorJS.onDidChangeModelContent(function(e) {
            // 保存当前编辑器内容到状态
            editorState.js = editorJS.getValue();
            
            // 添加防抖，避免频繁请求
            clearTimeout(window.staticCheckTimer);
            window.staticCheckTimer = setTimeout(function() {
                performStaticCheck();
            }, 1000); // 1秒后执行静态检查
        });

        // 将编辑器实例存储在editorState中，供其他模块使用
        editorState.htmlEditor = editor;
        editorState.cssEditor = editorCSS;
        editorState.jsEditor = editorJS;

        // 初始化编辑器标签切换
        initEditorTabs();

        // 初始化按钮事件
        initButtons();
    });

    // 初始化编辑器标签切换
    function initEditorTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        
        // 确保默认标签是激活的
        const defaultTab = 'html';
        document.getElementById('editor-' + defaultTab).style.display = 'block';
        
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                const tab = this.getAttribute('data-tab');
                console.log('切换到标签：', tab);
                
                // 更新标签按钮状态
                tabButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                
                // 首先隐藏所有内容区域
                document.querySelectorAll('.editor-container').forEach(container => {
                    container.style.display = 'none';
                });
                
                // 预览标签页的处理
                if (tab === 'preview') {
                    // 显示预览区域
                    document.getElementById('editor-preview').style.display = 'flex';
                    // 刷新预览
                    updateLocalPreview();
                    return;
                }
                
                // 显示当前选中的编辑器容器
                const editorContainer = document.getElementById('editor-' + tab);
                if (editorContainer) {
                    editorContainer.style.display = 'block';
                    console.log('显示编辑器容器：', 'editor-' + tab);
                } else {
                    console.error('找不到编辑器容器：', 'editor-' + tab);
                }
                
                // 将当前标签页保存到状态
                editorState.activeTab = tab;
                
                // 强制重新布局以确保编辑器正确显示
                if (tab === 'html' && editor) {
                    setTimeout(() => editor.layout(), 10);
                } else if (tab === 'css' && editorCSS) {
                    setTimeout(() => editorCSS.layout(), 10);
                } else if (tab === 'js' && editorJS) {
                    setTimeout(() => editorJS.layout(), 10);
                }
            });
        });
    }

    // 初始化按钮事件
    function initButtons() {
        const runButton = document.getElementById('run-button');
        if (runButton) {
            runButton.addEventListener('click', function() {
                runCodeOnBackend();
            });
        }

        const previewButton = document.getElementById('preview-button');
        if (previewButton) {
            previewButton.addEventListener('click', function() {
                updateLocalPreview();
            });
        }
        
        const refreshPreviewButton = document.getElementById('refresh-preview');
        if (refreshPreviewButton) {
            refreshPreviewButton.addEventListener('click', function() {
                updateLocalPreview();
            });
        }

        const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
        if (mobileMenuToggle) {
            mobileMenuToggle.addEventListener('click', function() {
                const sidebar = document.querySelector('.sidebar');
                if (sidebar) {
                    sidebar.classList.toggle('mobile-open');
                }
            });
        }
    }
    
    // 更新编辑器内容的函数
    function updateEditorContent(startCode) {
        // 更新编辑器状态
        if (startCode && typeof startCode === 'object') {
            editorState.html = startCode.html || '';
            editorState.css = startCode.css || '';
            editorState.js = startCode.js || '';
        }
        
        // 更新编辑器显示
        if (editor) {
            editor.setValue(editorState.html);
        }
        if (editorCSS) {
            editorCSS.setValue(editorState.css);
        }
        if (editorJS) {
            editorJS.setValue(editorState.js);
        }
        
        // 更新预览
        updateLocalPreview();
    }

    // 本地预览更新（仅用于快速刷新和初始化）
    function updateLocalPreview() {
        const previewFrame = document.getElementById('preview-frame');
        try {
            // 添加心跳和消息传递功能的脚本
            const consoleOverrideScript = `
                // 重写控制台方法，安全地传递给父窗口
                (function() {
                    const originalConsoleLog = console.log;
                    const originalConsoleError = console.error;
                    const originalConsoleWarn = console.warn;
                    
                    // 重写console.log
                    console.log = function() {
                        originalConsoleLog.apply(this, arguments);
                        try {
                            const logData = Array.from(arguments).map(arg => {
                                if (typeof arg === 'object') {
                                    try { return JSON.stringify(arg); }
                                    catch (e) { return String(arg); }
                                }
                                return String(arg);
                            }).join(' ');
                            window.parent.postMessage({ type: 'log', content: logData }, '*');
                        } catch (e) { /* 忽略错误 */ }
                    };
                    
                    // 重写console.error
                    console.error = function() {
                        originalConsoleError.apply(this, arguments);
                        try {
                            const errorData = Array.from(arguments).map(arg => {
                                if (typeof arg === 'object') {
                                    try { return JSON.stringify(arg); }
                                    catch (e) { return String(arg); }
                                }
                                return String(arg);
                            }).join(' ');
                            window.parent.postMessage({ type: 'error', content: errorData }, '*');
                        } catch (e) { /* 忽略错误 */ }
                    };
                    
                    // 重写console.warn
                    console.warn = function() {
                        originalConsoleWarn.apply(this, arguments);
                        try {
                            const warnData = Array.from(arguments).map(arg => {
                                if (typeof arg === 'object') {
                                    try { return JSON.stringify(arg); }
                                    catch (e) { return String(arg); }
                                }
                                return String(arg);
                            }).join(' ');
                            window.parent.postMessage({ type: 'warn', content: warnData }, '*');
                        } catch (e) { /* 忽略错误 */ }
                    };
                    
                    // 添加事件监听
                    document.addEventListener('click', function(event) {
                        try {
                            const element = event.target;
                            const elementInfo = {
                                tagName: element.tagName.toLowerCase(),
                                id: element.id || '',
                                className: element.className || '',
                                text: element.textContent ? element.textContent.substring(0, 50) : ''
                            };
                            window.parent.postMessage({ 
                                type: 'interaction', 
                                action: 'click', 
                                data: elementInfo 
                            }, '*');
                        } catch (e) { /* 忽略错误 */ }
                    });
                    
                    // 发送心跳信号，防止连接中断
                    function sendHeartbeat() {
                        try {
                            window.parent.postMessage({ type: 'heartbeat' }, '*');
                        } catch (e) { /* 忽略错误 */ }
                    }
                    
                    // 立即发送一次心跳，然后每秒发送一次
                    sendHeartbeat();
                    setInterval(sendHeartbeat, 1000);
                })();
            `;
            
            const content = `
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        ${editorState.cssEditor ? editorState.cssEditor.getValue() : editorState.css}
                    </style>
                </head>
                <body>
                    ${editorState.htmlEditor ? editorState.htmlEditor.getValue() : editorState.html}
                    <script>
                        ${consoleOverrideScript}
                        
                        try {
                            ${editorState.jsEditor ? editorState.jsEditor.getValue() : editorState.js}
                        } catch (error) {
                            console.error('JavaScript错误:', error);
                            const errorDiv = document.createElement('div');
                            errorDiv.style.position = 'fixed';
                            errorDiv.style.bottom = '10px';
                            errorDiv.style.left = '10px';
                            errorDiv.style.right = '10px';
                            errorDiv.style.padding = '10px';
                            errorDiv.style.backgroundColor = '#ffebee';
                            errorDiv.style.color = '#c62828';
                            errorDiv.style.border = '1px solid #ef9a9a';
                            errorDiv.style.borderRadius = '4px';
                            errorDiv.style.zIndex = '9999';
                            errorDiv.textContent = 'JavaScript错误: ' + error.message;
                            document.body.appendChild(errorDiv);
                        }
                    </script>
                </body>
                </html>
            `;

            // 直接写入Blob URL来避免跨域问题
            const blob = new Blob([content], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            previewFrame.src = url;
            
            // 清理旧的Blob URL
            previewFrame.onload = function() {
                URL.revokeObjectURL(url);
            };
            
            // 改进的心跳检测机制
            if (!window.hasHeartbeatListener) {
                // 使用自定义事件来接收心跳
                document.addEventListener('preview-heartbeat', function() {
                    window.lastPreviewHeartbeatTime = Date.now();
                    // 收到心跳，预览正常
                    console.log('预览心跳正常');
                });
                window.hasHeartbeatListener = true;
            }
            
            // 初始化心跳时间
            window.lastPreviewHeartbeatTime = Date.now();
            
            // 添加预览框架心跳检测
            if (window.localPreviewHeartbeatInterval) {
                clearInterval(window.localPreviewHeartbeatInterval);
            }
            
            window.localPreviewHeartbeatInterval = setInterval(() => {
                const currentTime = Date.now();
                const heartbeatTimeout = 8000; // 心跳超时时间，单位毫秒
                
                // 如果超过超时时间没有心跳，则重新加载预览
                if (currentTime - window.lastPreviewHeartbeatTime > heartbeatTimeout) {
                    console.log('预览心跳超时，尝试重新加载');
                    
                    // 尝试保持当前页面的段落和滚动位置
                    try {
                        // 更新预览
                        updateLocalPreview();
                        
                        // 重置心跳时间为当前时间
                        window.lastPreviewHeartbeatTime = currentTime;
                    } catch (e) {
                        console.error('重新加载预览出错:', e);
                    }
                }
            }, 2000); // 每2秒检查一次
        } catch (error) {
            console.error('生成预览出错:', error);
            showNotification('预览生成错误', 'error');
        }
    }
    
    // 在后端运行代码并更新预览
    function runCodeOnBackend() {
        if (editorState.isRunning) {
            return; // 防止重复点击
        }
        
        // 设置运行状态
        editorState.isRunning = true;
        const runButton = document.getElementById('run-button');
        runButton.textContent = '运行中...';
        runButton.disabled = true;
        
        // 执行静态检查
        performStaticCheck();
        
        // 立即更新本地预览，提高响应速度
        updateLocalPreview();
        
        // 显示消息提示用户正在连接到后端
        showNotification('预览已更新，正在连接到沙箱环境...', 'info', 1000);
        
        // 确保我们始终使用同一个会话ID，以确保后端只创建一个容器
        if (!editorState.sessionId) {
            // 如果没有会话ID，创建一个新的
            editorState.sessionId = generateUUID();
            console.log(`运行代码: 创建新的会话ID: ${editorState.sessionId}`);
            // 将会话ID保存到本地存储，即使页面刷新也能保持会话ID
            localStorage.setItem('editorSessionId', editorState.sessionId);
        } else {
            console.log(`运行代码: 使用现有会话ID: ${editorState.sessionId}`);
        }
        
        // 准备代码提交数据
        const codeData = {
            html: editorState.htmlEditor ? editorState.htmlEditor.getValue() : editorState.html,
            css: editorState.cssEditor ? editorState.cssEditor.getValue() : editorState.css,
            js: editorState.jsEditor ? editorState.jsEditor.getValue() : editorState.js,
            session_id: editorState.sessionId
        };
        
        // 尝试调用后端API，异步连接到沙箱环境
        fetch(`${editorState.backendUrl}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(codeData),
            // 设置超时，快速失败如果后端不可达
            timeout: 2000
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`服务器响应错误: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // 处理成功响应
            if (data.status === 'success') {
                // 保存容器ID以供后续请求使用
                // 注意：我们使用自己生成的会话ID，而不使用后端返回的容器ID
                // editorState.sessionId = data.container_id; // 不再直接使用容器ID做会话ID
                
                // 更新预览框
                if (data.preview_url) {
                    // 如果预览URL可用，更新到后端预览
                    updatePreviewWithBackendUrl(data.local_url || data.preview_url);
                    // 显示成功消息
                    showNotification('代码已在沙箱环境中运行', 'success');
                }
                // 注意：这里不再调用本地预览，因为我们已经在开始时调用过了
            } else {
                // 显示错误消息
                showNotification(`沙箱环境运行错误: ${data.message || '未知错误'}`, 'error');
                // 注意：不再调用本地预览，因为我们已经在开始时调用过了
            }
        })
        .catch(error => {
            console.error('运行代码出错:', error);
            showNotification(`沙箱环境连接错误，使用本地预览模式`, 'info');
            // 注意：不再调用本地预览，因为我们已经在开始时调用过了
        })
        .finally(() => {
            // 重置运行状态
            editorState.isRunning = false;
            runButton.textContent = '运行';
            runButton.disabled = false;
        });
    }
    
    // 生成UUID函数，用于生成全局唯一的会话ID
    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    // 使用后端URL更新预览框
    function updatePreviewWithBackendUrl(url) {
        const previewFrame = document.getElementById('preview-frame');
        previewFrame.src = url;
        
        // 添加30秒的心跳检查，确保预览保持连接
        if (window.previewHeartbeatInterval) {
            clearInterval(window.previewHeartbeatInterval);
        }
        
        window.previewHeartbeatInterval = setInterval(() => {
            // 检查iframe是否可访问
            try {
                if (!previewFrame.contentWindow || previewFrame.contentWindow.closed) {
                    // 预览窗口不可访问，尝试重新加载
                    console.log('预览窗口不可访问，尝试重新加载');
                    previewFrame.src = url;
                }
            } catch (e) {
                // 跨域错误或其他错误，尝试重新加载
                console.log('预览窗口出错，尝试重新加载');
                previewFrame.src = url;
            }
        }, 5000); // 每5秒检查一次
    }

    // 重置编辑器
    function resetEditor() {
        // 重置编辑器状态
        editorState = {
            activeTab: 'html',
            html: '<div class="demo">\n  <h1>欢迎使用HTML编辑器</h1>\n  <p>这是一个用于学习HTML、CSS和JavaScript的在线编辑器。</p>\n  <button id="demo-button">点击我</button>\n</div>',
            css: '.demo {\n  max-width: 600px;\n  margin: 20px auto;\n  padding: 20px;\n  font-family: Arial, sans-serif;\n  background-color: #f7f7f7;\n  border-radius: 8px;\n  box-shadow: 0 2px 4px rgba(0,0,0,0.1);\n}\n\nh1 {\n  color: #10a37f;\n}\n\nbutton {\n  background-color: #10a37f;\n  color: white;\n  border: none;\n  padding: 8px 16px;\n  border-radius: 4px;\n  cursor: pointer;\n}\n\nbutton:hover {\n  background-color: #0e906f;\n}',
            js: 'document.getElementById("demo-button").addEventListener("click", function() {\n  alert("按钮被点击了！");\n});',
            sessionId: null,
            isRunning: false,
            backendUrl: 'http://localhost:8000/api/ide'
        };

        // 更新编辑器内容
        if (editor) {
            const model = editor.getModel();
            monaco.editor.setModelLanguage(model, 'html');
            editor.setValue(editorState.html);
        }

        // 更新标签按钮状态
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(btn => btn.classList.remove('active'));
        document.querySelector('[data-tab="html"]').classList.add('active');

        // 更新预览
        updateLocalPreview();
        
        // 清理后端会话
        if (editorState.sessionId) {
            const oldSessionId = editorState.sessionId;
            console.log(`重置编辑器：清理会话ID ${oldSessionId}`);
            fetch(`${editorState.backendUrl}/cleanup/${oldSessionId}`, {
                method: 'POST'
            })
            .then(response => {
                if (response.ok) {
                    console.log(`会话 ${oldSessionId} 已成功清理`);
                    // 重置会话ID，确保下次会创建新容器
                    editorState.sessionId = null;
                    // 同时清除本地存储的会话ID
                    localStorage.removeItem('editorSessionId');
                } else {
                    console.error(`清理会话失败: ${response.status}`);
                }
            })
            .catch(error => console.error('清理会话失败:', error));
        }
    }

    // 执行静态检查
    function performStaticCheck() {
        try {
            const codeData = {
                html: editorState.htmlEditor ? editorState.htmlEditor.getValue() : editorState.html,
                css: editorState.cssEditor ? editorState.cssEditor.getValue() : editorState.css,
                js: editorState.jsEditor ? editorState.jsEditor.getValue() : editorState.js,
                session_id: editorState.sessionId
            };

            if (!editorState.sessionId) {
                editorState.sessionId = generateUUID();
            }
            codeData.session_id = editorState.sessionId;

            fetch(`${editorState.backendUrl}/static-check`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(codeData),
                timeout: 5000
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`服务器响应错误: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success' && data.details) {
                    showStaticCheckResults(data.details);
                }
            })
            .catch(error => {
                console.error('静态检查出错:', error);
            });
        } catch (error) {
            console.error('静态检查错误:', error);
        }
    }

    // 显示静态检查结果
    function showStaticCheckResults(results) {
        // 清除所有现有的错误标记
        if (window.currentDecorations) {
            editor.deltaDecorations(window.currentDecorations.html || [], []);
            editorCSS.deltaDecorations(window.currentDecorations.css || [], []);
            editorJS.deltaDecorations(window.currentDecorations.js || [], []);
        }
        
        window.currentDecorations = { html: [], css: [], js: [] };

        const problemsDiv = document.getElementById('problems-panel') || createProblemsPanel();
        problemsDiv.innerHTML = ''; // 清空现有内容

        let totalErrors = 0;
        let totalWarnings = 0;

        const processResults = (lang, editorInstance, resultsData) => {
            if (!resultsData) return;

            const errors = resultsData.errors || [];
            const warnings = resultsData.warnings || [];
            totalErrors += errors.length;
            totalWarnings += warnings.length;
            
            const decorations = [];
            const model = editorInstance.getModel();

            if (errors.length > 0) {
                const errorHeader = document.createElement('div');
                errorHeader.className = 'problem-category';
                errorHeader.innerHTML = `<span class="problem-icon error">⚠️</span> ${lang.toUpperCase()} 错误 (${errors.length})`;
                problemsDiv.appendChild(errorHeader);

                errors.forEach(error => {
                    if (error.line && error.column) {
                        const lineLength = model.getLineLength(error.line) || 1;
                        const endColumn = Math.min(error.column + 10, lineLength);
                        decorations.push({
                            range: new monaco.Range(error.line, error.column, error.line, endColumn),
                            options: {
                                inlineClassName: 'monaco-error-squiggle',
                                hoverMessage: { value: error.message },
                                overviewRuler: { color: '#FF0000', position: monaco.editor.OverviewRulerLane.Right },
                                minimap: { color: '#FF0000', position: monaco.editor.MinimapPosition.Inline }
                            }
                        });

                        const problemItem = document.createElement('div');
                        problemItem.className = 'problem-item';
                        problemItem.innerHTML = `
                            <span class="problem-icon error">⛔</span>
                            <span class="problem-message">${error.message}</span>
                            <span class="problem-location">[${error.line}:${error.column}]</span>
                        `;
                        problemItem.addEventListener('click', () => {
                            editorInstance.revealPositionInCenter({ lineNumber: error.line, column: error.column });
                            editorInstance.setPosition({ lineNumber: error.line, column: error.column });
                            editorInstance.focus();
                        });
                        problemsDiv.appendChild(problemItem);
                    }
                });
            }

            if (warnings.length > 0) {
                const warningHeader = document.createElement('div');
                warningHeader.className = 'problem-category';
                warningHeader.innerHTML = `<span class="problem-icon warning">⚠</span> ${lang.toUpperCase()} 警告 (${warnings.length})`;
                problemsDiv.appendChild(warningHeader);

                warnings.forEach(warning => {
                    if (warning.line && warning.column) {
                        const lineLength = model.getLineLength(warning.line) || 1;
                        const endColumn = Math.min(warning.column + 10, lineLength);
                        decorations.push({
                            range: new monaco.Range(warning.line, warning.column, warning.line, endColumn),
                            options: {
                                inlineClassName: 'monaco-warning-squiggle',
                                hoverMessage: { value: warning.message },
                                overviewRuler: { color: '#FFA500', position: monaco.editor.OverviewRulerLane.Right },
                                minimap: { color: '#FFA500', position: monaco.editor.MinimapPosition.Inline }
                            }
                        });

                        const problemItem = document.createElement('div');
                        problemItem.className = 'problem-item';
                        problemItem.innerHTML = `
                            <span class="problem-icon warning">⚠</span>
                            <span class="problem-message">${warning.message}</span>
                            <span class="problem-location">[${warning.line}:${warning.column}]</span>
                        `;
                        problemItem.addEventListener('click', () => {
                            editorInstance.revealPositionInCenter({ lineNumber: warning.line, column: warning.column });
                            editorInstance.setPosition({ lineNumber: warning.line, column: warning.column });
                            editorInstance.focus();
                        });
                        problemsDiv.appendChild(problemItem);
                    }
                });
            }
            
            window.currentDecorations[lang] = editorInstance.deltaDecorations(window.currentDecorations[lang] || [], decorations);
        };

        processResults('html', editor, results.html);
        processResults('css', editorCSS, results.css);
        processResults('js', editorJS, results.js);

        if (totalErrors > 0 || totalWarnings > 0) {
            problemsDiv.style.display = 'block';
        } else {
            problemsDiv.style.display = 'none';
        }
    }
    
    // 创建问题面板
    function createProblemsPanel() {
        const problemsDiv = document.createElement('div');
        problemsDiv.id = 'problems-panel';
        problemsDiv.className = 'problems-panel';
        
        // 添加标题栏
        const titleBar = document.createElement('div');
        titleBar.className = 'problems-titlebar';
        titleBar.innerHTML = `
            <span class="problems-title">问题</span>
            <button class="problems-close">×</button>
        `;
        problemsDiv.appendChild(titleBar);
        
        // 添加关闭按钮事件
        titleBar.querySelector('.problems-close').addEventListener('click', () => {
            problemsDiv.style.display = 'none';
        });
        
        // 添加到页面
        document.querySelector('.editor-container').appendChild(problemsDiv);
        
        return problemsDiv;
    }
    
    // 显示通知消息
    function showNotification(message, type = 'info', duration = 3000) {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // 添加到页面
        document.body.appendChild(notification);
        
        // 添加样式
        notification.style.position = 'fixed';
        notification.style.bottom = '20px';
        notification.style.right = '20px';
        notification.style.padding = '10px 15px';
        notification.style.borderRadius = '4px';
        notification.style.zIndex = '9999';
        notification.style.minWidth = '200px';
        notification.style.textAlign = 'center';
        
        // 根据类型设置样式
        if (type === 'success') {
            notification.style.backgroundColor = '#d4edda';
            notification.style.color = '#155724';
            notification.style.border = '1px solid #c3e6cb';
        } else if (type === 'error') {
            notification.style.backgroundColor = '#f8d7da';
            notification.style.color = '#721c24';
            notification.style.border = '1px solid #f5c6cb';
        } else {
            notification.style.backgroundColor = '#d1ecf1';
            notification.style.color = '#0c5460';
            notification.style.border = '1px solid #bee5eb';
        }
        
        // 自动移除
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.5s ease';
            setTimeout(() => notification.remove(), 500);
        }, duration);
    }
    
    // 初始化预览
    setTimeout(updateLocalPreview, 1000);
    
    // CSS样式注入
    const styleElement = document.createElement('style');
    styleElement.textContent = `
        /* Monaco Editor 错误和警告样式 */
        .monaco-error-squiggle {
            background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 6 3' enable-background='new 0 0 6 3' height='3' width='6'%3E%3Cg fill='%23ff0000'%3E%3Cpolygon points='5.5,0 2.5,3 1.1,3 4.1,0'/%3E%3Cpolygon points='4,0 6,2 6,0.6 5.4,0'/%3E%3Cpolygon points='0,2 1,3 2.4,3 0,0.6'/%3E%3C/g%3E%3C/svg%3E") repeat-x bottom left;
        }

        .monaco-warning-squiggle {
            background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 6 3' enable-background='new 0 0 6 3' height='3' width='6'%3E%3Cg fill='%23ffa500'%3E%3Cpolygon points='5.5,0 2.5,3 1.1,3 4.1,0'/%3E%3Cpolygon points='4,0 6,2 6,0.6 5.4,0'/%3E%3Cpolygon points='0,2 1,3 2.4,3 0,0.6'/%3E%3C/g%3E%3C/svg%3E") repeat-x bottom left;
        }

        /* 问题面板样式 */
        .problems-panel {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 150px;
            background-color: #f8f8f8;
            border-top: 1px solid #e0e0e0;
            z-index: 10;
            overflow-y: auto;
            display: none;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 12px;
            color: #333;
        }

        .problems-titlebar {
            padding: 5px 10px;
            background-color: #eee;
            border-bottom: 1px solid #ddd;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .problems-title {
            font-weight: bold;
        }

        .problems-close {
            background: none;
            border: none;
            font-size: 16px;
            cursor: pointer;
            color: #777;
        }

        .problems-close:hover {
            color: #000;
        }

        .problem-category {
            padding: 5px 10px;
            background-color: #f0f0f0;
            font-weight: bold;
            border-bottom: 1px solid #ddd;
        }

        .problem-item {
            padding: 5px 10px 5px 30px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            display: flex;
            align-items: center;
        }

        .problem-item:hover {
            background-color: #e8e8e8;
        }

        .problem-icon {
            margin-right: 6px;
        }

        .problem-message {
            flex-grow: 1;
        }

        .problem-location {
            color: #777;
            margin-left: 10px;
        }

        .notification {
            transition: opacity 0.5s ease;
            opacity: 1;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
    `;
    document.head.appendChild(styleElement);
});
