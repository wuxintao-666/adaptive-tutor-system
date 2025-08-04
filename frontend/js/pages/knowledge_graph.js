// frontend/js/pages/knowledge_graph.js
import { getParticipantId } from '../modules/session.js';
import { renderGraph, setupGraphInteractions } from '../modules/graph_renderer.js';
import { processGraphData } from '../modules/graph_logic.js';

document.addEventListener('DOMContentLoaded', async () => {
  const participantId = getParticipantId();
  if (!participantId) {
    window.location.href = '/index.html';
    return;
  }

  // 显示加载动画（可选）
  // showLoading();

  try {
    const [graphResponse, progressResponse] = await Promise.all([
      // 请求知识图谱数据
      fetch('/api/v1/knowledge-graph'),
      // 请求进度数据
      fetch(`/api/v1/participants/${participantId}/progress`)
    ]);

    if (!graphResponse.ok || !progressResponse.ok) throw new Error('请求失败');

    const graphResult = await graphResponse.json();
    const progressResult = await progressResponse.json();

    const graphData = graphResult.data;
    const completedTopics = new Set(progressResult.data.completed_topics);

    // 调用状态计算引擎
    const { processedNodes, dependencies } = processGraphData(graphData, completedTopics);
    // 渲染图谱
    const graphInstance = renderGraph(processedNodes, graphData.edges);
    setupGraphInteractions(graphInstance, dependencies, completedTopics);
  } catch (err) {
    console.error('图谱加载失败:', err);
    alert('图谱加载失败，请稍后重试');
  } finally {
    // 隐藏加载动画（可选）
    // hideLoading();
  }
});
