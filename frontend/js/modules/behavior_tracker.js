// frontend/js/modules/behavior_tracker.js
/**
 * BehaviorTracker 前端行为追踪模块
 *
 * 目标：
 * - 捕获 TDD-II-07 中规定的关键事件：
 *   code_edit（Monaco 编辑器防抖 2s）、ai_help_request（立即）、test_submission（立即，包含 code）、dom_element_select（立即，iframe 支持）、user_idle（60s）、page_focus_change（visibility）
 * - 组装标准化 payload 并可靠发送到后端 /api/v1/behavior/log
 * - 优先使用 navigator.sendBeacon；在不支持时 fallback 到 fetch(..., { keepalive: true })
 *
 * 注意：
 * - 本文件不修改现有 HTML。脚本提供自动初始化尝试（initAuto），但更可靠的方式是：在页面创建 Monaco 编辑器后显式调用 tracker.initEditors(...) 与 tracker.initTestActions(...)
 * - TODO中表示需要我们根据实际项目调整或确认的点（Monaco 编辑器实例的暴露方式等）
 */

import { debounce } from 'lodash-es';
import { getParticipantId } from './session.js';

class BehaviorTracker {
  constructor() {
    // 闲置阈值（ms）
    this.idleThreshold = 60000; // 60s
    // code_edit 防抖时长（ms）
    this.debounceMs = 2000;
    this.idleTimer = null;
  }

  // -------------------- 核心发送函数 --------------------
  // 优先使用 navigator.sendBeacon，否则使用 fetch keepalive（并在控制台打印错误）
  _sendPayload(payload) {
    const url = '/api/v1/behavior/log';
    try {
      if (navigator && typeof navigator.sendBeacon === 'function') {
        const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
        navigator.sendBeacon(url, blob);
      } else {
        // fallback: fetch keepalive（注意：并非所有浏览器都支持 keepalive）
        fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          keepalive: true
        }).catch(err => {
          console.warn('[BehaviorTracker] fetch fallback 发送失败：', err);
        });
      }
    } catch (e) {
      console.warn('[BehaviorTracker] 发送日志时异常：', e);
    }
  }

  // 公共上报接口：组装标准 payload 并发送
  logEvent(eventType, eventData = {}) {
    // 获取 participant_id（从 session.js 或 window 取）
    let participant_id = null;
    try {
      if (typeof getParticipantId === 'function') {
        participant_id = getParticipantId();
      }
    } catch (e) {
      // ignore
    }
    // 兜底：如果页面在全局暴露 participantId，也可取之
    if (!participant_id && window && window.participantId) {
      participant_id = window.participantId;
    }
    if (!participant_id) {
      // 如果没有 participant_id，则按 TDD-II-07 的说明不追踪；可选择缓冲但当前选择跳过
      console.warn('[BehaviorTracker] 无 participant_id，跳过事件：', eventType);
      return;
    }

    const payload = {
      participant_id,
      event_type: eventType,
      event_data: eventData,
      timestamp: new Date().toISOString()
    };

    this._sendPayload(payload);
  }

  // -------------------- 编辑器（Monaco）相关 --------------------
  // editors: { html: monacoEditorInstance, css: ..., js: ... }
  initEditors(editors) {
    if (!editors) return;

    // 防抖上报 code_edit
    const debouncedLog = debounce((name, code) => {
      this.logEvent('code_edit', {
        editorName: name,
        newLength: code ? code.length : 0,
        // TODO: 如果需要可加入 lineCount: editors[name].getModel().getLineCount()
      });
    }, this.debounceMs);

    try {
      if (editors.html && typeof editors.html.onDidChangeModelContent === 'function') {
        editors.html.onDidChangeModelContent(() => debouncedLog('html', editors.html.getValue()));
      }
      if (editors.css && typeof editors.css.onDidChangeModelContent === 'function') {
        editors.css.onDidChangeModelContent(() => debouncedLog('css', editors.css.getValue()));
      }
      if (editors.js && typeof editors.js.onDidChangeModelContent === 'function') {
        editors.js.onDidChangeModelContent(() => debouncedLog('js', editors.js.getValue()));
      }
    } catch (e) {
      console.warn('[BehaviorTracker] initEditors 错误：', e);
    }
  }

  // -------------------- AI 求助（聊天） --------------------
  // sendButtonId: 提问按钮 id；inputSelector: 文本输入选择器
  initChat(sendButtonId, inputSelector) {
    const btn = document.getElementById(sendButtonId);
    const input = document.querySelector(inputSelector);
    if (!btn || !input) return;
    btn.addEventListener('click', () => {
      const message = input.value || '';
      if (!message.trim()) return;
      this.logEvent('ai_help_request', { message: message.substring(0, 2000) });
    });
    // TODO: 如果希望支持 Enter 提交，可在此处绑定 keydown 事件
  }

  // -------------------- 测试/提交（包含 code） --------------------
  // runBtnId / submitBtnId: 按钮 id；editors: 同 initEditors；topicIdGetter: 可选函数返回 topic_id
  initTestActions(runBtnId, submitBtnId, editors, topicIdGetter) {
    const gatherCode = () => {
      const code = {};
      if (editors?.html && typeof editors.html.getValue === 'function') code.html = editors.html.getValue();
      if (editors?.css && typeof editors.css.getValue === 'function') code.css = editors.css.getValue();
      if (editors?.js && typeof editors.js.getValue === 'function') code.js = editors.js.getValue();
      return code;
    };

    const runBtn = document.getElementById(runBtnId);
    const subBtn = document.getElementById(submitBtnId);

    if (runBtn) {
      runBtn.addEventListener('click', () => {
        this.logEvent('test_submission', {
          action: 'run',
          topic_id: (typeof topicIdGetter === 'function' ? topicIdGetter() : window.currentTopicId) || null,
          code: gatherCode()
        });
      });
    }

    if (subBtn) {
      subBtn.addEventListener('click', () => {
        this.logEvent('test_submission', {
          action: 'submit',
          topic_id: (typeof topicIdGetter === 'function' ? topicIdGetter() : window.currentTopicId) || null,
          code: gatherCode()
        });
      });
    }
  }

  // -------------------- 元素选择（iframe 支持） --------------------
  // startBtnId / stopBtnId / iframeId
  initDOMSelector(startBtnId, stopBtnId, iframeId) {
    const startBtn = document.getElementById(startBtnId);
    const stopBtn = document.getElementById(stopBtnId);
    const iframe = document.getElementById(iframeId);
    if (!startBtn || !stopBtn || !iframe) return;

    let selecting = false;

    // 点击选择处理器（在 iframe 的 document 上绑定）
    const handler = (e) => {
      const tgt = e.target;
      if (!tgt) return;
      const selector = this._generateCssSelector(tgt);
      this.logEvent('dom_element_select', {
        tagName: tgt.tagName,
        selector,
        position: { x: e.clientX, y: e.clientY }
      });
      // TODO: 可在 iframe 中高亮元素或显示 tooltip，当前只上报事件
    };

    startBtn.addEventListener('click', () => {
      if (selecting) return;
      selecting = true;
      try {
        // 仅在同源 iframe 下可直接访问 contentWindow.document
        iframe.contentWindow.document.addEventListener('click', handler);
      } catch (err) {
        // 跨域 iframe 无法直接访问 -> 需要在 iframe 内实现 postMessage 协作
        console.warn('[BehaviorTracker] 无法访问 iframe document（可能跨域）。若需要选择，请实现 postMessage 协作。');
        // TODO: ceq如果页面存在跨域 iframe，则需要实现 postMessage 协作协议
      }
    });

    stopBtn.addEventListener('click', () => {
      if (!selecting) return;
      selecting = false;
      try {
        iframe.contentWindow.document.removeEventListener('click', handler);
      } catch (err) {
        // ignore
      }
    });
  }

  // -------------------- 闲置与焦点检测 --------------------
  initIdleAndFocus(idleMs) {
    const idleThreshold = typeof idleMs === 'number' ? idleMs : this.idleThreshold;

    const resetIdle = () => {
      clearTimeout(this.idleTimer);
      this.idleTimer = setTimeout(() => {
        this.logEvent('user_idle', { duration_ms: idleThreshold });
      }, idleThreshold);
    };

    ['mousemove', 'keydown', 'scroll', 'click'].forEach(evt => {
      document.addEventListener(evt, resetIdle, { passive: true });
    });

    document.addEventListener('visibilitychange', () => {
      const status = document.hidden ? 'blur' : 'focus';
      this.logEvent('page_focus_change', { status });
      if (status === 'focus') resetIdle();
    });

    // 启动初始计时
    resetIdle();
  }

  // -------------------- 辅助：生成 CSS Selector --------------------
  _generateCssSelector(el) {
    if (!el) return '';
    const parts = [];
    while (el && el.nodeType === Node.ELEMENT_NODE) {
      let part = el.nodeName.toLowerCase();
      if (el.id) {
        part += `#${el.id}`;
        parts.unshift(part);
        break;
      } else {
        let i = 1;
        let sib = el;
        while ((sib = sib.previousElementSibling) != null) {
          if (sib.nodeName.toLowerCase() === part) i++;
        }
        if (i > 1) part += `:nth-of-type(${i})`;
      }
      parts.unshift(part);
      el = el.parentElement;
    }
    return parts.join(' > ');
  }

  //TODO：ceq热力图内容的采集，目前决定和行为日志放在一起，产生较大单条日志可能考虑独立迁移。
  /* ============= 热力图（Heatmap）采集模块 =============
   - 支持按 page_id 分页统计（优先 document.body.dataset.pageId -> window.pageId -> location.pathname）
   - 点击（click）采集：记录坐标并聚合到网格单元
   - 停留（dwell）采集：基于定时采样（samplingIntervalMs），统计 samples -> 可转换为 ms
   - 数据持久化：保存在 localStorage（key: heatmap_data_v1），并支持周期性发送为 'heatmap_snapshot' 事件
    ================================================== */
  // 采样鼠标位置以估计停留时间（每次采样把 samples++，可转换为 dwell_ms）
  _sampleMousePosition() { }
  // 处理点击事件，记录到 heatmapData
  _onHeatmapClick(e) { }


  // -------------------- 自动初始化：尝试识别页面并注册监听 --------------------
  // 如果你希望更强控制，请在页面主动调用 tracker.initEditors(...) 等方法
  initAuto() {
    document.addEventListener('DOMContentLoaded', () => {
      // 编辑器页面检测：根据 DOM 中是否存在 id=monaco-editor 来识别
      const monacoContainer = document.getElementById('monaco-editor');
      if (monacoContainer && window.monaco && window.editors) {
        // 如果页面在全局把编辑器实例放到了 window.editors（推荐），直接取用
        try {
          const editors = window.editors || {};
          this.initEditors(editors);
          this.initChat('send-message', '#user-message');
          this.initTestActions('run-button', 'reset-button', editors, () => window.currentTopicId || null);
          this.initIdleAndFocus();
        } catch (e) {
          console.warn('[BehaviorTracker] 编辑器自动初始化失败，请在页面主动调用 tracker.initEditors(...)', e);
        }
        return;
      }

      // 元素选择页面检测
      const iframe = document.getElementById('element-selector-iframe');
      if (iframe) {
        this.initDOMSelector('startSelector', 'stopSelector', 'element-selector-iframe');
        this.initChat('send-message', '#user-message');
        this.initIdleAndFocus();
      }
    });
  }
}

// 导出单例并自动运行 initAuto 以便不改动 HTML 的情况下生效
const tracker = new BehaviorTracker();
export default tracker;
try {
  tracker.initAuto();
} catch (err) {
  console.warn('[BehaviorTracker] initAuto error', err);
}
