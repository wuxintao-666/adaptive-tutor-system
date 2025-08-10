
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
        
        this.handleMouseMove = (event) => {
            requestAnimationFrame(() => {
                if (this.highlightEl && this.highlightEl.style.display !== 'none') {
                    this.highlightEl.style.display = 'none';
                }
                
                const refElement = getElementAtPoint(event.clientX, event.clientY);
                if (!refElement || this.shouldIgnoreElement(refElement)) {
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
        
        // 检查是否在允许的元素列表中（只匹配标签名）
        if (this.options.allowedElements && this.options.allowedElements.length > 0) {
            const tag = element.tagName.toLowerCase();
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
        Object.assign(this.highlightEl.style, {
            display: 'block',
            left: `${rect.left}px`,
            top: `${rect.top}px`,
            width: `${rect.width}px`,
            height: `${rect.height}px`
        });
    }
    
    hideHighlight() {
        if (!this.highlightEl) return;
        this.highlightEl.style.display = 'none';
    }
}

// ==================== API工具函数 ====================
async function loadAllowedElementsFromAPI(topicId, baseURL = '/api') {
    try {
        const response = await fetch(`${baseURL}/content/learning-content/${topicId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        
        if (result.success && result.data) {
            const data = result.data;
            return getAllowedElementsFromData(data, topicId);
        }
        
        // 如果没有找到任何数据，返回空对象
        return {
            cumulative: [],
            current: []
        };
    } catch (error) {
        console.error('Failed to load allowed elements:', error);
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
    if (data.sc_all && Array.isArray(data.sc_all)) {
        const cumulativeElements = getCumulativeAllowedElements(data.sc_all, topicId);
        const currentElements = getCurrentChapterElements(data.sc_all, topicId);
        
        return {
            cumulative: cumulativeElements,
            current: currentElements
        };
    }
    
    // 如果直接包含 allowedElements
    if (data.allowedElements) {
        return {
            cumulative: data.allowedElements,
            current: data.allowedElements
        };
    }
    
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
                selector = new ElementSelector({
                    ignoreSelectors: startMessage.ignore,
                    allowedTags: startMessage.allowedTags || allowedTags,
                    allowedElements: startMessage.allowedElements || [],
                    onElementSelected: (element, info) => {
                        window.parent.postMessage({
                            type: MESSAGE_TYPES.CHOSEN,
                            payload: info
                        }, '*');
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
                iframeWindow.postMessage({
                    type: MESSAGE_TYPES.START,
                    ignore: ignoreSelectors,
                    allowedTags,
                    allowedElements
                }, targetOrigin);
            } catch (error) {
                if (onError) {
                    onError(error instanceof Error ? error : new Error(String(error)));
                }
            }
        },
        
        stop() {
            try {
                iframeWindow.postMessage({
                    type: MESSAGE_TYPES.STOP
                }, targetOrigin);
            } catch (error) {
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
