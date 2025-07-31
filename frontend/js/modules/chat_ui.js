// 在 chat_ui.js 的 sendMessage 函数被调用时，由 test_page.js 传入上下文
function buildChatRequestBody(userMessage) {
    return {
        user_message: userMessage,
        conversation_history: getChatHistoryFromUI(),
        code_context: {
            // TODO: cxz 需要根据HTML内容改一下这里的DOM
            html: htmlEditor.getValue(),
            css: cssEditor.getValue(),
            js: jsEditor.getValue()
        },
        // **关键区别:** 上下文是测试任务ID
        task_context: `test:${getTopicIdFromUrl()}`
    };
}

function getChatHistoryFromUI() {
    // TODO: cxz 需要补全获取上下文的逻辑
}