import os
import logging
import soundfile as sf
import speech_recognition as sr
from gtts import gTTS
from deep_translator import GoogleTranslator
import tempfile
import uuid

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultilingualService:
    """
    Handles Speech-to-Text (ASR), Text-to-Speech (TTS), and Neural Machine Translation (NMT)
    using free Python libraries.
    """

    def __init__(self):
        self.recognizer = sr.Recognizer()
        
    def asr(self, audio_path: str, lang_code: str = 'en-IN') -> str:
        """
        Converts audio file to text using Google Speech Recognition (Free).
        Args:
            audio_path: Path to the audio file (must be WAV/AIFF/FLAC for speech_recognition, we handle conversion).
            lang_code: Language code (e.g., 'hi-IN', 'en-IN', 'gu-IN').
        Returns:
            Transcribed text.
        """
        wav_path = None
        try:
            # 1. Convert to WAV (PCM) if not already, as SR prefers it.
            # Telegram voice is usually OGG Opus. soundfile can read it and write to WAV.
            # Create a temp wav file
            wav_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.wav")
            
            # Read audio data + samplerate
            data, samplerate = sf.read(audio_path)
            
            # Write to WAV
            sf.write(wav_path, data, samplerate)
            
            # 2. Recognize
            with sr.AudioFile(wav_path) as source:
                audio_data = self.recognizer.record(source)
                # recognize_google is the free API
                text = self.recognizer.recognize_google(audio_data, language=lang_code)
                return text

        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition could not understand audio")
            return ""
        except sr.RequestError as e:
            logger.error(f"Could not request results from Google Speech Recognition service; {e}")
            raise Exception("Speech service unavailable")
        except Exception as e:
            logger.error(f"Error in ASR: {e}")
            raise e
        finally:
            # Cleanup temp wav
            if wav_path and os.path.exists(wav_path):
                os.remove(wav_path)

    def tts(self, text: str, lang_code: str = 'en') -> str:
        """
        Converts text to speech using gTTS (Google Text-to-Speech).
        Args:
            text: Text to convert.
            lang_code: Language code (e.g., 'hi', 'en', 'gu'). Note: gTTS use 2-letter codes mostly.
        Returns:
            Path to the generated MP3 file.
        """
        try:
            # gTTS expects 'en', 'hi', 'gu' etc. 
            # If we get 'en-IN', strip to 'en' unless gTTS supports specific variants (it does for some).
            # simplified: take first 2 chars
            short_lang = lang_code.split('-')[0]
            
            tts = gTTS(text=text, lang=short_lang, slow=False)
            
            output_path = os.path.join(tempfile.gettempdir(), f"response_{uuid.uuid4()}.mp3")
            tts.save(output_path)
            return output_path
        except Exception as e:
            logger.error(f"Error in TTS: {e}")
            raise e

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translates text from source to target language.
        Args:
            text: Text to translate.
            source_lang: Source language code (e.g. 'auto', 'hi', 'en').
            target_lang: Target language code.
        Returns:
            Translated text.
        """
        if source_lang == target_lang:
            return text
            
        try:
            # Map codes if necessary. deep_translator uses standard codes (en, hi, gu).
            src = source_lang.split('-')[0]
            tgt = target_lang.split('-')[0]
            
            translator = GoogleTranslator(source=src, target=tgt)
            return translator.translate(text)
        except Exception as e:
            logger.error(f"Error in Translation: {e}")
            # Fallback: return original text to avoid breaking flow
            return text
