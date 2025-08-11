import { NODE_STATUS } from './graph_logic';

export function renderGraph(nodes, edges) {
  const graph = cytoscape({
    container: document.getElementById('graph'),
    elements: {
      nodes,
      edges
    },
    style: [
      {
        selector: 'node',
        style: {
          'label': 'data(label)',
          'text-valign': 'center',
          'text-halign': 'center',
          'background-color': ele => {
            const status = ele.data('status');
            return getColorByStatus(status);
          },
          'color': '#fff',
          'width': 40,
          'height': 40,
          'font-size': 8,
          'text-wrap': 'wrap',
          'text-max-width': 60
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 2,
          'line-color': '#ccc',
          'target-arrow-shape': 'triangle',
          'target-arrow-color': '#ccc',
          'curve-style': 'bezier'
        }
      }
    ],
    layout: {
      name: 'breadthfirst',
      directed: true,
      padding: 10,
      spacingFactor: 1.2,
      animate: false
    }
  });

  return graph;
}

export function setupGraphInteractions(graphInstance, dependencies, completedTopics) {
  graphInstance.on('tap', 'node', function (evt) {
    const node = evt.target;
    const id = node.id();
    const status = node.data('status');
    // 根据节点状态和用户选择跳转到学习或测试页面
    if (status === NODE_STATUS.COMPLETED || status === NODE_STATUS.UNLOCKED) {
      showJumpDialog(`当前节点为「${node.data('label')}」，请选择操作：`, id);
    } else {
      alert(`「${node.data('label')}」尚未解锁，请先完成前置知识点。`);
    }
  });
}

function getColorByStatus(status) {
  switch (status) {
    case NODE_STATUS.COMPLETED:
      return '#4caf50'; // 绿色
    case NODE_STATUS.UNLOCKED:
      return '#2196f3'; // 蓝色
    case NODE_STATUS.LOCKED:
    default:
      return '#aaa';     // 灰色
  }
}

// 显示跳转对话框
function showJumpDialog(message, id) {
  if (document.getElementById("jump-dialog")) return;

  const dialog = document.createElement("div");
  dialog.id = "jump-dialog";
  dialog.style.position = "fixed";
  dialog.style.top = "50%";
  dialog.style.left = "50%";
  dialog.style.transform = "translate(-50%, -50%)";
  dialog.style.backgroundColor = "#fff";
  dialog.style.border = "1px solid #ccc";
  dialog.style.borderRadius = "8px";
  dialog.style.padding = "20px";
  dialog.style.boxShadow = "0 2px 10px rgba(0,0,0,0.2)";
  dialog.style.zIndex = 9999;
  dialog.innerHTML = `
    <p style="margin-bottom: 12px;">${message}</p>
    <button id="learn-btn" style="margin-right: 10px;">学习页面</button>
    <button id="test-btn">测试页面</button>
    <button id="cancel-btn" style="margin-left: 10px; float: right;">取消</button>
  `;
  document.body.appendChild(dialog);

  document.getElementById("learn-btn").onclick = function () {
    window.location.href = `/pages/learning_page.html?topic=${id}`;
  };
  document.getElementById("test-btn").onclick = function () {
    window.location.href = `/pages/test_page.html?topic=${id}`;
  };
  document.getElementById("cancel-btn").onclick = function () {
    dialog.remove();
  };
}
