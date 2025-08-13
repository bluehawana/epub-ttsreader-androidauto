import os
import logging
import tempfile
from pathlib import Path
from typing import Optional
import asyncio
import subprocess
import sys

logger = logging.getLogger(__name__)

class CoquiTTSService:
    """High-quality TTS service using Coqui XTTS-v2 for human-like voices"""
    
    def __init__(self):
        self.model = None
        self.device = "cpu"  # Will detect GPU if available
        self.initialized = False
        
    def _install_coqui_tts(self):
        """Install Coqui TTS if not available"""
        try:
            import TTS
            logger.info("Coqui TTS already installed")
            return True
        except ImportError:
            logger.info("Installing Coqui TTS...")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "coqui-tts"
                ])
                logger.info("Coqui TTS installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install Coqui TTS: {e}")
                return False
    
    def initialize(self) -> bool:
        """Initialize the Coqui TTS model"""
        try:
            if not self._install_coqui_tts():
                return False
            
            from TTS.api import TTS
            import torch
            
            # Detect device
            if torch.cuda.is_available():
                self.device = "cuda"
                logger.info("Using GPU for TTS")
            else:
                self.device = "cpu"
                logger.info("Using CPU for TTS")
            
            # Initialize XTTS-v2 model
            logger.info("Loading Coqui XTTS-v2 model...")
            self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
            
            self.initialized = True
            logger.info("Coqui XTTS-v2 initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Coqui TTS: {e}")
            return False
    
    async def text_to_speech(
        self, 
        text: str, 
        output_path: str, 
        voice_name: str = "en-US-AriaNeural",  # For compatibility, will be mapped
        speaker_audio: Optional[str] = None,
        language: str = "en"
    ) -> bool:
        """
        Convert text to speech using Coqui XTTS-v2
        
        Args:
            text: Text to convert
            output_path: Path to save MP3 file
            voice_name: Voice name (mapped from EdgeTTS names)
            speaker_audio: Path to speaker reference audio for voice cloning
            language: Language code (en, zh, es, etc.)
        
        Returns:
            bool: Success status
        """
        if not self.initialized and not self.initialize():
            logger.error("Coqui TTS not initialized")
            return False
        
        try:
            # Language mapping
            lang_map = {
                "en-US": "en",
                "zh-CN": "zh-cn", 
                "zh-TW": "zh-cn",
                "es": "es",
                "fr": "fr",
                "de": "de",
                "it": "it",
                "pt": "pt",
                "ru": "ru",
                "ar": "ar",
                "ja": "ja",
                "ko": "ko"
            }
            
            # Extract language from voice_name if provided in EdgeTTS format
            if "-" in voice_name:
                lang_code = voice_name.split("-")[0] + "-" + voice_name.split("-")[1]
                language = lang_map.get(lang_code, language)
            
            # Use default speaker audio if none provided
            if not speaker_audio:
                # You can add default speaker files for different languages
                speaker_audio = self._get_default_speaker(language)
            
            # Generate speech
            logger.info(f"Generating speech for text length: {len(text)} chars in {language}")
            
            # Run in thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._generate_speech,
                text, output_path, speaker_audio, language
            )
            
            # Verify file was created
            if Path(output_path).exists() and Path(output_path).stat().st_size > 0:
                logger.info(f"Successfully generated audio: {output_path}")
                return True
            else:
                logger.error(f"Failed to generate audio file: {output_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error in text_to_speech: {e}")
            return False
    
    def _generate_speech(self, text: str, output_path: str, speaker_audio: str, language: str):
        """Generate speech synchronously"""
        try:
            if speaker_audio and Path(speaker_audio).exists():
                # Voice cloning mode
                self.model.tts_to_file(
                    text=text,
                    file_path=output_path,
                    speaker_wav=speaker_audio,
                    language=language
                )
            else:
                # Use built-in speakers
                self.model.tts_to_file(
                    text=text,
                    file_path=output_path,
                    language=language
                )
                
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            raise
    
    def _get_default_speaker(self, language: str) -> Optional[str]:
        """Get default speaker audio for language"""
        # You can add default speaker files for different languages
        speaker_files = {
            "en": "speakers/english_female.wav",
            "zh-cn": "speakers/chinese_female.wav", 
            "es": "speakers/spanish_female.wav",
            "fr": "speakers/french_female.wav",
            # Add more languages as needed
        }
        
        speaker_path = speaker_files.get(language)
        if speaker_path and Path(speaker_path).exists():
            return speaker_path
        
        return None  # Will use model's default voice
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        return [
            "en-US-Female-Natural",
            "en-US-Male-Natural", 
            "zh-CN-Female-Natural",
            "zh-CN-Male-Natural",
            "es-ES-Female-Natural",
            "fr-FR-Female-Natural",
            "de-DE-Female-Natural",
            # Add more as you create speaker references
        ]
    
    def clone_voice_from_audio(self, reference_audio: str, output_dir: str = "cloned_voices") -> str:
        """
        Clone a voice from reference audio
        
        Args:
            reference_audio: Path to reference audio file (6+ seconds)
            output_dir: Directory to save cloned voice info
            
        Returns:
            str: Path to the cloned voice reference
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Copy reference audio to cloned voices directory
            import shutil
            voice_id = Path(reference_audio).stem
            cloned_path = Path(output_dir) / f"{voice_id}.wav"
            shutil.copy2(reference_audio, cloned_path)
            
            logger.info(f"Voice cloned and saved to: {cloned_path}")
            return str(cloned_path)
            
        except Exception as e:
            logger.error(f"Error cloning voice: {e}")
            return ""

# Fallback service class for easy switching
class AdvancedTTSService:
    """
    Advanced TTS service that can use multiple backends
    Falls back to EdgeTTS if Coqui is not available
    """
    
    def __init__(self):
        self.coqui_service = None
        self.edge_service = None
        self.backend = "edge"  # Default fallback
        
    async def initialize(self) -> str:
        """Initialize TTS services and return active backend"""
        # Try Coqui first for better quality
        try:
            self.coqui_service = CoquiTTSService()
            if self.coqui_service.initialize():
                self.backend = "coqui"
                logger.info("Using Coqui XTTS-v2 for high-quality TTS")
                return "coqui"
        except Exception as e:
            logger.warning(f"Coqui TTS not available: {e}")
        
        # Fallback to EdgeTTS
        try:
            from edge_tts_service import EdgeTTSService
            self.edge_service = EdgeTTSService()
            self.backend = "edge"
            logger.info("Using EdgeTTS as fallback")
            return "edge"
        except Exception as e:
            logger.error(f"No TTS service available: {e}")
            return "none"
    
    async def text_to_speech(
        self, 
        text: str, 
        output_path: str, 
        voice_name: str = "en-US-AriaNeural",
        **kwargs
    ) -> bool:
        """Convert text to speech using best available service"""
        if self.backend == "coqui" and self.coqui_service:
            return await self.coqui_service.text_to_speech(
                text, output_path, voice_name, **kwargs
            )
        elif self.backend == "edge" and self.edge_service:
            return await self.edge_service.text_to_speech(
                text, output_path, voice_name
            )
        else:
            logger.error("No TTS service available")
            return False
    
    def get_backend_info(self) -> dict:
        """Get information about active TTS backend"""
        return {
            "backend": self.backend,
            "quality": "high" if self.backend == "coqui" else "standard",
            "features": {
                "voice_cloning": self.backend == "coqui",
                "emotion_transfer": self.backend == "coqui", 
                "multilingual": True,
                "streaming": self.backend == "coqui"
            }
        }