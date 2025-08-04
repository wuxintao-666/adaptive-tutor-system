import os
import torch
import warnings
from typing import Dict, Any
from transformers import BertTokenizer, BertForSequenceClassification
from transformers.utils import logging
from safetensors.torch import load_file

# 设置日志级别和警告
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["PYTHONWARNINGS"] = "ignore"
warnings.filterwarnings("ignore")
logging.set_verbosity_error()

class SentimentAnalysisService:
    def __init__(self):
        # 加载模型和tokenizer
        model_dir = 'backend/models/sentiment_bert'
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
        
        # 标签映射
        self.label_map = {0: 'NEGATIVE', 1: 'NEUTRAL', 2: 'POSITIVE'}
      
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyzes the sentiment of a given text.
        Returns a dictionary like {'label': 'NEGATIVE', 'score': 0.95}
        """
        if not text.strip():
            return {"label": "NEUTRAL", "score": 1.0}
        
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
        return {
            'label': self.label_map.get(pred.item(), 'NEUTRAL'),
            'score': score.item()
        }
if __name__ == "__main__":
    sentiment_analysis_service = SentimentAnalysisService()
    while True:
        input_text = input("Enter your text: ")
        if input_text.lower() == "exit":
            break
        print(sentiment_analysis_service.analyze_sentiment(input_text))