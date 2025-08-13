import edge_tts
import logging
import asyncio

logger = logging.getLogger(__name__)

class EdgeTTSService:
    def __init__(self):
        logger.info("Initialized EdgeTTS service")
    
    async def text_to_speech(self, text: str, output_path: str, voice_name: str = None) -> bool:
        """Convert text to speech using EdgeTTS"""
        try:
            voice = voice_name or self.detect_language_and_voice(text)
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            
            logger.info(f"EdgeTTS: Successfully created {output_path} using voice {voice}")
            return True
            
        except Exception as e:
            logger.error(f"EdgeTTS conversion failed: {e}")
            return False
    
    def get_available_voices(self):
        """Get list of available EdgeTTS voices"""
        return [
            # English voices
            "en-US-AriaNeural",
            "en-US-JennyNeural", 
            "en-US-GuyNeural",
            "en-US-SaraNeural",
            "en-US-TonyNeural",
            "en-GB-SoniaNeural",
            "en-GB-RyanNeural",
            "en-AU-NatashaNeural",
            "en-CA-ClaraNeural",
            
            # Chinese voices (Simplified)
            "zh-CN-XiaoxiaoNeural",
            "zh-CN-YunxiNeural", 
            "zh-CN-YunjianNeural",
            "zh-CN-XiaoyiNeural",
            "zh-CN-YunyangNeural",
            "zh-CN-XiaochenNeural",
            "zh-CN-XiaohanNeural",
            "zh-CN-XiaomengNeural",
            "zh-CN-XiaomoNeural",
            "zh-CN-XiaoqiuNeural",
            "zh-CN-XiaoruiNeural",
            "zh-CN-XiaoshuangNeural",
            "zh-CN-XiaoxuanNeural",
            "zh-CN-XiaoyanNeural",
            "zh-CN-XiaoyouNeural",
            
            # Chinese voices (Traditional - Taiwan)
            "zh-TW-HsiaoChenNeural",
            "zh-TW-YunJheNeural",
            "zh-TW-HsiaoYuNeural",
            
            # Chinese voices (Traditional - Hong Kong)  
            "zh-HK-HiuMaanNeural",
            "zh-HK-WanLungNeural",
            "zh-HK-HiuGaaiNeural"
        ]
    
    def detect_language_and_voice(self, text: str) -> str:
        """Detect language from text and return appropriate voice"""
        import re
        
        # Count Chinese characters (CJK Unified Ideographs)
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text.strip())
        
        if total_chars == 0:
            return "en-US-AriaNeural"
        
        chinese_ratio = chinese_chars / total_chars
        
        # If more than 30% Chinese characters, use Chinese voice
        if chinese_ratio > 0.3:
            logger.info(f"Detected Chinese text ({chinese_ratio:.2%} Chinese chars), using Chinese voice")
            return "zh-CN-XiaoxiaoNeural"  # Pleasant female Chinese voice
        
        # Default to English
        logger.info(f"Detected non-Chinese text ({chinese_ratio:.2%} Chinese chars), using English voice")
        return "en-US-AriaNeural"
    
    def estimate_cost(self, character_count: int) -> dict:
        """EdgeTTS is completely free"""
        return {"service": "Edge TTS", "cost": 0.0, "free": True}