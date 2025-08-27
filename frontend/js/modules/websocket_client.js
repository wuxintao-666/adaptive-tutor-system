//TODO:Aeolyn:对接chat.js
//TODO:Aeolyn:对接上chat.js后将manager和connector逻辑分离
import { buildWebSocketUrl } from '../api_client.js';
import { getParticipantId } from './session.js';
class WebSocketManager {
            constructor() {
                this.socket = null;
                //this.state = "CLOSED";//CONNECTING|OPEN|CLOSED
                this.reconnectAttempts = 0;
                this.maxReconnectAttempts = 5;
                this.subscribers = {};  //{type:[callbacks]}
            }
            
            subscribe(type,callback){
                if(!this.subscribers[type])this.subscribers[type] = [];
                this.subscribers[type].push(callback);
            }

            unsubscribe(type,callback){
                if (this.subscribers[type]) {
                this.subscribers[type] = this.subscribers[type].filter(cb => cb !== callback);
            }}

            _dispatch_message(rawMessage){
                const { type, taskid, message, error, timestamp } = rawMessage;
                // if (error) {
                //     this.handleError(message);
                //     return;
                //     }
                if (this.subscribers[type]) {
                   this.subscribers[type].forEach(callback => callback(message));
                    }else {
                    console.warn(`收到未处理的消息类型: ${type}`, message);
                    }
            }
            // handleError(message) {
            //        console.error('WebSocket消息错误:', message.error);
    
            //             if (this.subscribers.error) {
            //                 this.subscribers.error.forEach(callback => callback(message));
            //             }
                        
            //             // 特殊处理：如果是认证错误，可能需要重新登录
            //             if (message.error.code === 'authentication_failed') {
            //                 this.handleAuthenticationError();
            //             }
            //     }


            // onOpen(callback) {
            //      this.onOpenCallback = callback;
            // }
            // onClose(callback) {
            //      this.onCloseCallback = callback;
            // }
            // 连接WebSocket
            async connect() {
                if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                    return;
                }
                try {
                    const wsUrl = buildWebSocketUrl(getParticipantId());
                    //const wsUrl = `${protocol}//localhost:8000/ws/chat/${this.userId}`;
                    alert('WebSocket URL: ' + wsUrl);
                    this.socket = new WebSocket(wsUrl);
                    this.socket.onopen = () => {
                        this.reconnectAttempts = 0; // 重置重连尝试次数
                       
                    };
                    this.socket.onmessage = (event) => {
                        try {
                            const data = JSON.parse(event.data);
                            this._dispatch_message(data);
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
                        // if (this.onCloseCallback) {
                        //        this.onCloseCallback();
                        //     }
                        // // 尝试重新连接
                        // if (this.reconnectAttempts < this.maxReconnectAttempts) {
                        //     this.reconnectAttempts++;
                            
                        //     setTimeout(() => this.connect(), 1000* (2 ** (this.reconnectAttempts-1))); 
                        // }
                        this._tryReconnect();
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
            _tryReconnect() {
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    const delay = Math.pow(2, this.reconnectAttempts) * 1000;
                    console.log(`重连中 (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})，等待 ${delay}ms`);
                    setTimeout(() => this.connect(), delay);
                    this.reconnectAttempts++;
                } else {
                    console.error("WebSocket 达到最大重连次数");
                }
            }
            
            // 断开WebSocket连接
            disconnect() {
                if (this.socket) {
                    this.socket.close();
                    this.socket = null;
                }
            }
            
            
        }
// 导出单例
const websocket = new WebSocketManager();
export default websocket;