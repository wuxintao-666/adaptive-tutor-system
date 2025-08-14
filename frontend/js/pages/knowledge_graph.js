// knowledgeGraph.js - 主模块（协调其他模块）
import { getParticipantId } from '../modules/session.js';
import { GraphState } from '../modules/graph_data.js';
import { GraphRenderer } from '../modules/graph_renderer.js';


// 初始化应用
document.addEventListener('DOMContentLoaded',async () => {
  try {
    // 获取用户ID并验证
   /*  const participantId = getParticipantId();
    if (!participantId) {
      window.location.href = '/index.html';
      return;
    } */

    // 并行获取图谱数据和用户进度
    const [graphResponse] = await Promise.all([
      // 请求知识图谱数据
      fetch('/api/v1/knowledge-graph'),
      // 请求进度数据
      /* fetch(`/api/v1/participants/${participantId}/progress`) */
    ]);

    // 检查响应状态
    if (!graphResponse.ok) {
      throw new Error('获取数据失败');
    }

    // 解析JSON数据
    const [graphResult] = await Promise.all([
      graphResponse.json(),
      /* progressResponse.json() */
    ]);
    // 查看后端返回数据格式
    console('知识图谱数据:', graphResult);
    // 查看后端返回数据格式
    /* console('初始化状态失败:', progressResult); */
    // 处理数据
 /*    const graphData = graphResult.data;
    const learnedNodes = progressResult.data.completed_topics || []; */
    // 测试用数据
    const graphData = {
      nodes: [
        { data: { id: "chapter1", label: "模块一: 页面结构基础", type: "chapter" } },
        { data: { id: "text_paragraph", label: "使用h元素和p元素体验标题与段落", type: "knowledge" } },
        { data: { id: "text_format", label: "应用文本格式(加粗、斜体)", type: "knowledge" } },
        { data: { id: "structure_header", label: "构建页面头部结构", type: "knowledge" } },

        { data: { id: "chapter2", label: "模块二: 盒子与列表使用", type: "chapter" } },
        { data: { id: "structure_div", label: "使用盒子元素进行内容划分", type: "knowledge" } },
        { data: { id: "text_list_ol", label: "创建有序列表", type: "knowledge" } },
        { data: { id: "text_list_ul", label: "创建无序列表", type: "knowledge" } },

        { data: { id: "chapter3", label: "模块三: 表单与交互控件", type: "chapter" } },
        { data: { id: "form_input", label: "文本框与按钮的使用", type: "knowledge" } },
        { data: { id: "form_checkbox", label: "复选框与单选框", type: "knowledge" } },
        { data: { id: "form_submit", label: "表单提交机制", type: "knowledge" } }
      ],
      edges: [
        { data: { source: "chapter1", target: "chapter2" } },
        { data: { source: "chapter2", target: "chapter3" } },

        { data: { source: "chapter1", target: "text_paragraph" } },
        { data: { source: "chapter1", target: "text_format" } },
        { data: { source: "chapter1", target: "structure_header" } },

        { data: { source: "chapter2", target: "structure_div" } },
        { data: { source: "chapter2", target: "text_list_ol" } },
        { data: { source: "chapter2", target: "text_list_ul" } },

        { data: { source: "chapter3", target: "form_input" } },
        { data: { source: "chapter3", target: "form_checkbox" } },
        { data: { source: "chapter3", target: "form_submit" } }
      ],
      dependent_edges: [
        { data: { source: "chapter1", target: "chapter2" } },
        { data: { source: "chapter2", target: "chapter3" } },

        { data: { source: "chapter1", target: "text_paragraph" } },
        { data: { source: "text_paragraph", target: "text_format" } },
        { data: { source: "text_format", target: "structure_header" } },

        { data: { source: "chapter2", target: "structure_div" } },
        { data: { source: "structure_div", target: "text_list_ol" } },
        { data: { source: "text_list_ol", target: "text_list_ul" } },

        { data: { source: "chapter3", target: "form_input" } },
        { data: { source: "form_input", target: "form_checkbox" } },
        { data: { source: "form_checkbox", target: "form_submit" } }
      ]
    };
    const learnedNodes = ["chapter1","text_paragraph"];// 测试用数据

    // 验证数据格式
    if (!graphData || !graphData.nodes || !graphData.edges) {
      throw new Error('图谱数据格式不正确');
    }

    // 初始化状态管理
    const graphState = new GraphState(graphData, learnedNodes);
    try {
      graphState.initMaps();
    } catch (error) {
      console.error('初始化状态失败:', error);
      throw new Error('初始化知识图谱状态失败');
    }
    
    // 初始化渲染器
    const graphRenderer = new GraphRenderer('cy', graphState);
    graphRenderer.addElements([...graphData.nodes, ...graphData.edges]);
    
    // 设置初始布局
    graphRenderer.setFixedChapterPositions();
    graphRenderer.hideAllKnowledgeNodes();
    graphRenderer.updateNodeColors();
    
    // 初始居中
    setTimeout(() => graphRenderer.centerAndZoomGraph(), 100);

    // 设置窗口大小变化监听
    window.addEventListener('resize', () => {
      setTimeout(() => graphRenderer.centerAndZoomGraph(), 100);
    });
    // 窗口点击事件处理
    window.onclick = (event) => {
      const modal = document.getElementById('knowledgeModal');
      if (event.target === modal) modal.style.display = 'none';
    };
    // 显示知识点弹窗
    function showKnowledgeModal(knowledgeId, nodeLabel) {
      const modal = document.getElementById('knowledgeModal');
      const title = document.getElementById('modalTitle');
      const status = document.getElementById('modalStatus');
      const learnBtn = document.getElementById('learnBtn');
      const testBtn = document.getElementById('testBtn');
      
      title.textContent = nodeLabel || knowledgeId;
      learnBtn.className = 'learn-btn';
      learnBtn.disabled = false;
      learnBtn.textContent = '学习';
      testBtn.className = 'test-btn';
      
      if (graphState.learnedNodes.includes(knowledgeId)) {
        status.textContent = '您已学过该知识点，是否再次复习或重新测试？';
        learnBtn.textContent = '复习';
        learnBtn.className = 'review-btn';
        
        learnBtn.onclick = () => {
          window.location.href = `/pages//learning_page.html?node=${knowledgeId}`;
        };
        
        testBtn.onclick = () => {
          window.location.href = `/pages//test_page.html?chapter=${knowledgeId}`;
        };
      } else if (graphState.isKnowledgeUnlocked(knowledgeId)) {
        status.textContent = '您可以开始学习该知识点或直接进行测试';
        
        learnBtn.onclick = () => {
          window.location.href = `/pages/learning_page.html?node=${knowledgeId}`;
        };
        
        testBtn.onclick = () => {
          window.location.href = `/pages/test_page.html?chapter=${knowledgeId}`;
        };
      } else {
        status.textContent = '该知识点尚未解锁，您是否要直接开始测试？';
        learnBtn.disabled = true;
        learnBtn.className += ' disabled';
        
        learnBtn.onclick = () => {};
        testBtn.onclick = () => {
          window.location.href = `/pages/test_page.html?chapter=${knowledgeId}`;
        };
      }
      modal.style.display = 'block';
    }
    
    // 单击/双击处理
    const clickState = { lastId: null, timer: null, ts: 0 };
    const DBL_DELAY = 280;
    
    graphRenderer.cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const id = node.id();
      const now = Date.now();
      
      if (clickState.lastId === id && (now - clickState.ts) < DBL_DELAY) {
        clearTimeout(clickState.timer);
        clickState.timer = null;
        clickState.lastId = null;
        handleDoubleClick(node);
      } else {
        clickState.lastId = id;
        clickState.ts = now;
        clickState.timer = setTimeout(() => {
          handleSingleClick(node);
          clickState.timer = null;
          clickState.lastId = null;
        }, DBL_DELAY);
      }
    });
        // 单击处理
    function handleSingleClick(node) {
      const id = node.id();
      const type = node.data('type');
      
      if (type === 'chapter') {
        if (graphState.expandedSet.has(id)) {
          graphRenderer.collapseChapter(id);
        } else {
          graphRenderer.expandChapter(id);
        }
        
        if (graphState.currentLearningChapter === null && id === 'chapter1' && 
            !graphState.learnedNodes.includes(id)) {
          graphState.currentLearningChapter = id;
        }
        
        graphRenderer.updateNodeColors();
        return;
      }
      
      if (type === 'knowledge') {
        const label = node.data('label') || id;
        if (graphState.learnedNodes.includes(id)) {// 已学知识点
          showKnowledgeModal(id, label);
        } else if (graphState.isKnowledgeUnlocked(id)) {// 可学知识点
          showKnowledgeModal(id, label);
        } else {// 未解锁知识点
          if (confirm("您还未学习前置知识点，是否直接开始测试？")) {
            window.location.href = `/pages/test_page.html?node=${id}`;
          }
        }
      }
    }
    
    // 双击处理
    function handleDoubleClick(node) {
      const id = node.id();
      const type = node.data('type');
      
      if (type === 'chapter') {
        if (graphState.isChapterCompleted(id)) {
          if (confirm("您已学过本章节，是否再次进行测试？")) {
            window.location.href = `/pages/test_page.html?chapter=${id}`;
          }
        } else if (graphState.currentLearningChapter === id) {
          if (confirm("您还未学完当前章节内容，是否直接开始测试？")) {
            window.location.href = `/pages/test_page.html?chapter=${id}`;
          }
        } else {
          if (confirm("您还未解锁前置章节，是否直接开始测试？")) {
            window.location.href = `/pages/test_page.html?chapter=${id}`;
          }
        }
        
        graphState.passChapterTest(id);
        graphRenderer.updateNodeColors();
      }
    }
  } catch (error) {
    console.error('初始化知识图谱失败:', error);
    alert('加载知识图谱失败，请刷新页面重试');
  }

});