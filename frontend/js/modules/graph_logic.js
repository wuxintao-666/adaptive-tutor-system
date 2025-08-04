
export const NODE_STATUS = {
  COMPLETED: 'completed',   // 已完成
  UNLOCKED: 'unlocked',     // 未完成
  LOCKED: 'locked'          // 锁定
};

/**
 * 根据图结构和用户完成的节点，标记每个节点的状态
 * @param {Object} graphData - 包含 nodes 和 edges 的图谱结构
 * @param {Set<string>} completedTopics - 用户已完成的知识点 ID 集合
 * @returns {Object} - 包含带状态的节点数组和依赖表
 */
export function processGraphData(graphData, completedTopics) {
  const dependencies = {};

  // 构建依赖表：目标节点 -> 所有前置节点
  graphData.edges.forEach(edge => {
    const target = edge.data.target;
    const source = edge.data.source;
    if (!dependencies[target]) dependencies[target] = [];
    dependencies[target].push(source);
  });
// 处理每个节点，计算状态
  const processedNodes = graphData.nodes.map(node => {
    const nodeId = node.data.id;
    const status = _calculateNodeStatus(nodeId, completedTopics, dependencies);
    return {
      data: node.data,
      status: status
    };
  });

  return { processedNodes, dependencies };
}

/**
 * 计算单个节点的状态
 * @param {string} nodeId - 节点 ID
 * @param {Set<string>} completedTopics - 已完成知识点集合
 * @param {Object} dependencies - 节点依赖关系表
 * @returns {'completed' | 'unlocked' | 'locked'}
 */
function _calculateNodeStatus(nodeId, completedTopics, dependencies) {
  if (completedTopics.has(nodeId)) return NODE_STATUS.COMPLETED;

  const prereqs = dependencies[nodeId] || [];
  
  if (prereqs.every(prereq => completedTopics.has(prereq))) {
    return NODE_STATUS.UNLOCKED;
  }

  return NODE_STATUS.LOCKED;
}
