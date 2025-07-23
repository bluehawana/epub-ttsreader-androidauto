import azure.cognitiveservices.speech as speechsdk
import os
import tempfile
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class AzureTTSService:
    def __init__(self):
        self.speech_key = os.getenv('AZURE_SPEECH_KEY')
        self.speech_region = os.getenv('AZURE_SPEECH_REGION', 'eastus')
        
        if not self.speech_key:
            logger.warning("Azure Speech key not found, falling back to Edge TTS")
            self.use_edge_tts = True
        else:
            self.use_edge_tts = False
            
        # Configure Azure TTS
        if not self.use_edge_tts:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key, 
                region=self.speech_region
            )
            # Use neural voice for better quality
            self.speech_config.speech_synthesis_voice_name = "en-US-AriaNeural"
    
    async def text_to_speech(self, text: str, output_path: str, voice_name: str = None) -> bool:
        """Convert text to speech using Azure TTS or Edge TTS fallback"""
        try:
            if self.use_edge_tts:
                return await self._edge_tts_fallback(text, output_path, voice_name)
            else:
                return await self._azure_tts(text, output_path, voice_name)
        except Exception as e:
            logger.error(f"TTS conversion failed: {e}")
            # Fallback to Edge TTS
            return await self._edge_tts_fallback(text, output_path, voice_name)
    
    async def _azure_tts(self, text: str, output_path: str, voice_name: str = None) -> bool:
        """Use Azure Cognitive Services TTS"""
        try:
            # Set voice if specified
            if voice_name:
                self.speech_config.speech_synthesis_voice_name = voice_name
            
            # Configure audio output
            audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
            
            # Create synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            # Enhanced SSML for better speech quality
            ssml = f"""
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                <voice name="{self.speech_config.speech_synthesis_voice_name}">
                    <prosody rate="0.9" pitch="0%">
                        {self._clean_text_for_ssml(text)}
                    </prosody>
                </voice>
            </speak>
            """
            
            # Synthesize speech
            result = synthesizer.speak_ssml_async(ssml).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info(f"Azure TTS: Successfully created {output_path}")
                return True
            else:
                logger.error(f"Azure TTS failed: {result.reason}")
                return False
                
        except Exception as e:
            logger.error(f"Azure TTS error: {e}")
            return False
    
    async def _edge_tts_fallback(self, text: str, output_path: str, voice_name: str = None) -> bool:
        """Fallback to Edge TTS"""
        try:
            import edge_tts
            
            voice = voice_name or "en-US-AriaNeural"
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            
            logger.info(f"Edge TTS fallback: Successfully created {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Edge TTS fallback failed: {e}")
            return False
    
    def _clean_text_for_ssml(self, text: str) -> str:
        """Clean text for SSML compatibility"""
        # Escape XML special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        
        # Add pauses for better reading
        text = text.replace('. ', '. <break time="500ms"/>')
        text = text.replace('! ', '! <break time="500ms"/>')
        text = text.replace('? ', '? <break time="500ms"/>')
        text = text.replace('\n\n', '<break time="1s"/>')
        
        return text
    
    def get_available_voices(self):
        """Get list of available voices"""
        if self.use_edge_tts:
            return [
                "en-US-AriaNeural",
                "en-US-JennyNeural", 
                "en-US-GuyNeural",
                "en-GB-SoniaNeural",
                "en-AU-NatashaNeural"
            ]
        else:
            # Azure has many more voices available
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
        """Estimate Azure TTS costs"""
        if self.use_edge_tts:
            return {"service": "Edge TTS", "cost": 0.0, "free": True}
        
        # Azure pricing: $4 per 1M characters for Neural voices
        cost_per_char = 4.0 / 1_000_000
        estimated_cost = character_count * cost_per_char
        
        # First 500K characters are free each month
        free_chars = 500_000
        if character_count <= free_chars:
            return {
                "service": "Azure TTS", 
                "cost": 0.0, 
                "free": True,
                "remaining_free": free_chars - character_count
            }
        else:
            billable_chars = character_count - free_chars
            actual_cost = billable_chars * cost_per_char
            return {
                "service": "Azure TTS",
                "cost": actual_cost,
                "free": False,
                "free_used": free_chars,
                "billable_chars": billable_chars
            }