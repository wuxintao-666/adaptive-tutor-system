/* ============================
   graph_renderer.js
   功能：
   - 初始化 Cytoscape
   - 固定章节位置
   - 布局知识点
   - 随窗口调整中心和缩放
   ============================ */
// graphRenderer.js - 图谱渲染与布局

import { LAYOUT_PARAMS } from './graph_data.js';

// 图谱渲染类
export class GraphRenderer {
  constructor(containerId, graphState) {
    this.cy = cytoscape({
      container: document.getElementById(containerId),
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'color': '#000',
            'background-color': '#ddd',
            'width': 120,
            'height': 120,
            'font-size': 14,
            'text-wrap': 'wrap',
            'text-max-width': '100px',
            'shape': 'ellipse'
          }
        },
        {
          selector: 'node[type="chapter"]',
          style: {
            'shape': 'roundrectangle',
            'font-weight': 'bold'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#bbb',
            'target-arrow-shape': 'triangle',
            'target-arrow-color': '#bbb',
            'curve-style': 'bezier'
          }
        }
      ],
      layout: { name: 'preset' }
    });
    
    this.graphState = graphState;
    this.layoutParams = LAYOUT_PARAMS;
  }

  // 添加元素到图谱
  addElements(elements) {
    this.cy.add(elements);
  }

  // 设置章节固定位置
  setFixedChapterPositions() {
    const chapters = this.cy.nodes().filter(n => n.data('type') === 'chapter')
      .sort((a, b) => {
        const ai = parseInt(a.id().replace('chapter', '')) || 0;
        const bi = parseInt(b.id().replace('chapter', '')) || 0;
        return ai - bi;
      });

    chapters.forEach((node, idx) => {
      const x = this.layoutParams.CHAPTER_START_X + idx * this.layoutParams.CHAPTER_GAP_X;
      const y = (idx % 2 === 0) ? this.layoutParams.TOP_ROW_Y : (this.layoutParams.TOP_ROW_Y + this.layoutParams.ROW_DELTA_Y);
      node.position({ x, y });
      node.lock();
      this.graphState.fixedPositions[node.id()] = { x, y };
    });
  }

  // 确保知识点位置
  ensurePositionsForChapterKnowledge(chapterId) {
    const sampleKids = this.graphState.collectKnowledgeDescendantsForDisplay(chapterId);
    if (!sampleKids || sampleKids.length === 0) return;
    
    const anySet = sampleKids.some(id => this.graphState.fixedPositions[id]);
    if (anySet) return;

    const chapterPos = this.graphState.fixedPositions[chapterId] || this.cy.getElementById(chapterId).position();
    const chapterY = chapterPos.y;
    const isChapterTop = (Math.abs(chapterY - this.layoutParams.KNOWLEDGE_TOP_ROW_Y) < 
                         Math.abs(chapterY - (this.layoutParams.KNOWLEDGE_TOP_ROW_Y + this.layoutParams.KNOWLEDGE_ROW_DELTA_Y)));
    
    const targetY = isChapterTop ? 
      (this.layoutParams.KNOWLEDGE_TOP_ROW_Y + this.layoutParams.KNOWLEDGE_ROW_DELTA_Y) : 
      this.layoutParams.KNOWLEDGE_TOP_ROW_Y;

    const kids = this.graphState.collectKnowledgeDescendantsForDisplay(chapterId);
    const cx = chapterPos.x;
    const n = kids.length;
    const half = (n - 1) / 2;
    
    kids.forEach((id, i) => {
      const x = cx + (i - half) * this.layoutParams.KNOWLEDGE_GAP_X;
      this.graphState.fixedPositions[id] = { x, y: targetY };
    });
  }

  // 展开章节
  expandChapter(chapterId) {
    this.ensurePositionsForChapterKnowledge(chapterId);
    const kids = this.graphState.collectKnowledgeDescendantsForDisplay(chapterId);
    
    kids.forEach(id => {
      const node = this.cy.getElementById(id);
      if (node && node.length) {
        const pos = this.graphState.fixedPositions[id];
        if (pos) node.position(pos);
        node.show();
      }
    });

    this.updateEdgesVisibility();
    this.graphState.expandedSet.add(chapterId);
    this.updateNodeColors();
  }

  // 收起章节
  collapseChapter(chapterId) {
    const kids = this.graphState.collectKnowledgeDescendantsForDisplay(chapterId);
    kids.forEach(id => {
      const node = this.cy.getElementById(id);
      if (node && node.length) node.hide();
    });
    
    this.updateEdgesVisibility();
    this.graphState.expandedSet.delete(chapterId);
    this.updateNodeColors();
  }

  // 更新边可见性
  updateEdgesVisibility() {
    this.cy.edges().forEach(e => {
      const s = e.data('source'), t = e.data('target');
      const sn = this.cy.getElementById(s), tn = this.cy.getElementById(t);
      if (sn && tn && sn.length && tn.length && sn.visible() && tn.visible()) e.show();
      else e.hide();
    });
  }

  // 更新节点颜色
  updateNodeColors() {
    this.cy.nodes().forEach(n => {
      const id = n.id();
      const type = n.data('type');

      if (type === 'chapter') {
        if (this.graphState.currentLearningChapter === id) {
          n.style('background-color', '#f1c40f'); // 黄色 - 正在学习
        } else if (this.graphState.isChapterCompleted(id)) {
          n.style('background-color', '#2ecc71'); // 绿色 - 已完成
        } else if (this.graphState.canLearnChapter(id)) {
          n.style('background-color', '#3498db'); // 蓝色 - 可学习
        } else {
          n.style('background-color', '#ddd'); // 灰色 - 未解锁
        }
      } else {
        if (this.graphState.learnedNodes.includes(id)) {
          n.style('background-color', '#2ecc71'); // 绿色 - 已完成
        } else if (this.graphState.isKnowledgeUnlocked(id)) {
          n.style('background-color', '#3498db'); // 蓝色 - 可学习
        } else {
          n.style('background-color', '#ddd'); // 灰色 - 未解锁
        }
      }
    });
  }

  // 隐藏所有知识点
  hideAllKnowledgeNodes() {
    this.cy.nodes().forEach(n => {
      if (n.data('type') === 'knowledge') n.hide();
    });
    this.updateEdgesVisibility();
  }

  // 居中缩放图谱
  centerAndZoomGraph() {
    const nodes = this.cy.nodes().filter(node => node.visible());
    if (nodes.length === 0) return;
    
    let minX = Infinity, maxX = -Infinity;
    let minY = Infinity, maxY = -Infinity;
    
    nodes.forEach(node => {
      const pos = node.position();
      minX = Math.min(minX, pos.x);
      maxX = Math.max(maxX, pos.x);
      minY = Math.min(minY, pos.y);
      maxY = Math.max(maxY, pos.y);
    });
    
    const margin = 100;
    minX -= margin;
    maxX += margin;
    minY -= margin;
    maxY += margin;
    
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    const width = maxX - minX;
    const height = maxY - minY;
    
    const containerWidth = this.cy.container().clientWidth;
    const containerHeight = this.cy.container().clientHeight;
    
    const scaleX = containerWidth / width;
    const scaleY = containerHeight / height;
    const scale = Math.min(scaleX, scaleY) * 0.9;
    
    const panX = -centerX * scale + containerWidth / 2;
    const panY = -centerY * scale + containerHeight / 2;
    
    this.cy.zoom(scale);
    this.cy.pan({ x: panX, y: panY });
  }
}