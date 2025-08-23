// frontend/js/modules/chat.js
/**
 * Chat 前端聊天模块
 *
 * 目标：
 * - 提供一个通用的聊天界面，供学习页面和测试页面使用
 * - 处理与后端 /api/v1/chat/ai/chat 端点的通信
 * - 管理聊天UI的渲染和交互
 */

import { getParticipantId } from './session.js';
import { marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";
import websocket from './socket.js';

class ChatModule {
  constructor() {
    this.chatContainer = null;
    this.messagesContainer = null;
    this.inputElement = null;
    this.sendButton = null;
    this.isLoading = false;
  }

  /**
   * 初始化聊天模块
   * @param {string} mode - 模式 ('learning' 或 'test')
   * @param {string} contentId - 内容ID (学习内容ID或测试任务ID)
   */
  init(mode, contentId) {
    // 获取聊天界面元素
    this.chatContainer = document.querySelector('.ai-chat-messages');
    this.messagesContainer = document.getElementById('ai-chat-messages');
    this.inputElement = document.getElementById('user-message');
    this.sendButton = document.getElementById('send-message');

    if (!this.chatContainer || !this.messagesContainer || !this.inputElement || !this.sendButton) {
      console.warn('[ChatModule] 聊天界面元素未找到，无法初始化聊天模块');
      return;
    }

    // 绑定事件监听器
    this.bindEvents(mode, contentId);

    // 初始化并连接 WebSocket（供消息传输与接收）
    try {
      websocket.userId = getParticipantId ? getParticipantId() : websocket.userId;
      websocket.connect();

      // 附加一个额外的 message listener，不会覆盖 socket.js 内部的 onmessage
      if (websocket.socket) {
        websocket.socket.addEventListener('message', (event) => this._handleWsMessage(event));
      }
    } catch (e) {
      console.warn('[ChatModule] 无法连接 WebSocket，继续使用 HTTP 回退', e);
    }

    console.log('[ChatModule] 聊天模块初始化完成');
  }

  /**
   * 绑定事件监听器
   * @param {string} mode - 模式 ('learning' 或 'test')
   * @param {string} contentId - 内容ID
   */
  bindEvents(mode, contentId) {
    // 发送按钮点击事件
    this.sendButton.addEventListener('click', () => {
      this.sendMessage(mode, contentId);
    });

    // 回车键发送消息（Shift+Enter换行）
    this.inputElement.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage(mode, contentId);
      }
    });
  }

  /**
   * 发送消息到后端
   * @param {string} mode - 模式 ('learning' 或 'test')
   * @param {string} contentId - 内容ID
   */
  async sendMessage(mode, contentId) {
    const message = this.inputElement.value.trim();
    if (!message || this.isLoading) return;

    // 清空输入框
    this.inputElement.value = '';

    // 添加用户消息到UI
    this.addMessageToUI('user', message);

    // 设置加载状态
    this.setLoadingState(true);

    try {
      // 构建请求体 (participant_id 会由 apiClient 自动注入)
      const requestBody = {
        user_message: message,
        conversation_history: this.getConversationHistory(),
        code_context: this.getCodeContext(),
        mode: mode,
        content_id: contentId
      };

      // 如果是测试模式，添加测试结果
      if (mode === 'test') {
        const testResults = this._getTestResults();
        if (testResults) {
          requestBody.test_results = testResults;
        }
      }

      // 优先通过已创建的 WebSocket 发送（如果存在且已打开）
      if (websocket && websocket.socket && websocket.socket.readyState === WebSocket.OPEN) {
        const wsPayload = {
          type: 'chat_request',
          userId: websocket.userId || getParticipantId?.(),
          payload: requestBody
        };
        websocket.socket.send(JSON.stringify(wsPayload));
        // 后端回复将通过 websocket 的 message 事件到达，我们在 _handleWsMessage 中处理渲染
      } else {
        // 回退到原先的 HTTP API
        const data = await window.apiClient.post('/chat/ai/chat', requestBody);

        if (data.code === 200 && data.data && typeof data.data.ai_response === 'string') {
          // 添加AI回复到UI
          this.addMessageToUI('ai', data.data.ai_response);
        } else {
          // 即使请求成功，但如果响应内容为空或格式不正确，也抛出错误
          throw new Error(data.message || 'AI回复内容为空或格式不正确');
        }
      }
    } catch (error) {
      console.error('[ChatModule] 发送消息时出错:', error);
      this.addMessageToUI('ai', `抱歉，我无法回答你的问题。错误信息: ${error.message}`);
    } finally {
      // 取消加载状态
      this.setLoadingState(false);
    }
  }

  /**
   * 处理来自 WebSocket 的消息，支持流式分片（stream）和普通消息
   * @private
   */
  _handleWsMessage(event) {
    if (!event || !event.data) return;
    try {
      const data = JSON.parse(event.data);

      // 支持后端直接返回 data.data.ai_response（兼容原 HTTP 响应）
      if (data.data && typeof data.data.ai_response === 'string') {
        this.setLoadingState(false);
        this.addMessageToUI('ai', data.data.ai_response);
        return;
      }

      // 如果后端使用统一字段 message
      if (data.message && !data.type) {
        this.setLoadingState(false);
        this.addMessageToUI('ai', data.message);
        return;
      }

      // 处理流式分片事件（stream_start / stream / stream_end）
      if (data.type === 'stream_start') {
        // 在UI中创建占位AI消息元素并记录为当前流元素
        this.setLoadingState(true);
        this.addMessageToUI('ai', '');
        // 保存一个指向最后一个 ai-message 元素的引用，供后续分片追加
        this._currentStreamElement = this.messagesContainer.querySelector('.ai-message:last-child .markdown-content');
        return;
      }

      if (data.type === 'stream') {
        if (this._currentStreamElement) {
          // 直接追加纯文本，保留 markdown 渲染为后续整段完成时的责任
          this._currentStreamElement.textContent += data.message || '';
          this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
        return;
      }

      if (data.type === 'stream_end') {
        if (this._currentStreamElement && data.message) {
          this._currentStreamElement.textContent += data.message;
        }
        this._currentStreamElement = null;
        this.setLoadingState(false);
        return;
      }

    } catch (e) {
      console.error('[ChatModule] 解析 WebSocket 消息失败', e);
    }
  }

  /**
   * 添加消息到UI
   * @param {string} sender - 发送者 ('user' 或 'ai')
   * @param {string} content - 消息内容
   */
  addMessageToUI(sender, content) {
    if (!this.messagesContainer) return;

    const messageElement = document.createElement('div');
    messageElement.classList.add(`${sender}-message`);

    if (sender === 'user') {
      const contentDiv = document.createElement('div');
      contentDiv.className = 'markdown-content';
      contentDiv.textContent = content;
      messageElement.innerHTML = `
        <div class="user-avatar">你</div>
        <div class="user-content">
          ${contentDiv.outerHTML}
        </div>
      `;
    } else {
      messageElement.innerHTML = `
        <div class="ai-avatar">AI</div>
        <div class="ai-content">
          <div class="markdown-content">${marked(content)}</div>
        </div>
      `;
    }

    this.messagesContainer.appendChild(messageElement);

    // 滚动到底部
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }

  /**
   * 设置加载状态
   * @param {boolean} loading - 是否加载中
   */
  setLoadingState(loading) {
    this.isLoading = loading;
    if (this.sendButton) {
      this.sendButton.disabled = loading;
      this.sendButton.textContent = loading ? '发送中...' : '提问';
    }
    
    // 添加或移除加载指示器
    if (loading) {
      const loadingElement = document.createElement('div');
      loadingElement.id = 'ai-loading';
      loadingElement.classList.add('ai-message');
      loadingElement.innerHTML = `
        <div class="ai-avatar">AI</div>
        <div class="ai-content">
          <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      `;
      this.messagesContainer.appendChild(loadingElement);
      this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    } else {
      const loadingElement = document.getElementById('ai-loading');
      if (loadingElement) {
        loadingElement.remove();
      }
    }
  }

  /**
   * 获取测试结果
   * @returns {Array|null} 测试结果数组或null
   * @private
   */
  /**
   * 获取测试结果
   * @returns {Array|null} 测试结果数组或null
   * @private
   */
  _getTestResults() {
    const resultsContainer = document.getElementById('test-results-content');
    if (!resultsContainer || !resultsContainer.innerHTML.trim()) {
      return null;
    }

    const results = [];
    const overallStatus = resultsContainer.classList.contains('test-result-passed') ? 'success' : 'error';

    // 提取主标题和副标题
    const mainHeader = resultsContainer.querySelector('h4');
    const subMessage = resultsContainer.querySelector('p');

    if (mainHeader) {
      results.push({
        status: overallStatus,
        message: mainHeader.textContent.trim()
      });
    }

    if (subMessage && subMessage.textContent.trim()) {
      results.push({
        status: 'info',
        message: subMessage.textContent.trim()
      });
    }

    // 提取详细信息
    const detailItems = resultsContainer.querySelectorAll('ul > li');
    detailItems.forEach(item => {
      results.push({
        status: overallStatus === 'success' ? 'info' : 'error', // 细节项跟随总体状态
        message: item.textContent.trim()
      });
    });

    return results.length > 0 ? results : null;
  }

  /**
   * 获取对话历史
   * @returns {Array} 对话历史数组
   */
  getConversationHistory() {
    if (!this.messagesContainer) {
      console.warn('[ChatModule] 消息容器未找到，无法获取对话历史');
      return [];
    }

    const history = [];
    // 获取所有消息元素（用户消息和AI消息，但不包括加载指示器）
    const messageElements = this.messagesContainer.querySelectorAll('.user-message, .ai-message:not(#ai-loading)');

    messageElements.forEach(element => {
      const isUserMessage = element.classList.contains('user-message');
      const isAiMessage = element.classList.contains('ai-message');

      if (isUserMessage || isAiMessage) {
        // 提取消息文本内容
        let textContent = '';
        const markdownContent = element.querySelector('.markdown-content');
        
        if (markdownContent) {
          // 如果是AI消息，markdownContent包含HTML，需要提取纯文本
          // 如果是用户消息，markdownContent是纯文本节点
          if (isAiMessage) {
            textContent = markdownContent.textContent || markdownContent.innerText || '';
          } else {
            textContent = markdownContent.textContent || markdownContent.innerText || '';
          }
        } else {
          // 作为后备方案，尝试从其他内容元素获取文本
          const contentElement = element.querySelector('.user-content, .ai-content');
          if (contentElement) {
            textContent = contentElement.textContent || contentElement.innerText || '';
          }
        }

        // 添加到历史记录中
        history.push({
          role: isUserMessage ? 'user' : 'assistant',
          content: textContent.trim()
        });
      }
    });

    return history;
  }

  /**
   * 获取代码上下文
   * @returns {Object} 代码上下文对象
   */
  getCodeContext() {
    // 尝试从全局编辑器状态获取代码
    try {
      if (window.editorState) {
        return {
          html: window.editorState.htmlEditor?.getValue() || '',
          css: window.editorState.cssEditor?.getValue() || '',
          js: window.editorState.jsEditor?.getValue() || ''
        };
      }
    } catch (e) {
      console.warn('[ChatModule] 获取代码上下文时出错:', e);
    }
    
    // 如果无法获取，返回空字符串
    return {
      html: '',
      css: '',
      js: ''
    };
  }

}

// 导出单例
const chatModule = new ChatModule();
export default chatModule;