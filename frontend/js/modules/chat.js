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

      // 使用封装的 apiClient 发送请求
      const data = await window.apiClient.post('/chat/ai/chat', requestBody);

      if (data.code === 200 && data.data && typeof data.data.ai_response === 'string') {
        // 添加AI回复到UI
        this.addMessageToUI('ai', data.data.ai_response);
      } else {
        // 即使请求成功，但如果响应内容为空或格式不正确，也抛出错误
        throw new Error(data.message || 'AI回复内容为空或格式不正确');
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
   * 获取对话历史
   * @returns {Array} 对话历史数组
   */
  getConversationHistory() {
    // TODO: 实现获取对话历史的逻辑
    // 这里可以遍历消息容器中的消息，构建对话历史数组
    // 为了简化，我们暂时返回空数组
    return [];
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