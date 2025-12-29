# Music file scanner
import os
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Iterator
from mutagen import File as MutagenFile
from .config import Config

logger = logging.getLogger(__name__)


@dataclass
class MusicFile:
    """Represents a scanned music file with its metadata."""
    path: Path
    artist: str
    title: str
    album: str
    
    @property
    def lyrics_path(self) -> Path:
        """Path where lyrics file should be saved."""
        return self.path.with_suffix(".lrc")
    
    @property
    def cover_path(self) -> Path:
        """Path where cover image should be saved (in same directory)."""
        return self.path.parent / "cover.jpg"
    
    def has_lyrics(self) -> bool:
        """Check if lyrics file already exists."""
        return self.lyrics_path.exists()
    
    def has_cover(self) -> bool:
        """Check if cover file already exists in the directory."""
        return self.cover_path.exists()


class MusicScanner:
    """Scans directories for music files and extracts metadata."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def scan(self, root_path: Optional[str] = None) -> Iterator[MusicFile]:
        """
        Recursively scan directory for music files.
        Yields MusicFile objects with extracted metadata.
        """
        scan_path = Path(root_path or self.config.music_path)
        
        if not scan_path.exists():
            logger.error(f"Music path does not exist: {scan_path}")
            return
        
        logger.info(f"Scanning: {scan_path}")
        
        for root, dirs, files in os.walk(scan_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            
            for filename in files:
                if not self._is_audio_file(filename):
                    continue
                
                file_path = Path(root) / filename
                music_file = self._parse_file(file_path)
                
                if music_file and music_file.title:
                    yield music_file
    
    def _is_audio_file(self, filename: str) -> bool:
        """Check if file has a supported audio extension."""
        return filename.lower().endswith(self.config.audio_extensions)
    
    def _parse_file(self, file_path: Path) -> Optional[MusicFile]:
        """Extract metadata from an audio file."""
        try:
            audio = MutagenFile(file_path, easy=True)
            if audio is None:
                return None
            
            # Extract metadata with fallbacks
            artist = self._get_tag(audio, "artist", "")
            title = self._get_tag(audio, "title", "")
            album = self._get_tag(audio, "album", "")
            
            # If no title in tags, try to use filename
            if not title:
                title = file_path.stem
                logger.debug(f"No title tag, using filename: {title}")
            
            # Infer from folder structure: Artist/Album/song.mp3
            if self.config.use_folder_structure:
                parent = file_path.parent  # Album folder
                grandparent = parent.parent  # Artist folder
                music_root = Path(self.config.music_path).resolve()
                
                # Use grandparent as artist if no ID3 artist
                # Make sure grandparent is not the music root itself
                # Use grandparent as artist if no ID3 artist
                # Make sure grandparent is not the music root itself
                if not artist and grandparent.name and grandparent.resolve() != music_root:
                    artist = grandparent.name
                    logger.debug(f"No artist tag, using folder: {artist}")
                elif not artist and parent.name and grandparent.resolve() == music_root:
                    # Shallow structure: Artist/song.mp3
                    # Parent is likely the artist, not the album
                    artist = parent.name
                    album = ""  # Clear album as it was likely misidentified
                    logger.debug(f"Shallow structure detected. Using parent as artist: {artist}")
                
                # Use parent as album if no ID3 album
                if not album and parent.name and not (grandparent.resolve() == music_root and not artist):
                    # Only use parent as album if it wasn't just used as artist
                    if parent.name != artist:
                        album = parent.name
                        logger.debug(f"No album tag, using folder: {album}")
            
            # Fallback to default_artist if still no artist
            if not artist and self.config.default_artist:
                artist = self.config.default_artist
                logger.debug(f"No artist tag, using default: {artist}")
            
            return MusicFile(
                path=file_path,
                artist=artist,
                title=title,
                album=album,
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return None
    
    def _get_tag(self, audio, tag_name: str, default: str = "") -> str:
        """Safely get a tag value from audio metadata."""
        try:
            value = audio.get(tag_name)
            if value:
                # Tags can be lists, take first value
                if isinstance(value, list):
                    return str(value[0])
                return str(value)
        except Exception:
            pass
        return default
