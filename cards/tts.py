"""
Сервис для озвучки слов через gTTS.
"""
import os
from pathlib import Path
from gtts import gTTS
from django.conf import settings


class TTSService:
    """Сервис для работы с текстовым озвучиванием."""
    
    @staticmethod
    def get_audio_path(word: str, language: str = None) -> Path:
        """
        Получает путь к аудиофайлу для слова.
        
        Args:
            word: Слово для озвучки
            language: Язык (по умолчанию из настроек)
        
        Returns:
            Path: Путь к файлу
        """
        if language is None:
            language = getattr(settings, 'TTS_LANGUAGE', 'en')
        
        # Создаем безопасное имя файла
        safe_word = "".join(c for c in word if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_word = safe_word.replace(' ', '_')
        filename = f"{safe_word}_{language}.mp3"
        
        cache_dir = getattr(settings, 'TTS_CACHE_DIR', Path(settings.MEDIA_ROOT) / 'tts_cache')
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        return cache_dir / filename
    
    @staticmethod
    def generate_audio(word: str, language: str = None) -> Path:
        """
        Генерирует аудиофайл для слова.
        
        Args:
            word: Слово для озвучки
            language: Язык (по умолчанию из настроек)
        
        Returns:
            Path: Путь к созданному файлу
        """
        if language is None:
            language = getattr(settings, 'TTS_LANGUAGE', 'en')
        
        audio_path = TTSService.get_audio_path(word, language)
        
        # Если файл уже существует, возвращаем его
        if audio_path.exists():
            return audio_path
        
        # Генерируем новый файл
        try:
            tts = gTTS(text=word, lang=language, slow=False)
            tts.save(str(audio_path))
            return audio_path
        except Exception as e:
            # Если не удалось создать, пробуем английский
            if language != 'en':
                return TTSService.generate_audio(word, 'en')
            raise e

