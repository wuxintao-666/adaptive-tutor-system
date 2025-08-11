import os
import warnings
from app.schemas.chat import SentimentAnalysisResult

class SentimentAnalysisService:
    def __init__(self):
        self.model_available = False
        self.model = None
        self.tokenizer = None
        self.device = None
        
        # 检查模型文件是否存在
        model_dir = 'backend/models/sentiment_bert'
        if os.path.exists(model_dir):
            try:
                # 只在模型文件存在时才导入相关库
                import torch
                from transformers import BertTokenizer, BertForSequenceClassification
                from transformers.utils import logging
                from safetensors.torch import load_file
                
                # 设置日志级别和警告
                os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
                os.environ["PYTHONWARNINGS"] = "ignore"
                warnings.filterwarnings("ignore")
                logging.set_verbosity_error()
                
                # 加载模型和tokenizer
                self.tokenizer = BertTokenizer.from_pretrained(model_dir)
                
                # 加载模型
                self.model = BertForSequenceClassification.from_pretrained(
                    model_dir,
                    local_files_only=True
                )
                
                # 设置设备
                self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                self.model = self.model.to(self.device)
                self.model.eval()
                
                self.model_available = True
                print("✅ BERT情感分析模型加载成功")
                
            except Exception as e:
                print(f"⚠️  BERT模型加载失败: {e}")
                print("📝 将使用简化的情感分析功能")
                self.model_available = False
        else:
            print("⚠️  未找到BERT模型文件，跳过模型加载")
            print("📝 情感分析功能将返回中性结果")
            self.model_available = False
        
        # 标签映射
        self.label_map = {0: 'NEGATIVE', 1: 'NEUTRAL', 2: 'POSITIVE'}
      
    def analyze_sentiment(self, text: str) -> SentimentAnalysisResult:
        """
        Analyzes the sentiment of a given text.
        Returns a SentimentAnalysisResult object
        """
        if not text.strip():
            return SentimentAnalysisResult(
                label="NEUTRAL",
                confidence=1.0
            )
        
        # 如果模型不可用，返回中性结果
        if not self.model_available:
            return SentimentAnalysisResult(
                label="NEUTRAL",
                confidence=1.0
            )
        
        # 只在模型可用时才导入torch
        import torch
        
        # 对输入文本进行编码
        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=128,
            truncation=True,
            padding='max_length',
            return_attention_mask=True,
            return_tensors='pt'
        )
        
        # 将输入数据移动到指定设备
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        # 模型推理
        with torch.no_grad():
            outputs = self.model(input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            probs = torch.nn.functional.softmax(logits, dim=1)
            score, pred = torch.max(probs, dim=1)
            
        # 返回结果
        return SentimentAnalysisResult(
            label=self.label_map.get(pred.item(), 'NEUTRAL'),
            confidence=score.item()
        )

# 创建单例实例
sentiment_analysis_service = SentimentAnalysisService()

if __name__ == "__main__":
    sentiment_analysis_service = SentimentAnalysisService()
    while True:
        input_text = input("Enter your text: ")
        if input_text.lower() == "exit":
            break
        print(sentiment_analysis_service.analyze_sentiment(input_text))
