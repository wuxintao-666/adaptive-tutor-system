# RAGmodule/__main__.py
from .diagnose import test_ollama_service, test_embedding_generation, test_rerank_results
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("=== RAG Module Diagnostic ===")
    
    # 检查基础服务
    ollama_ok = test_ollama_service()
    embedding_ok = test_embedding_generation()
    
    if ollama_ok and embedding_ok:
        # 运行重排序测试
        test_rerank_results()
    else:
        logger.error("基础服务不可用，无法进行重排序测试")

if __name__ == "__main__":
    main()