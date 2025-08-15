// 导入会话管理模块
import { getParticipantId } from '../modules/session.js';

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 获取提交按钮
    const submitButton = document.getElementById('submit-button');
    
    // 从URL获取topicId
    const topicId = new URLSearchParams(window.location.search).get('topic');
    
    // 从localStorage获取用户ID
    const participant_id = getParticipantId();
    
    // 添加提交按钮事件监听器
    if (submitButton) {
        submitButton.addEventListener('click', async () => {
            // 禁用按钮并显示加载状态
            const originalText = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.textContent = '批改中...';
            
            try {
                // 从全局编辑器状态获取代码
                const submissionData = {
                    participant_id: participant_id,
                    topic_id: topicId,
                    code: {
                        html: window.editorState?.html || '',
                        css: window.editorState?.css || '',
                        js: window.editorState?.js || ''
                    }
                };
                
                // 调用API提交测试
                const result = await window.apiClient.post('/submit-test', submissionData);
                
                if (result.code === 200) {
                    const testResult = result.data;
                    displayTestResult(testResult);
                    
                    // 如果通过测试，跳转回知识图谱
                    if (testResult.passed) {
                        alert("测试完成！即将跳转回到知识图谱界面");
                        setTimeout(() => {
                            window.location.href = '/pages/knowledge_graph.html';
                        }, 3000);
                    }
                } else {
                    throw new Error(result.message || '提交失败');
                }
            } catch (error) {
                console.error('提交测试时出错:', error);
                alert('提交测试时出错: ' + (error.message || '未知错误'));
            } finally {
                // 确保按钮状态完全恢复
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }
        });
    }
});

// 显示测试结果
function displayTestResult(result) {
    const testResultsContent = document.getElementById('test-results-content');
    
    if (testResultsContent) {
        let message = result.passed ? '✅ 恭喜！所有测试点都通过了！' : '❌ 很遗憾，部分测试点未通过。';
        
        if (result.details && result.details.length > 0) {
            message += '\n\n详细信息:\n' + result.details.join('\n');
        }
        
        // 使用textContent而不是innerHTML以防止XSS攻击
        testResultsContent.textContent = message;
        
        // 添加适当的样式类
        if (result.passed) {
            testResultsContent.className = 'test-result-passed';
        } else {
            testResultsContent.className = 'test-result-failed';
        }
    } else {
        // 如果找不到测试结果区域，使用alert显示
        let message = result.passed ? '✅ 恭喜！所有测试点都通过了！' : '❌ 很遗憾，部分测试点未通过。';
        if (result.details && result.details.length > 0) {
            message += '\n\n详细信息:\n' + result.details.join('\n');
        }
        alert(message);
    }
}