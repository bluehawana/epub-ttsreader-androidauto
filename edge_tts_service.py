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
            voice = voice_name or "en-US-AriaNeural"
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            
            logger.info(f"EdgeTTS: Successfully created {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"EdgeTTS conversion failed: {e}")
            return False
    
    def get_available_voices(self):
        """Get list of available EdgeTTS voices"""
        return [
            "en-US-AriaNeural",
            "en-US-JennyNeural", 
            "en-US-GuyNeural",
            "en-US-SaraNeural",
            "en-US-TonyNeural",
            "en-GB-SoniaNeural",
            "en-GB-RyanNeural",
            "en-AU-NatashaNeural",
            "en-CA-ClaraNeural"
        ]
    
    def estimate_cost(self, character_count: int) -> dict:
        """EdgeTTS is completely free"""
        return {"service": "Edge TTS", "cost": 0.0, "free": True}