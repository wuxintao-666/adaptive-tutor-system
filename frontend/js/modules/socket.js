//TODO:Aeolyn:对接chat.js
//TODO:Aeolyn:对接上chat.js后将manager和connector逻辑分离
import {AppConfig} from './config.js'
class WebSocketManager {
            constructor() {
                this.socket = null;
                this.userId = null;
                this.reconnectAttempts = 0;
                this.maxReconnectAttempts = 5;
                this.currentAiMessageElement = null;
                this.onMessageCallback = null;
                this.onOpenCallback = null;
                this.onCloseCallback = null;
            }
            // 允许外部注册回调
            onMessage(callback) {
                 this.onMessageCallback = callback;
            }
            onOpen(callback) {
                 this.onOpenCallback = callback;
            }
            onClose(callback) {
                 this.onCloseCallback = callback;
            }
            // 连接WebSocket
            connect() {
                if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                    //this.addMessage('WebSocket 已经连接', 'system');
                    //弹出界面
                    //alert('WebSocket 已经连接');
                    return;
                }
                try {
                    //alert('开始连接WebSocket');
                    // 构建WebSocket URL，包含用户ID作为查询参数
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    // 分开写 host 和 port
                    const host = window.location.hostname;  // 只拿到域名或IP，不带端口
                    const port =  AppConfig.backend_port;
                    // 没有 port 时用默认 80/443
                    const wsUrl = `${protocol}//${host}:${port}/ws/chat/${this.userId}`;
                    //const wsUrl = `${protocol}//localhost:8000/ws/chat/${this.userId}`;
                    alert('WebSocket URL: ' + wsUrl);
                    this.socket = new WebSocket(wsUrl);
                    
                    this.socket.onopen = () => {
                        if (this.onOpenCallback) {
                               this.onOpenCallback();
                            }
                        this.updateConnectionStatus(true);
                        this.addMessage('WebSocket 连接已建立', 'system');
                        this.reconnectAttempts = 0; // 重置重连尝试次数
                        
                        // 启用发送消息的输入框和按钮
                        document.getElementById('messageInput').disabled = false;
                        document.getElementById('sendBtn').disabled = false;
                    };
                    //TODO:Aeolyn:将流式输出部分拆成单独的工具函数
                    this.socket.onmessage = (event) => {
                        try {
                            const data = JSON.parse(event.data);
                            if (this.onMessageCallback) {
                               this.onMessageCallback(data, event);
                            }
                            /* 
                            if (data.type === "stream_start") {
                                // 开始流式传输
                                //this.showTypingIndicator(false);
                                this.currentAiMessageElement = this.addMessage('', 'ai', 'AI');
                            } else if (data.type === "stream") {
                                // 流式传输中
                                if (this.currentAiMessageElement) {
                                    this.appendMessageContent(this.currentAiMessageElement, data.message);
                                }
                            } else if (data.type === "stream_end") {
                                        // 流式传输结束：如果 stream_end 携带最后一段文本，先通过 appendMessageContent 入缓冲，
                                        // 然后调用元素的分片 flush 函数完成剩余内容，避免一次性大块追加
                                        if (this.currentAiMessageElement) {
                                            const el = this.currentAiMessageElement;
                                            if (data.message) {
                                                this.appendMessageContent(el, data.message);
                                            }
                                            if (el._flushFn) {
                                                el._flushFn();
                                            } else if (el._streamBuffer && el._streamBuffer.length > 0) {
                                                el.textContent += el._streamBuffer;
                                                el._streamBuffer = '';
                                            }
                                        }
                                        this.currentAiMessageElement = null;
                                    } else {
                                // 普通消息
                                this.addMessage(data.message, 'received', data.sender);
                            }
                            */
                        } catch (e) {
                            //this.addMessage(event.data, 'received', '系统');
                            console.error('解析消息错误:', e);
                        }
                    };
                    
                    this.socket.onclose = (event) => {
                        //this.updateConnectionStatus(false);
                        //this.addMessage('WebSocket 连接已关闭', 'system');
                        
                        // 禁用发送消息的输入框和按钮
                        // document.getElementById('messageInput').disabled = true;
                        // document.getElementById('sendBtn').disabled = true;
                        if (this.onCloseCallback) {
                               this.onCloseCallback();
                            }
                        // 尝试重新连接
                        if (this.reconnectAttempts < this.maxReconnectAttempts) {
                            this.reconnectAttempts++;
                            //this.addMessage(`尝试重新连接 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`, 'system');
                            setTimeout(() => this.connect(), 3000);
                        }
                    };
                    
                    this.socket.onerror = (error) => {
                        //this.addMessage('WebSocket 错误发生', 'system');
                        console.error('WebSocket error:', error);
                    };
                    
                } catch (error) {
                    console.error('Failed to connect WebSocket:', error);
                    //this.addMessage('连接失败: ' + error.message, 'system');
                }
            }
        
            
            // 断开WebSocket连接
            disconnect() {
                if (this.socket) {
                    this.socket.close();
                    this.socket = null;
                }
                //this.updateConnectionStatus(false);
            }
            
            
        }
// 导出单例
const websocket = new WebSocketManager();
export default websocket;