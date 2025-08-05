# backend/app/services/sentiment_analysis_service.py
import re
from typing import Dict, Any
from ..schemas.chat import SentimentAnalysisResult


class SentimentAnalysisService:
    """情感分析服务"""
    
    def __init__(self):
        # 定义情感关键词映射
        self.emotion_keywords = {
            'FRUSTRATED': [
                'frustrated', 'frustrating', 'annoying', 'confusing', 'difficult',
                'hard', 'trouble', 'problem', 'error', 'bug', 'broken', 'not working',
                'doesn\'t work', 'can\'t', 'cannot', 'failed', 'failure', 'stuck',
                '困惑', '困难', '问题', '错误', '不行', '不会', '失败', '卡住'
            ],
            'CONFUSED': [
                'confused', 'confusing', 'unclear', 'not sure', 'don\'t understand',
                'what does', 'how to', 'why', 'what is', 'explain', 'help',
                '不明白', '不清楚', '不懂', '不知道', '怎么', '为什么', '解释', '帮助'
            ],
            'EXCITED': [
                'excited', 'great', 'awesome', 'amazing', 'wonderful', 'perfect',
                'working', 'success', 'solved', 'figured out', 'got it',
                '兴奋', '太好了', '棒', '完美', '成功', '解决了', '明白了'
            ],
            'NEUTRAL': [
                'ok', 'fine', 'alright', 'good', 'yes', 'no', 'maybe',
                '好的', '可以', '行', '是的', '不是', '也许'
            ]
        }
    
    def analyze_sentiment(self, text: str) -> SentimentAnalysisResult:
        """
        分析文本情感
        
        Args:
            text: 要分析的文本
            
        Returns:
            SentimentAnalysisResult: 情感分析结果
        """
        if not text or not isinstance(text, str):
            return SentimentAnalysisResult(
                label="NEUTRAL",
                confidence=1.0
            )
        
        # 转换为小写进行分析
        text_lower = text.lower()
        
        # 计算每种情感的匹配分数
        emotion_scores = {}
        for emotion, keywords in self.emotion_keywords.items():
            score = 0
            for keyword in keywords:
                # 使用正则表达式进行精确匹配
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                matches = len(re.findall(pattern, text_lower))
                score += matches
            
            if score > 0:
                emotion_scores[emotion] = score
        
        # 如果没有匹配到任何情感，返回NEUTRAL
        if not emotion_scores:
            return SentimentAnalysisResult(
                label="NEUTRAL",
                confidence=1.0
            )
        
        # 选择得分最高的情感
        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        
        # 计算置信度（基于匹配数量和文本长度）
        total_matches = sum(emotion_scores.values())
        confidence = min(1.0, total_matches / max(1, len(text.split())))
        
        return SentimentAnalysisResult(
            label=dominant_emotion[0],
            confidence=confidence,
            details={
                'emotion_scores': emotion_scores,
                'text_length': len(text),
                'word_count': len(text.split())
            }
        )
    
    def get_emotion_strategy(self, emotion_label: str) -> str:
        """
        根据情感标签获取教学策略
        
        Args:
            emotion_label: 情感标签
            
        Returns:
            str: 教学策略描述
        """
        strategies = {
            'FRUSTRATED': "The student seems frustrated. Your top priority is to be encouraging and empathetic. Acknowledge the difficulty before offering help. Use phrases like 'Don't worry, this is a tricky part' or 'Let's try a different approach'.",
            'CONFUSED': "The student seems confused. Break down concepts into smaller, simpler steps. Use analogies. Provide the simplest possible examples. Avoid jargon.",
            'EXCITED': "The student seems excited and engaged. You can introduce more advanced concepts and challenge them with deeper explanations.",
            'NEUTRAL': "The student seems neutral. Provide clear, structured explanations and check for understanding."
        }
        
        return strategies.get(emotion_label.upper(), strategies['NEUTRAL'])


# 创建单例实例
sentiment_analysis_service = SentimentAnalysisService()
