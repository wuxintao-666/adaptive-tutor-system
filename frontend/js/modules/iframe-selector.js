
// ==================== 工具函数 ====================
function getElementAtPoint(x, y) {
    const elementsStack = document.elementsFromPoint(x, y);
    const refElement = elementsStack.find((element) => !element.closest('svg') &&
        !element.closest('.sw-selector') &&
        isElementAtPoint(element, x, y)) || document.body;
    return refElement;
}

function isElementAtPoint(element, clientX, clientY) {
    const boundingRect = element.getBoundingClientRect();
    const isInHorizontalBounds = clientX >= boundingRect.left &&
        clientX <= boundingRect.left + boundingRect.width;
    const isInVerticalBounds = clientY >= boundingRect.top &&
        clientY <= boundingRect.top + boundingRect.height;
    return isInHorizontalBounds && isInVerticalBounds;
}

function getElementXPath(element) {
    if (!element || element.nodeType !== Node.ELEMENT_NODE) {
        return '';
    }
    if (element.id) {
        return `//*[@id="${element.id}"]`;
    }
    
    const paths = [];
    for (; element && element.nodeType === Node.ELEMENT_NODE; element = element.parentNode) {
        let index = 0;
        let hasFollowingSiblings = false;
        
        for (let sibling = element.previousSibling; sibling; sibling = sibling.previousSibling) {
            if (sibling.nodeType !== Node.ELEMENT_NODE) continue;
            if (sibling.tagName === element.tagName) {
                index++;
            }
        }
        
        for (let sibling = element.nextSibling; sibling && !hasFollowingSiblings; sibling = sibling.nextSibling) {
            if (sibling.nodeType !== Node.ELEMENT_NODE) continue;
            if (sibling.tagName === element.tagName) {
                hasFollowingSiblings = true;
            }
        }
        
        const tagName = element.tagName.toLowerCase();
        const pathIndex = (index || hasFollowingSiblings) ? `[${index + 1}]` : '';
        paths.unshift(tagName + pathIndex);
        
        if (element.id) {
            paths.unshift(`*[@id="${element.id}"]`);
            break;
        }
    }
    return '/' + paths.join('/');
}

function getElementInfo(element) {
    const bbox = element.getBoundingClientRect();
    const computedStyle = window.getComputedStyle(element);
    
    return {
        tagName: element.tagName.toLowerCase(),
        id: element.id || '',
        className: element.className || '',
        classList: Array.from(element.classList || []),
        textContent: element.textContent?.trim().substring(0, 100) || '',
        outerHTML: element.outerHTML?.substring(0, 500) || '',
        selector: getElementXPath(element),
        bounds: { x: bbox.left, y: bbox.top, width: bbox.width, height: bbox.height },
        styles: {
            backgroundColor: computedStyle.backgroundColor,
            color: computedStyle.color,
            fontSize: computedStyle.fontSize
        },
        pageURL: window.location.href
    };
}

// ==================== 元素选择器 ====================
const MAX_Z_INDEX = 2147483646;

class ElementSelector {
    constructor(options = {}) {
        this.selectorEl = null;
        this.highlightEl = null;
        this.lastHoveredElement = null;
        this.isActive = false;
        this.currentElements = options.currentElements || [];  // 当前章节元素
        this.cumulativeElements = options.cumulativeElements || [];  // 累积元素
        
        this.handleMouseMove = (event) => {
            requestAnimationFrame(() => {
                if (this.highlightEl && this.highlightEl.style.display !== 'none') {
                    this.highlightEl.style.display = 'none';
                }
                
                const refElement = getElementAtPoint(event.clientX, event.clientY);
                if (!refElement) {
                    console.log('未找到元素在坐标:', event.clientX, event.clientY);
                    this.hideHighlight();
                    return;
                }
                
                if (this.shouldIgnoreElement(refElement)) {
                    console.log('元素被忽略:', refElement.tagName.toLowerCase());
                    this.hideHighlight();
                    return;
                }
                
                if (this.lastHoveredElement === refElement) {
                    if (this.highlightEl && this.highlightEl.style.display === 'none') {
                        this.updateHighlight(refElement);
                    }
                    return;
                }
                
                if (this.lastHoveredElement !== refElement) {
                    if (this.lastHoveredElement && this.options.onElementUnhovered) {
                        this.options.onElementUnhovered();
                    }
                    this.lastHoveredElement = refElement;
                    this.updateHighlight(refElement);
                    if (this.options.onElementHovered) {
                        this.options.onElementHovered(refElement);
                    }
                }
            });
        };
        
        this.handleMouseLeave = () => {
            this.hideHighlight();
            this.lastHoveredElement = null;
            if (this.options.onElementUnhovered) {
                this.options.onElementUnhovered();
            }
        };
        
        this.handleMouseClick = (event) => {
            event.preventDefault();
            event.stopPropagation();
            if (!this.lastHoveredElement) return;
            if (this.shouldIgnoreElement(this.lastHoveredElement)) return;
            
            const elementInfo = getElementInfo(this.lastHoveredElement);
            if (this.options.onElementSelected) {
                this.options.onElementSelected(this.lastHoveredElement, elementInfo);
            }
            this.stop();
        };
        
        this.handleKeyDown = (event) => {
            if (event.key === 'Escape') {
                this.stop();
            }
        };
        
        this.options = {
            ignoreSelectors: ['.sw-selector', '.sw-highlight'],
            allowedTags: [],
            ...options
        };
    }
    
    start() {
        if (this.isActive) return;
        this.isActive = true;
        this.createSelectorElement();
        this.createHighlightElement();
        this.bindEscapeKey();
    }
    
    stop() {
        if (!this.isActive) return;
        this.isActive = false;
        this.removeSelectorElement();
        this.removeHighlightElement();
        this.unbindEscapeKey();
        if (this.options.onClose) {
            this.options.onClose();
        }
    }
    
    shouldIgnoreElement(element) {
        if (!element) return true;
        
        const tag = element.tagName.toLowerCase();
        
        // 检查是否在允许的元素列表中（只匹配标签名）
        if (this.options.allowedElements && this.options.allowedElements.length > 0) {
            const isAllowed = this.options.allowedElements.some(allowed => {
                // 如果allowed是字符串，直接比较标签名
                if (typeof allowed === 'string') {
                    return tag === allowed.toLowerCase();
                }
                // 如果allowed是对象，检查tagName属性
                if (allowed.tagName) {
                    return tag === allowed.tagName.toLowerCase();
                }
                return false;
            });
            
            if (!isAllowed) {
                console.log(`元素 ${tag} 不在允许列表中:`, this.options.allowedElements);
                return true;
            }
        }
        
        // 检查允许的标签
        if (this.options.allowedTags && this.options.allowedTags.length > 0) {
            const tag = element.tagName.toLowerCase();
            if (!this.options.allowedTags.includes(tag)) {
                return true;
            }
        }
        
        // 检查忽略的选择器
        const ignoreSelectors = this.options.ignoreSelectors || [];
        return ignoreSelectors.some(selector => {
            if (selector.startsWith('.')) {
                return element.classList.contains(selector.substring(1));
            }
            if (selector.startsWith('#')) {
                return element.id === selector.substring(1);
            }
            return element.matches(selector);
        });
    }
    
    createSelectorElement() {
        if (this.selectorEl) return;
        
        const selectorEl = document.createElement('div');
        selectorEl.className = 'sw-selector';
        Object.assign(selectorEl.style, {
            position: 'fixed',
            inset: '0',
            width: '100vw',
            height: '100vh',
            backgroundColor: 'rgba(0, 0, 0, 0.01)',
            zIndex: String(MAX_Z_INDEX),
            cursor: 'crosshair',
            pointerEvents: 'auto'
        });
        
        selectorEl.addEventListener('mousemove', this.handleMouseMove);
        selectorEl.addEventListener('mouseleave', this.handleMouseLeave);
        selectorEl.addEventListener('click', this.handleMouseClick);
        document.body.appendChild(selectorEl);
        this.selectorEl = selectorEl;
    }
    
    createHighlightElement() {
        if (this.highlightEl) return;
        
        const highlightEl = document.createElement('div');
        highlightEl.className = 'sw-highlight';
        Object.assign(highlightEl.style, {
            position: 'fixed',
            display: 'none',
            pointerEvents: 'none',
            border: '2px solid #0079d3',
            backgroundColor: 'rgba(0, 121, 211, 0.1)',
            zIndex: String(MAX_Z_INDEX - 1)
        });
        document.body.appendChild(highlightEl);
        this.highlightEl = highlightEl;
    }
    
    removeSelectorElement() {
        if (!this.selectorEl) return;
        
        this.selectorEl.removeEventListener('mousemove', this.handleMouseMove);
        this.selectorEl.removeEventListener('mouseleave', this.handleMouseLeave);
        this.selectorEl.removeEventListener('click', this.handleMouseClick);
        document.body.removeChild(this.selectorEl);
        this.selectorEl = null;
    }
    
    removeHighlightElement() {
        if (!this.highlightEl) return;
        
        document.body.removeChild(this.highlightEl);
        this.highlightEl = null;
        this.lastHoveredElement = null;
    }
    
    bindEscapeKey() {
        document.addEventListener('keydown', this.handleKeyDown);
    }
    
    unbindEscapeKey() {
        document.removeEventListener('keydown', this.handleKeyDown);
    }
    
    updateHighlight(element) {
        if (!this.highlightEl || !element) return;
        
        const rect = element.getBoundingClientRect();
        const tagName = element.tagName.toLowerCase();
        
        // 判断元素类型并设置相应的颜色
        let borderColor, backgroundColor;
        
        // 检查是否是当前章节的元素
        const isCurrentElement = this.currentElements.includes(tagName);
        // 检查是否是之前章节的元素
        const isPreviousElement = this.cumulativeElements.includes(tagName) && !isCurrentElement;
        
        if (isCurrentElement) {
            // 当前章节元素 - 蓝色
            borderColor = '#0079d3';
            backgroundColor = 'rgba(0, 121, 211, 0.1)';
        } else if (isPreviousElement) {
            // 之前章节元素 - 红色
            borderColor = '#dc3545';
            backgroundColor = 'rgba(220, 53, 69, 0.1)';
        } else {
            // 默认颜色
            borderColor = '#0079d3';
            backgroundColor = 'rgba(0, 121, 211, 0.1)';
        }
        
        Object.assign(this.highlightEl.style, {
            display: 'block',
            left: `${rect.left}px`,
            top: `${rect.top}px`,
            width: `${rect.width}px`,
            height: `${rect.height}px`,
            border: `2px solid ${borderColor}`,
            backgroundColor: backgroundColor
        });
    }
    
    hideHighlight() {
        if (!this.highlightEl) return;
        this.highlightEl.style.display = 'none';
    }
}

// ==================== API工具函数 ====================
import { buildBackendUrl } from './config.js';

async function loadAllowedElementsFromAPI(topicId) {
    try {
        console.log(`[SelectModules] 开始加载章节 ${topicId} 的可选元素数据`);
        
        // 使用导入的buildBackendUrl函数
        const apiUrl = buildBackendUrl(`/learning-content/${topicId}`);
        console.log(`[SelectModules] API请求地址: ${apiUrl}`);
        
        const response = await fetch(apiUrl);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        
        console.log(`[SelectModules] 后端返回的原始数据:`, result);
        
        if (result.code === 200 && result.data) {
            const data = result.data;
            console.log(`[SelectModules] 解析后的数据:`, data);
            
            const allowedElements = getAllowedElementsFromData(data, topicId);
            console.log(`[SelectModules] 提取的可选元素:`, allowedElements);
            
            return allowedElements;
        }
        
        console.warn(`[SelectModules] API返回码不是200或没有数据:`, result);
        
        // 如果没有找到任何数据，返回空对象
        return {
            cumulative: [],
            current: []
        };
    } catch (error) {
        console.error('[SelectModules] Failed to load allowed elements:', error);
        return {
            cumulative: [],
            current: []
        };
    }
}

function getCumulativeAllowedElements(scAll, targetTopicId) {
    const allowedElements = new Set();
    
    // 遍历所有章节
    for (const chapter of scAll) {
        const chapterTopicId = chapter.topic_id;
        const selectElements = chapter.select_element || [];
        
        // 将当前章节的可选元素添加到集合中
        selectElements.forEach(element => allowedElements.add(element));
        
        // 如果找到目标章节，停止累加
        if (chapterTopicId === targetTopicId) {
            break;
        }
    }
    
    return Array.from(allowedElements);
}

function getCurrentChapterElements(scAll, targetTopicId) {
    // 找到当前章节
    const currentChapter = scAll.find(chapter => chapter.topic_id === targetTopicId);
    
    if (currentChapter && currentChapter.select_element) {
        return currentChapter.select_element;
    }
    
    return [];
}

function getAllowedElementsFromData(data, topicId) {
    console.log(`[SelectModules] 开始解析数据，目标章节: ${topicId}`);
    console.log(`[SelectModules] 数据中是否包含 sc_all:`, !!data.sc_all);
    console.log(`[SelectModules] 数据中是否包含 allowedElements:`, !!data.allowedElements);
    
    if (data.sc_all && Array.isArray(data.sc_all)) {
        console.log(`[SelectModules] 找到 sc_all 数组，长度: ${data.sc_all.length}`);
        console.log(`[SelectModules] sc_all 内容:`, data.sc_all);
        
        const cumulativeElements = getCumulativeAllowedElements(data.sc_all, topicId);
        const currentElements = getCurrentChapterElements(data.sc_all, topicId);
        
        console.log(`[SelectModules] 累积元素:`, cumulativeElements);
        console.log(`[SelectModules] 当前章节元素:`, currentElements);
        
        return {
            cumulative: cumulativeElements,
            current: currentElements
        };
    }
    
    // 如果直接包含 allowedElements
    if (data.allowedElements) {
        console.log(`[SelectModules] 使用直接包含的 allowedElements:`, data.allowedElements);
        return {
            cumulative: data.allowedElements,
            current: data.allowedElements
        };
    }
    
    console.warn(`[SelectModules] 未找到有效的元素数据，返回空数组`);
    return {
        cumulative: [],
        current: []
    };
}

// ==================== iframe桥接 ====================
const MESSAGE_TYPES = {
    START: 'SW_SELECT_START',
    STOP: 'SW_SELECT_STOP',
    CHOSEN: 'SW_SELECT_CHOSEN',
};

function initIframeSelector(options = {}) {
    const { allowed = true, allowedOrigins = ['*'], allowedTags = [] } = options;
    if (!allowed) return () => {};
    
    let selector = null;
    const handleMessage = (event) => {
        if (allowedOrigins[0] !== '*' && !allowedOrigins.includes(event.origin)) return;
        
        let message;
        try {
            message = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
        } catch (e) { return; }
        
        switch (message.type) {
            case MESSAGE_TYPES.START:
                if (selector) {
                    selector.stop();
                }
                const startMessage = message;
                // 解析allowedElements，区分当前章节和累积章节的元素
                const allowedElements = startMessage.allowedElements || [];
                let currentElements = [];
                let cumulativeElements = [];
                
                // 如果allowedElements是对象格式（包含current和cumulative）
                if (typeof allowedElements === 'object' && !Array.isArray(allowedElements)) {
                    currentElements = allowedElements.current || [];
                    cumulativeElements = allowedElements.cumulative || [];
                } else {
                    // 如果allowedElements是数组格式，全部作为累积元素
                    cumulativeElements = allowedElements;
                }
                
                console.log('iframe选择器接收到消息:', {
                    allowedElements: startMessage.allowedElements,
                    currentElements: currentElements,
                    cumulativeElements: cumulativeElements
                });
                
                selector = new ElementSelector({
                    ignoreSelectors: startMessage.ignore,
                    allowedTags: startMessage.allowedTags || allowedTags,
                    allowedElements: cumulativeElements, // 使用累积元素作为允许的元素
                    currentElements: currentElements, // 当前章节元素
                    cumulativeElements: cumulativeElements, // 累积元素
                    onElementSelected: (element, info) => {
                        try {
                            if (window.parent && window.parent.postMessage) {
                                window.parent.postMessage({
                                    type: MESSAGE_TYPES.CHOSEN,
                                    payload: info
                                }, '*');
                            } else {
                                console.warn('无法发送postMessage到父窗口');
                            }
                        } catch (error) {
                            console.error('发送postMessage失败:', error);
                        }
                    }
                });
                selector.start();
                break;
            case MESSAGE_TYPES.STOP:
                if (selector) {
                    selector.stop();
                    selector = null;
                }
                break;
        }
    };
    
    window.addEventListener('message', handleMessage);
    return () => {
        window.removeEventListener('message', handleMessage);
        if (selector) {
            selector.stop();
            selector = null;
        }
    };
}

function createSelectorBridge(options) {
    const { iframeWindow, targetOrigin = '*', ignoreSelectors = ['.sw-selector', '.sw-highlight'], onChosen, onError } = options;
    
    if (!iframeWindow) throw new Error('Invalid iframe window');
    
    const handleMessage = (event) => {
        let message;
        try {
            message = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
        } catch (e) { return; }
        
        if (message.type === MESSAGE_TYPES.CHOSEN && onChosen) {
            const chosenMessage = message;
            onChosen(chosenMessage.payload);
        }
    };
    
    window.addEventListener('message', handleMessage);
    
    return {
        start(allowedTags = [], allowedElements = []) {
            try {
                // 检查iframe是否准备就绪
                if (!iframeWindow || !iframeWindow.postMessage) {
                    console.warn('iframe window未准备就绪，无法发送消息');
                    if (onError) {
                        onError(new Error('iframe window未准备就绪'));
                    }
                    return;
                }
                
                // 确保传递正确的元素信息
                let elementsToSend = allowedElements;
                
                // 如果allowedElements是对象格式，直接传递
                if (typeof allowedElements === 'object' && !Array.isArray(allowedElements)) {
                    elementsToSend = allowedElements;
                } else {
                    // 如果是数组格式，转换为对象格式
                    elementsToSend = {
                        current: allowedElements,
                        cumulative: allowedElements
                    };
                }
                
                const message = {
                    type: MESSAGE_TYPES.START,
                    ignore: ignoreSelectors,
                    allowedTags,
                    allowedElements: elementsToSend
                };
                
                // 使用try-catch包装postMessage调用
                try {
                    iframeWindow.postMessage(message, targetOrigin);
                } catch (postMessageError) {
                    console.warn('postMessage发送失败:', postMessageError);
                    if (onError) {
                        onError(postMessageError instanceof Error ? postMessageError : new Error(String(postMessageError)));
                    }
                }
            } catch (error) {
                console.error('启动选择器失败:', error);
                if (onError) {
                    onError(error instanceof Error ? error : new Error(String(error)));
                }
            }
        },
        
        stop() {
            try {
                // 检查iframe是否准备就绪
                if (!iframeWindow || !iframeWindow.postMessage) {
                    console.warn('iframe window未准备就绪，无法发送停止消息');
                    return;
                }
                
                const message = {
                    type: MESSAGE_TYPES.STOP
                };
                
                // 使用try-catch包装postMessage调用
                try {
                    iframeWindow.postMessage(message, targetOrigin);
                } catch (postMessageError) {
                    console.warn('postMessage停止消息发送失败:', postMessageError);
                }
            } catch (error) {
                console.error('停止选择器失败:', error);
                if (onError) {
                    onError(error instanceof Error ? error : new Error(String(error)));
                }
            }
        },
        
        destroy() {
            window.removeEventListener('message', handleMessage);
        }
    };
}

// 导出模块
window.SelectModules = {
    getElementAtPoint,
    isElementAtPoint,
    getElementXPath,
    getElementInfo,
    ElementSelector,
    initIframeSelector,
    createSelectorBridge,
    loadAllowedElementsFromAPI,
    getCumulativeAllowedElements,
    getCurrentChapterElements,
    getAllowedElementsFromData,
    MESSAGE_TYPES
};

// 自动初始化 - 在iframe页面中启用
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initIframeSelector();
    });
} else {
    initIframeSelector();
}