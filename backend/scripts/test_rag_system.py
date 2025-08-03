# diagnose.py
import sys
import os

# 添加项目根目录和模块目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..')
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'app', 'modules'))
sys.path.append(os.path.join(project_root, 'app'))

import logging
from RAG import initialize_rag_system
# 从正确的位置导入配置
from core.config import RAG_CONFIG, SERVICE_CONFIG
import requests
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rerank_results():
    """
    @brief 测试重排序结果
    """
    logger.info("=== 测试重排序结果 ===")
    
    # 初始化RAG系统
    retriever = initialize_rag_system()
    
    # 测试查询
    test_queries = [
        "人如何自律",
        "html是什么",
        "what is codeAID",
        "荀子有哪些名言"
    ]
    
    for query in test_queries:
        logger.info(f"\n{'='*50}")
        logger.info(f"查询: '{query}'")
        logger.info(f"{'='*50}")
        
        # 测试基础检索（无重排）
        logger.info("\n--- 基础检索结果（无重排） ---")
        base_context = retriever.retrieve_raw(query, use_rerank=False)
        logger.info("基础检索摘要:")
        for idx, item in enumerate(base_context, 1):
            logger.info(f"{idx}. {item.get('summary', '')}（{item.get('score', '')}）")
        
        # 测试重排序检索
        if RAG_CONFIG["reranker"].get("enable", False):
            logger.info("\n--- 重排序结果 ---")
            start_time = time.time()
            rerank_context = retriever.retrieve_raw(query, use_rerank=True)
            end_time = time.time()
            logger.info("重排序摘要:")
            for idx, item in enumerate(rerank_context, 1):
                logger.info(f"{idx}. {item.get('summary', '')}（{item.get('score', '')}）")
            logger.info(f"重排耗时: {end_time - start_time:.2f}秒")
        else:
            logger.warning("重排序功能未启用")

def test_ollama_service():
    """
    @brief 测试Ollama服务是否可用
    
    @return bool: 服务可用返回True，否则返回False
    """
    logger.info("\n=== 测试Ollama服务 ===")
    try:
        start_time = time.time()
        response = requests.get(SERVICE_CONFIG["ollama_host"], timeout=5)
        latency = time.time() - start_time
        
        if response.status_code == 200:
            logger.info(f"✅ Ollama服务可用! 响应时间: {latency:.2f}秒")
            return True
        else:
            logger.error(f"❌ Ollama服务异常: HTTP {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ 连接Ollama失败: {str(e)}")
        return False

def test_modelscope_api():
    """
    @brief 测试ModelScope API是否可用
    
    @return bool: API可用返回True，否则返回False
    """
    logger.info("\n=== 测试ModelScope API ===")
    import os
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    
    if not api_key:
        logger.error("❌ ModelScope API密钥未设置，请设置DASHSCOPE_API_KEY环境变量")
        return False
    
    try:
        # 尝试导入openai库
        from openai import OpenAI
    except ImportError:
        logger.error("❌ 未安装openai库，请运行 'pip install openai'")
        return False
    
    try:
        # 使用OpenAI兼容方式调用ModelScope API
        client = OpenAI(
            api_key=api_key,
            base_url=SERVICE_CONFIG["modelscope_base_url"]
        )
        
        start_time = time.time()
        # 简单测试API可用性
        models = client.models.list()
        latency = time.time() - start_time
        logger.info(f"✅ ModelScope API可用! 响应时间: {latency:.2f}秒")
        return True
    except Exception as e:
        logger.error(f"❌ ModelScope API连接失败: {str(e)}")
        return False

def test_embedding_generation():
    """
    @brief 测试嵌入生成功能
    
    @return bool: 嵌入生成成功返回True，否则返回False
    """
    logger.info("\n=== 测试嵌入生成 ===")
    
    # 从正确的位置导入配置
    from app.core.config import RAG_CONFIG
    from RAG.embeddings import EmbeddingModel
    
    try:
        # 修复：EmbeddingModel构造函数不需要参数
        model = EmbeddingModel()
        texts = ["这是一个测试句子"]
        
        start_time = time.time()
        embeddings = model.embed_texts(texts)
        latency = time.time() - start_time
        
        if embeddings and len(embeddings) == len(texts):
            logger.info(f"✅ 嵌入生成成功! 耗时: {latency:.2f}秒")
            logger.info(f"嵌入维度: {len(embeddings[0])}")
            return True
        else:
            logger.error(f"❌ 嵌入生成失败: 返回数量不匹配")
            return False
    except Exception as e:
        logger.error(f"❌ 嵌入生成异常: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=== 开始RAG重排序诊断 ===")
    
    # 根据配置检查相应的基础服务
    embedding_config = RAG_CONFIG["embeddings"]
    embedding_service_ok = True
    
    if embedding_config["model_type"] == "ollama":
        embedding_service_ok = test_ollama_service()
    elif embedding_config["model_type"] in ["modelscope", "dashscope"]:
        embedding_service_ok = test_modelscope_api()
    
    # 检查重排序服务（如果启用）
    reranker_config = RAG_CONFIG["reranker"]
    reranker_service_ok = True
    
    if reranker_config.get("enable", False):
        if reranker_config["model_type"] == "ollama":
            reranker_service_ok = test_ollama_service()
        elif reranker_config["model_type"] in ["modelscope", "dashscope"]:
            reranker_service_ok = test_modelscope_api()
    
    # 检查摘要服务
    summarizer_config = RAG_CONFIG["summarizer"]
    summarizer_service_ok = True
    
    if summarizer_config["model_type"] == "ollama":
        summarizer_service_ok = test_ollama_service()
    elif summarizer_config["model_type"] in ["modelscope", "dashscope"]:
        summarizer_service_ok = test_modelscope_api()
    
    all_services_ok = embedding_service_ok and reranker_service_ok and summarizer_service_ok
    
    if all_services_ok:
        # 运行嵌入生成测试
        embedding_ok = test_embedding_generation()
        
        if embedding_ok:
            # 运行重排序测试
            test_rerank_results()
        else:
            logger.error("嵌入生成功能测试失败")
    else:
        logger.error("基础服务不可用，无法进行后续测试")