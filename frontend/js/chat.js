class ChatService {
    constructor() {
        this.ws = null;
        this.participantId = 'user_' + Math.random().toString(36).substr(2, 9); // 生成随机用户ID
        this.sessionId = 'session_' + Date.now(); // 生成会话ID
        this.messageContainer = document.getElementById('messageContainer');
        this.statusElement = document.getElementById('connectionStatus');
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        this.reconnectDelay = 5000; // 5秒

        this.connect();
    }

    connect() {
        try {
            // 连接WebSocket，传入participant_id参数
            this.ws = new WebSocket(`ws://localhost:8000/chat?participant_id=${this.participantId}&`);
            this.setupEventHandlers();
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.handleReconnection();
        }
    }

    setupEventHandlers() {
        if (!this.ws) return;

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.statusElement.textContent = '已连接';
            this.statusElement.style.color = '#4CAF50';
            this.reconnectAttempts = 0;
        };

        this.ws.onmessage = (event) => {
            try {
                const response = JSON.parse(event.data);
                this.handleMessage(response);
            } catch (error) {
                console.error('Error parsing message:', error);
            }
        };

        this.ws.onclose = () => {
            console.log('WebSocket connection closed');
            this.statusElement.textContent = '连接已断开';
            this.statusElement.style.color = '#f44336';
            this.handleReconnection();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.statusElement.textContent = '连接错误';
            this.statusElement.style.color = '#f44336';
        };
    }

    handleMessage(response) {
        switch (response.type) {
            case 'chunk':
                this.handleChunkResponse(response);
                break;
            case 'end':
                this.handleEndResponse(response);
                break;
            case 'error':
                this.handleErrorResponse(response);
                break;
            case 'heartbeat':
                this.handleHeartbeat();
                break;
        }
    }

    handleChunkResponse(response) {
        // 显示AI的响应
        this.appendMessage(response.content, 'ai');
    }

    handleEndResponse(response) {
        console.log('Response ended for session:', response.session_id);
    }

    handleErrorResponse(response) {
        console.error('Error from server:', response.content);
        this.appendMessage(`错误: ${response.content}`, 'error');
    }

    handleHeartbeat() {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'heartbeat_response',
                timestamp: new Date().toISOString()
            }));
        }
    }

    handleReconnection() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.statusElement.textContent = `正在尝试重新连接 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`;
            setTimeout(() => this.connect(), this.reconnectDelay);
        } else {
            this.statusElement.textContent = '重连失败，请刷新页面重试';
        }
    }

    appendMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.textContent = content;
        this.messageContainer.appendChild(messageDiv);
        // 滚动到最新消息
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    }

    async sendMessage(content) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            alert('WebSocket未连接，请等待重连或刷新页面');
            return;
        }

        // 显示用户发送的消息
        this.appendMessage(content, 'user');

        const message = {
            content: content,
            session_id: this.sessionId,
            type: 'message'
        };

        try {
            this.ws.send(JSON.stringify(message));
        } catch (error) {
            console.error('Error sending message:', error);
            this.appendMessage('消息发送失败', 'error');
        }
    }
}

// 创建聊天服务实例
let chatService = new ChatService();

// 发送消息的全局函数
function sendMessage() {
    const input = document.getElementById('messageInput');
    const content = input.value.trim();
    
    if (content) {
        chatService.sendMessage(content);
        input.value = ''; // 清空输入框
    }
}

// 添加回车键发送功能
document.getElementById('messageInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
