// 导入模块
import { getParticipantId } from '../modules/session.js';
import { marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";
import { createLivePreview } from '../modules/live_preview.js';

// 初始化函数
async function initializePage() {
    // 获取URL参数
    const urlParams = new URLSearchParams(window.location.search);
    
    // 先尝试获取topic参数，如果没有则检查是否直接在查询字符串中（如?1_1）
    let topicId = urlParams.get('topic');
    
    // 如果没有topic参数，且查询字符串只有一个值，则使用该值
    if (!topicId) {
        // 获取所有参数的键
        const keys = Array.from(urlParams.keys());
        // 如果没有键（如?1_1），则使用整个查询字符串
        if (keys.length === 0 && window.location.search.length > 1) {
            topicId = window.location.search.substring(1); // 去掉开头的'?'
        }
        // 如果有键但键为空字符串（这种情况较少见），则使用第一个值
        else if (keys.length === 1 && keys[0] === '') {
            topicId = urlParams.get('');
        }
    }
    
    if (!topicId) {
        console.error('未找到Topic ID');
        alert('错误：无效的测试链接。');
        return;
    }

    try {
        // 使用不带认证的get方法获取测试任务数据
        const response = await window.apiClient.getWithoutAuth(`/test-tasks/${topicId}`);
        if (response.code === 200 && response.data) {
            const task = response.data;
            // 更新UI
            updateUIWithTaskData(task);
            // 初始化编辑器
            initializeEditors(task.start_code);
            // 设置聊天功能
            setupChat(topicId); 
        } else {
            throw new Error(response.message || '获取测试任务失败');
        }
    } catch (error) {
        console.error('初始化页面时出错:', error);
        alert('无法加载测试任务: ' + (error.message || '未知错误'));
    }
}

// 更新UI
function updateUIWithTaskData(task) {
    const headerTitle = document.querySelector('.header-title');
    const requirementsContent = document.getElementById('test-requirements-content');
    if (headerTitle) {
        headerTitle.textContent = task.title || '编程测试';
    }
    if (requirementsContent) {
        requirementsContent.innerHTML = marked(task.description_md || '');
    }
}

// 初始化Monaco编辑器并设置实时预览
function initializeEditors(startCode) {
    if (window.monaco) {
        window.editorState = window.editorState || {};

        const editors = {
            html: monaco.editor.create(document.getElementById('monaco-editor'), {
                value: startCode?.html || '', language: 'html', theme: 'vs-dark'
            }),
            css: monaco.editor.create(document.getElementById('monaco-editor-css'), {
                value: startCode?.css || '', language: 'css', theme: 'vs-dark'
            }),
            js: monaco.editor.create(document.getElementById('monaco-editor-js'), {
                value: startCode?.js || '', language: 'javascript', theme: 'vs-dark'
            })
        };
        
        window.editorState.html = editors.html;
        window.editorState.css = editors.css;
        window.editorState.js = editors.js;

        // 设置实时预览
        const iframe = document.getElementById('preview-frame');
        if (iframe) {
            const livePreviewManager = createLivePreview({ html: editors.html, css: editors.css, js: editors.js }, iframe);
            livePreviewManager.triggerUpdate(); // 初始渲染
        } else {
            console.error("未找到预览iframe。");
        }

    } else {
        console.error("Monaco Editor 未加载。");
    }
}

// 设置聊天功能
function setupChat(topicId) {
    // TODO: 实现聊天功能
    console.log('聊天功能尚未实现，topicId:', topicId);
    // const buildChatContext = () => {
    //     return {
    //         code_context: {
    //             html: window.editorState.html?.getValue() || '',
    //             css: window.editorState.css?.getValue() || '',
    //             js: window.editorState.js?.getValue() || ''
    //         },
    //         task_context: `test:${topicId}` // 关键区别
    //     };
    // };
    // initializeChat(buildChatContext);
}

// 提交逻辑
function setupSubmitLogic() {
    const submitButton = document.getElementById('submit-button');
    if (!submitButton) return;
    
    submitButton.addEventListener('click', async () => {
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = '批改中...';
        
        try {
            const topicId = new URLSearchParams(window.location.search).get('topic');
            const participant_id = getParticipantId();
            if (!participant_id || !topicId) throw new Error("用户或主题ID无效。");
            
            const submissionData = {
                participant_id: participant_id,
                topic_id: topicId,
                code: {
                    html: window.editorState.html?.getValue() || '',
                    css: window.editorState.css?.getValue() || '',
                    js: window.editorState.js?.getValue() || ''
                }
            };
            
            const result = await window.apiClient.post('/submission/submit-test', submissionData);
            
            if (result.code === 200) {
                displayTestResult(result.data);
                if (result.data.passed) {
                    alert("测试完成！即将跳转回到知识图谱界面");
                    setTimeout(() => { window.location.href = '/pages/knowledge_graph.html'; }, 3000);
                }
            } else {
                throw new Error(result.message || '提交失败');
            }
        } catch (error) {
            console.error('提交测试时出错:', error);
            alert('提交测试时出错: ' + (error.message || '未知错误'));
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = originalText;
        }
    });
}

// 显示测试结果
function displayTestResult(result) {
    const testResultsContent = document.getElementById('test-results-content');
    if (!testResultsContent) {
        console.warn("未找到 'test-results-content' 元素。");
        const message = `${result.passed ? '✅ 通过' : '❌ 失败'}: ${result.message}\n\n详情:\n${(result.details || []).join('\n')}`;
        alert(message);
        return;
    }
    
    let content = `<h4>${result.passed ? '✅ 恭喜！通过测试！' : '❌ 未通过测试'}</h4><p>${result.message || ''}</p>`;
    if (result.details && result.details.length > 0) {
        content += `<h5>详细信息:</h5><ul>${result.details.map(d => `<li>${d}</li>`).join('')}</ul>`;
    }
    
    testResultsContent.innerHTML = content;
    testResultsContent.className = result.passed ? 'test-result-passed' : 'test-result-failed';
}

// 主程序入口
document.addEventListener('DOMContentLoaded', function() {
    require(['vs/editor/editor.main'], function () {
        initializePage();
        setupSubmitLogic();
    });
});
