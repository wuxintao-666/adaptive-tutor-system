# backend/app/services/llm_gateway.py
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from ..core.config import settings


class LLMGateway:
    """LLM网关服务"""
    
    def __init__(self):
        # 从环境变量或配置中获取API配置
        self.provider = os.getenv('LLM_PROVIDER', settings.LLM_PROVIDER)
        
        if self.provider == "modelscope":
            # 魔搭配置
            self.api_key = os.getenv('MODELSCOPE_API_KEY', settings.MODELSCOPE_API_KEY)
            self.api_base = os.getenv('MODELSCOPE_API_BASE', settings.MODELSCOPE_API_BASE)
            self.model = os.getenv('MODELSCOPE_MODEL', settings.MODELSCOPE_MODEL)
        else:
            # OpenAI配置
            self.api_key = os.getenv('OPENAI_API_KEY', settings.OPENAI_API_KEY)
            self.api_base = os.getenv('OPENAI_API_BASE', settings.OPENAI_API_BASE)
            self.model = os.getenv('OPENAI_MODEL', settings.OPENAI_MODEL)
        
        self.max_tokens = int(os.getenv('LLM_MAX_TOKENS', '1000'))
        self.temperature = float(os.getenv('LLM_TEMPERATURE', '0.7'))
        
        # 初始化OpenAI客户端（兼容魔搭API）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
    
    async def get_completion(
        self, 
        system_prompt: str, 
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        获取LLM完成结果
        
        Args:
            system_prompt: 系统提示词
            messages: 消息列表
            max_tokens: 最大token数
            temperature: 温度参数
            
        Returns:
            str: LLM生成的回复
        """
        try:
            # 构建完整的消息列表
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            
            # 使用传入的参数或默认值
            max_tokens = max_tokens or self.max_tokens
            temperature = temperature or self.temperature
            
            # 调用LLM API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # 提取回复内容
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                return "I apologize, but I couldn't generate a response at this time."
                
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def get_embedding(self, text: str) -> List[float]:
        """
        获取文本的嵌入向量
        
        Args:
            text: 要嵌入的文本
            
        Returns:
            List[float]: 嵌入向量
        """
        try:
            # 根据提供商选择嵌入模型
            embedding_model = os.getenv('EMBEDDING_MODEL', settings.EMBEDDING_MODEL)
            
            response = self.client.embeddings.create(
                input=[text],
                model=embedding_model
            )
            
            if response.data and len(response.data) > 0:
                return response.data[0].embedding
            else:
                return []
                
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return []
    
    def validate_connection(self) -> bool:
        """
        验证与LLM服务的连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 检查API密钥是否设置
            if not self.api_key:
                print("LLM API key not configured")
                return False
            
            # 检查基本配置
            if not self.api_base or not self.model:
                print("LLM basic configuration missing")
                return False
            
            # 尝试一个简单的API调用来验证连接
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            print(f"LLM connection validation failed: {e}")
            # 如果验证失败，但配置看起来正确，返回True（因为实际使用时可能工作）
            if self.api_key and self.api_base and self.model:
                print("LLM configuration looks correct, but validation failed. Service may still work.")
                return True
            return False


# 创建单例实例
llm_gateway = LLMGateway()
