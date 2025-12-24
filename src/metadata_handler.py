# Metadata handler - saves lyrics and covers
import logging
from pathlib import Path
from .config import Config
from .scanner import MusicFile

logger = logging.getLogger(__name__)


class MetadataHandler:
    """Handles saving lyrics and cover files."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def save_lyrics(self, music_file: MusicFile, lyrics_content: str) -> bool:
        """
        Save lyrics content to .lrc file.
        Returns True if successful.
        """
        if not lyrics_content:
            return False
        
        lyrics_path = music_file.lyrics_path
        
        # Check if already exists
        if lyrics_path.exists() and not self.config.overwrite_lyrics:
            logger.debug(f"Lyrics already exists, skipping: {lyrics_path}")
            return False
        
        try:
            # Ensure content ends with newline
            if not lyrics_content.endswith("\n"):
                lyrics_content += "\n"
            
            lyrics_path.write_text(lyrics_content, encoding="utf-8")
            logger.info(f"✓ Saved lyrics: {lyrics_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save lyrics {lyrics_path}: {e}")
            return False
    
    def save_cover(self, music_file: MusicFile, cover_data: bytes) -> bool:
        """
        Save cover image to cover.jpg in the album directory.
        Returns True if successful.
        """
        if not cover_data:
            return False
        
        cover_path = music_file.cover_path
        
        # Check if already exists
        if cover_path.exists() and not self.config.overwrite_cover:
            logger.debug(f"Cover already exists, skipping: {cover_path}")
            return False
        
        try:
            cover_path.write_bytes(cover_data)
            logger.info(f"✓ Saved cover: {cover_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save cover {cover_path}: {e}")
            return False
    
    def needs_processing(self, music_file: MusicFile) -> tuple[bool, bool]:
        """
        Check if a music file needs lyrics and/or cover download.
        Returns (needs_lyrics, needs_cover).
        """
        needs_lyrics = False
        needs_cover = False
        
        if self.config.download_lyrics:
            if not music_file.has_lyrics() or self.config.overwrite_lyrics:
                needs_lyrics = True
        
        if self.config.download_cover:
            if not music_file.has_cover() or self.config.overwrite_cover:
                needs_cover = True
        
        return needs_lyrics, needs_cover
