import os
import json
import logging
from pathlib import Path
from typing import List, Dict
from core.config import DOCUMENTS_DIR, RAG_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentLoader:
    """
    @brief 文档加载器类，用于从指定目录加载文档
    
    @details 该类支持加载多种格式的文档，包括JSON、TXT等格式
    """
    
    def __init__(self):
        """
        @brief 初始化文档加载器
        
        @details 设置支持的文件扩展名和文档目录路径
        """
        self.supported_extensions = RAG_CONFIG["document_loader"]["extensions"]
        self.documents_dir = Path(DOCUMENTS_DIR)
        
    def load_documents(self) -> List[Dict[str, str]]:
        """
        @brief 加载所有支持的文档
        
        @details 遍历文档目录，加载所有支持的文档文件
        
        @return List[Dict[str, str]]: 包含文档内容和元数据的列表
        """
        documents = []
        
        if not self.documents_dir.exists():
            logger.warning(f"Documents directory not found: {self.documents_dir}")
            return documents
            
        logger.info(f"Loading documents from {self.documents_dir}")
        
        for file_path in self.documents_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                try:
                    doc = self._load_single_document(file_path)
                    if doc:
                        documents.append(doc)
                except Exception as e:
                    logger.error(f"Error loading document {file_path}: {str(e)}")
                    
        logger.info(f"Loaded {len(documents)} documents")
        return documents
        
    def _load_single_document(self, file_path: Path) -> Dict[str, str]:
        """
        @brief 加载单个文档文件
        
        @details 根据文件扩展名选择适当的加载方法
        
        @param file_path (Path): 文档文件路径
        
        @return Dict[str, str]: 包含文档内容和元数据的字典
        """
        try:
            suffix = file_path.suffix.lower()
            if suffix == ".json":
                return self._load_json_document(file_path)
            elif suffix == ".txt":
                return self._load_text_document(file_path)
            elif suffix == ".pdf":
                return self._load_pdf_document(file_path)
            elif suffix == ".md":
                return self._load_markdown_document(file_path)
            else:
                # 对于其他格式，暂时以文本方式加载
                return self._load_text_document(file_path)
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            return None
            
    def _load_json_document(self, file_path: Path) -> Dict[str, str]:
        """
        @brief 加载JSON格式文档
        
        @details 解析JSON文件并提取文档内容和元数据
        
        @param file_path (Path): JSON文档文件路径
        
        @return Dict[str, str]: 包含文档内容和元数据的字典
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # 处理不同格式的JSON数据
        if isinstance(data, list):
            # 如果是列表，连接所有项目
            content = "\n".join([str(item) for item in data])
        elif isinstance(data, dict):
            # 如果是字典，转换为字符串
            content = json.dumps(data, ensure_ascii=False, indent=2)
        else:
            content = str(data)
            
        return {
            "content": content,
            "source": str(file_path.relative_to(self.documents_dir)),
            "file_type": "json"
        }
        
    def _load_pdf_document(self, file_path: Path) -> Dict[str, str]:
        """
        @brief 加载PDF格式文档
        
        @details 提取PDF文件中的文本内容
        
        @param file_path (Path): PDF文档文件路径
        
        @return Dict[str, str]: 包含文档内容和元数据的字典
        """
        try:
            # 尝试导入PyPDF2库
            import PyPDF2
            with open(file_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text() + "\n"
                
            return {
                "content": content,
                "source": str(file_path.relative_to(self.documents_dir)),
                "file_type": "pdf"
            }
        except ImportError:
            logger.warning(f"PyPDF2 library not installed. Cannot process PDF file: {file_path}")
            logger.warning("Please install PyPDF2 with: pip install PyPDF2")
            # 如果无法处理PDF，返回空内容但保留文件信息
            return {
                "content": "",
                "source": str(file_path.relative_to(self.documents_dir)),
                "file_type": "pdf"
            }
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            # 即使提取失败，也返回文件信息
            return {
                "content": "",
                "source": str(file_path.relative_to(self.documents_dir)),
                "file_type": "pdf"
            }
            
    def _load_markdown_document(self, file_path: Path) -> Dict[str, str]:
        """
        @brief 加载Markdown格式文档
        
        @details 读取Markdown文件内容（与文本文件处理方式相同）
        
        @param file_path (Path): Markdown文档文件路径
        
        @return Dict[str, str]: 包含文档内容和元数据的字典
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return {
            "content": content,
            "source": str(file_path.relative_to(self.documents_dir)),
            "file_type": "md"
        }
            
    def _load_text_document(self, file_path: Path) -> Dict[str, str]:
        """
        @brief 加载文本格式文档
        
        @details 读取文本文件内容
        
        @param file_path (Path): 文本文档文件路径
        
        @return Dict[str, str]: 包含文档内容和元数据的字典
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return {
            "content": content,
            "source": str(file_path.relative_to(self.documents_dir)),
            "file_type": file_path.suffix.lower()[1:] if file_path.suffix.lower() else "txt"
        }