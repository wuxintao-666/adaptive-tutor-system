import os
import time
from tqdm import tqdm
import logging
import sys

# 获取当前文件所在目录作为基准路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
APP_DIR = os.path.dirname(BASE_DIR)

# 将app目录添加到sys.path
if APP_DIR not in sys.path:
    sys.path.append(APP_DIR)

# 确保能正确导入core.config
sys.path.append(BASE_DIR)

# 使用项目配置中的路径
from core.config import DATA_DIR, DOCUMENTS_DIR, VECTOR_STORE_DIR

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 动态导入模块
def initialize_rag_system(force_rebuild=False):
    """
    
    @brief 初始化整个RAG系统，包括文档加载器、分割器、嵌入模型、向量存储和检索器
    
    @param force_rebuild (bool): 是否强制重建向量库，默认为False
    
    @return Retriever: 初始化完成的检索器实例
    """
    from .document_loader import DocumentLoader
    from .text_splitter import TextSplitter
    from .embeddings import EmbeddingModel
    from .vector_store import VectorStore
    from .retriever import Retriever
    
    vector_store = VectorStore(rebuild_mode=force_rebuild)  
    if not force_rebuild and vector_store.index_path.exists() and vector_store.metadata_path.exists():
        logger.info("Using existing vector store")
        return Retriever()
    
    
    logger.info("Vector store not found or incomplete. Building new vector store...")
    if build_vector_store():
        return Retriever()
    else:
        logger.error("Failed to build vector store")
        return Retriever()

def build_vector_store(progress_callback=None):
    """
    
    @brief 手动触发整个向量存储的构建过程，包括文档加载、文本分割、向量生成和索引构建
    
    @param progress_callback (function, optional): 进度回调函数，用于报告构建进度
    
    @return bool: 构建成功返回True，否则返回False
    """
    logger.info("Building new vector store...")
    
    from .document_loader import DocumentLoader
    from .text_splitter import TextSplitter
    from .embeddings import EmbeddingModel
    from .vector_store import VectorStore
    
    # 加载文档
    loader = DocumentLoader()
    documents = loader.load_documents()
    
    # 添加进度回调
    progress_callback = progress_callback or (lambda **kw: None)
    progress_callback(stage="load", total=len(documents), current=0, message="开始加载文档")
    
    if not documents:
        logger.warning("No documents found to build vector store")
        progress_callback(stage="load", message="未找到文档", status="error")
        return False
    
    # 分割文档
    splitter = TextSplitter(progress_callback=progress_callback)
    chunks = splitter.split_documents(documents)
    
    # 检查是否有文本块
    if not chunks:
        logger.warning("No text chunks created from documents")
        progress_callback(stage="split", message="未生成文本块", status="error")
        return False
    
    # 生成嵌入
    embedding_model = EmbeddingModel()
    texts = [chunk["text"] for chunk in chunks]
    
    # 生成嵌入
    embedder = EmbeddingModel()
    progress_callback(stage="embed", total=len(chunks), current=0, message="开始生成嵌入")

    try:
        embeddings = embedder.embed_texts([chunk["text"] for chunk in chunks])
        if not embeddings:
            logger.error("Failed to generate embeddings")
            progress_callback(stage="embed", message="嵌入生成失败", status="error")
            return False
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        progress_callback(stage="embed", message=f"嵌入生成异常: {str(e)}", status="error")
        return False

    progress_callback(stage="embed", current=len(chunks), total=len(chunks), message="嵌入生成完成", status="completed")
    
    logger.info(f"Embeddings generated in {time.time()-start_time:.2f} seconds")
    
    # 构建向量存储
    vector_store = VectorStore()
    
    # 传递进度回调函数
    success = vector_store.build_index(embeddings, chunks)
    
    if success:
        logger.info("Vector store built successfully")
        return True
    else:
        logger.error("Failed to build vector store")
        return False