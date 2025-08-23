export class WebSocketManager {
            constructor() {
                this.socket = null;
                this.userId = null;
                this.reconnectAttempts = 0;
                this.maxReconnectAttempts = 5;
                this.currentAiMessageElement = null;
                this.messagesContainer = null;
            }
            
            // 连接WebSocket
            connect() {
                if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                    return;
                }
                try {
                    // 构建WebSocket URL，包含用户ID作为查询参数
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${protocol}//localhost:8000/ws/${this.userId}`;
                    this.socket = new WebSocket(wsUrl);
                    this.socket.onopen = () => {
                        this.reconnectAttempts = 0; // 重置重连尝试次数
                    };
                    
                    this.socket.onmessage = (event) => {
                        try {
                            const data = JSON.parse(event.data);
                            if (data.type === "stream") {
                                // 流式传输中
                                if (this.currentAiMessageElement) {
                                    this.appendMessageContent(this.currentAiMessageElement, data.message);
                                }
                            } 
                            else if (data.type === "stream_end") {
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
                            } 
                        } catch (e) {
                            //this.addMessage(event.data, 'received', '系统');
                            console.error('解析消息错误:', e);
                        }
                    };
                    
                    this.socket.onclose = (event) => {
                        // 尝试重新连接
                        if (this.reconnectAttempts < this.maxReconnectAttempts) {
                            this.reconnectAttempts++;
                            setTimeout(() => this.connect(), 3000);
                        }
                    };
                    
                    this.socket.onerror = (error) => {
                        console.error('WebSocket error:', error);
                    };
                    
                } catch (error) {
                    console.error('Failed to connect WebSocket:', error);
                }
            }
            
            // 发送消息
            sendMessage(message) {
                if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                    const messageData = {
                        userId: this.userId,
                        message: message
                    };
                    this.socket.send(JSON.stringify(messageData));
                } else {
                    console.error('WebSocket 未连接，无法发送消息');
                }
            }
            
            // 断开WebSocket连接
            disconnect() {
                if (this.socket) {
                    this.socket.close();
                    this.socket = null;
                }
            }
            // 追加内容到消息元素（更平滑的流式渲染）
            appendMessageContent(messageContentElement, content) {
                // 按流缓冲起来，使用 requestAnimationFrame 分片追加，避免每次小片段都触发大量重排
                if (!messageContentElement._streamBuffer) messageContentElement._streamBuffer = '';
                messageContentElement._streamBuffer += content;

                //TODO:对接已有界面后添加markdown模式的输出
                // // 如果这是一个 Markdown 流目标，我们还需要把原始 markdown 累积到 _mdBuffer
                // if (messageContentElement._isMarkdown) {
                //     if (!messageContentElement._mdBuffer) messageContentElement._mdBuffer = '';
                //     messageContentElement._mdBuffer += content;
                // }

                // 如果已有调度则无需重复调度
                if (messageContentElement._rafScheduled) return;
                messageContentElement._rafScheduled = true;

                const messagesContainer = this.messagesContainer;

                const FLUSH_CHUNK = 2; // 每帧最多追加的字符数，调大或调小以平衡流畅度与实时性

                const flush = () => {
                    messageContentElement._rafScheduled = false;

                    // 每次从缓冲区取出一段字符追加
                    const buffer = messageContentElement._streamBuffer || '';
                    if (!buffer) return;

                    const toAppend = buffer.slice(0, FLUSH_CHUNK);
                    // 如果是 markdown 流目标，优先用 marked 渲染整个已累积的 markdown 缓冲，否则使用 textContent 分片追加
                    if (messageContentElement._isMarkdown) {
                        // 渲染已累积的 markdown（尽量减少重渲染频率）
                        try {
                            // 为了避免频繁完全重写 innerHTML，我们只在每次 flush 时渲染整个已知的 mdBuffer
                            messageContentElement.innerHTML = marked(messageContentElement._mdBuffer || '');
                        } catch (e) {
                            // fallback: 追加纯文本片段
                            messageContentElement.textContent += toAppend;
                        }
                    } else {
                        // 使用 textContent 追加纯文本，避免 XSS 和重解析
                        messageContentElement.textContent += toAppend;
                    }

                    // 剩余写回缓冲区
                    messageContentElement._streamBuffer = buffer.slice(FLUSH_CHUNK);

                    // 平滑滚动到底部，但仅在用户接近底部时使用 smooth，避免用户查看历史消息时被打断
                    try {
                        const distanceFromBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight;
                        const useSmooth = distanceFromBottom < 80; // 阈值可调整
                        messagesContainer.scrollTo({ top: messagesContainer.scrollHeight, behavior: useSmooth ? 'smooth' : 'auto' });
                    } catch (e) {
                        // fallback
                        messagesContainer.scrollTop = messagesContainer.scrollHeight;
                    }

                    // 如果还有缓冲则在下一帧继续刷新
                    if (messageContentElement._streamBuffer && messageContentElement._streamBuffer.length > 0) {
                        messageContentElement._rafScheduled = true;
                        requestAnimationFrame(flush);
                    }
                };

                // 将 flush 暴露到元素，以便 stream_end 调用时触发分片完成
                messageContentElement._flushFn = () => {
                    // 如果已经在调度中，flush 会在当前 rAF 循环中自动完成
                    if (messageContentElement._rafScheduled) return;
                    messageContentElement._rafScheduled = true;
                    requestAnimationFrame(flush);
                };

                // 首次调度
                requestAnimationFrame(flush);
            }
        }
// 导出单例
const websocket = new WebSocketManager();
export default websocket;