# Embed handler - embeds lyrics and covers into audio file metadata
import logging
from pathlib import Path
from typing import Optional, Protocol
from abc import ABC, abstractmethod

from mutagen import File as MutagenFile
from mutagen.id3 import ID3, USLT, APIC, ID3NoHeaderError
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

from .config import Config
from .scanner import MusicFile

logger = logging.getLogger(__name__)


class FormatEmbedder(ABC):
    """Abstract base class for format-specific metadata embedding."""
    
    @abstractmethod
    def embed_lyrics(self, path: Path, lyrics: str) -> bool:
        """Embed lyrics into the audio file."""
        pass
    
    @abstractmethod
    def embed_cover(self, path: Path, cover_data: bytes, mime_type: str = "image/jpeg") -> bool:
        """Embed cover image into the audio file."""
        pass
    
    @abstractmethod
    def has_embedded_lyrics(self, path: Path) -> bool:
        """Check if the file already has embedded lyrics."""
        pass
    
    @abstractmethod
    def has_embedded_cover(self, path: Path) -> bool:
        """Check if the file already has an embedded cover."""
        pass


class MP3Embedder(FormatEmbedder):
    """Handles embedding for MP3 files using ID3v2 tags."""
    
    def embed_lyrics(self, path: Path, lyrics: str) -> bool:
        try:
            try:
                audio = ID3(path)
            except ID3NoHeaderError:
                audio = ID3()
            
            # Remove existing lyrics
            audio.delall("USLT")
            
            # Add new lyrics (USLT = Unsynchronized lyrics)
            audio.add(USLT(
                encoding=3,  # UTF-8
                lang="xxx",  # Unknown language
                desc="",
                text=lyrics
            ))
            audio.save(path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to embed lyrics in MP3 {path}: {e}")
            return False
    
    def embed_cover(self, path: Path, cover_data: bytes, mime_type: str = "image/jpeg") -> bool:
        try:
            try:
                audio = ID3(path)
            except ID3NoHeaderError:
                audio = ID3()
            
            # Remove existing front covers
            audio.delall("APIC")
            
            # Add new cover (APIC = Attached picture)
            audio.add(APIC(
                encoding=3,  # UTF-8
                mime=mime_type,
                type=3,  # Front cover
                desc="Cover",
                data=cover_data
            ))
            audio.save(path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to embed cover in MP3 {path}: {e}")
            return False
    
    def has_embedded_lyrics(self, path: Path) -> bool:
        try:
            audio = ID3(path)
            return bool(audio.getall("USLT"))
        except Exception:
            return False
    
    def has_embedded_cover(self, path: Path) -> bool:
        try:
            audio = ID3(path)
            return bool(audio.getall("APIC"))
        except Exception:
            return False


class FLACEmbedder(FormatEmbedder):
    """Handles embedding for FLAC files using Vorbis Comments."""
    
    def embed_lyrics(self, path: Path, lyrics: str) -> bool:
        try:
            audio = FLAC(path)
            audio["LYRICS"] = lyrics
            audio.save()
            return True
            
        except Exception as e:
            logger.error(f"Failed to embed lyrics in FLAC {path}: {e}")
            return False
    
    def embed_cover(self, path: Path, cover_data: bytes, mime_type: str = "image/jpeg") -> bool:
        try:
            audio = FLAC(path)
            
            # Remove existing pictures
            audio.clear_pictures()
            
            # Create and add new picture
            pic = Picture()
            pic.type = 3  # Front cover
            pic.mime = mime_type
            pic.desc = "Cover"
            pic.data = cover_data
            
            audio.add_picture(pic)
            audio.save()
            return True
            
        except Exception as e:
            logger.error(f"Failed to embed cover in FLAC {path}: {e}")
            return False
    
    def has_embedded_lyrics(self, path: Path) -> bool:
        try:
            audio = FLAC(path)
            return "LYRICS" in audio or "lyrics" in audio
        except Exception:
            return False
    
    def has_embedded_cover(self, path: Path) -> bool:
        try:
            audio = FLAC(path)
            return bool(audio.pictures)
        except Exception:
            return False


class M4AEmbedder(FormatEmbedder):
    """Handles embedding for M4A/AAC files using MP4 atoms."""
    
    def embed_lyrics(self, path: Path, lyrics: str) -> bool:
        try:
            audio = MP4(path)
            audio["\xa9lyr"] = lyrics
            audio.save()
            return True
            
        except Exception as e:
            logger.error(f"Failed to embed lyrics in M4A {path}: {e}")
            return False
    
    def embed_cover(self, path: Path, cover_data: bytes, mime_type: str = "image/jpeg") -> bool:
        try:
            from mutagen.mp4 import MP4Cover
            
            audio = MP4(path)
            
            # Determine cover format
            if mime_type == "image/png":
                cover_format = MP4Cover.FORMAT_PNG
            else:
                cover_format = MP4Cover.FORMAT_JPEG
            
            audio["covr"] = [MP4Cover(cover_data, imageformat=cover_format)]
            audio.save()
            return True
            
        except Exception as e:
            logger.error(f"Failed to embed cover in M4A {path}: {e}")
            return False
    
    def has_embedded_lyrics(self, path: Path) -> bool:
        try:
            audio = MP4(path)
            return "\xa9lyr" in audio
        except Exception:
            return False
    
    def has_embedded_cover(self, path: Path) -> bool:
        try:
            audio = MP4(path)
            return "covr" in audio and audio["covr"]
        except Exception:
            return False


class OGGEmbedder(FormatEmbedder):
    """Handles embedding for OGG Vorbis files."""
    
    def embed_lyrics(self, path: Path, lyrics: str) -> bool:
        try:
            audio = OggVorbis(path)
            audio["LYRICS"] = lyrics
            audio.save()
            return True
            
        except Exception as e:
            logger.error(f"Failed to embed lyrics in OGG {path}: {e}")
            return False
    
    def embed_cover(self, path: Path, cover_data: bytes, mime_type: str = "image/jpeg") -> bool:
        try:
            import base64
            
            audio = OggVorbis(path)
            
            # Create FLAC picture and encode as base64
            pic = Picture()
            pic.type = 3  # Front cover
            pic.mime = mime_type
            pic.desc = "Cover"
            pic.data = cover_data
            
            # Encode picture as base64 and store in METADATA_BLOCK_PICTURE
            audio["METADATA_BLOCK_PICTURE"] = [base64.b64encode(pic.write()).decode("ascii")]
            audio.save()
            return True
            
        except Exception as e:
            logger.error(f"Failed to embed cover in OGG {path}: {e}")
            return False
    
    def has_embedded_lyrics(self, path: Path) -> bool:
        try:
            audio = OggVorbis(path)
            return "LYRICS" in audio or "lyrics" in audio
        except Exception:
            return False
    
    def has_embedded_cover(self, path: Path) -> bool:
        try:
            audio = OggVorbis(path)
            return "METADATA_BLOCK_PICTURE" in audio
        except Exception:
            return False


class EmbedHandler:
    """Handles embedding lyrics and covers into audio file metadata."""
    
    # Map file extensions to their embedders
    EMBEDDERS: dict[str, type[FormatEmbedder]] = {
        ".mp3": MP3Embedder,
        ".flac": FLACEmbedder,
        ".m4a": M4AEmbedder,
        ".mp4": M4AEmbedder,
        ".ogg": OGGEmbedder,
    }
    
    def __init__(self, config: Config):
        self.config = config
        self._embedder_cache: dict[str, FormatEmbedder] = {}
    
    def _get_embedder(self, path: Path) -> Optional[FormatEmbedder]:
        """Get the appropriate embedder for the file format."""
        ext = path.suffix.lower()
        
        if ext not in self.EMBEDDERS:
            return None
        
        # Cache embedder instances
        if ext not in self._embedder_cache:
            self._embedder_cache[ext] = self.EMBEDDERS[ext]()
        
        return self._embedder_cache[ext]
    
    def embed_lyrics(self, music_file: MusicFile, lyrics: str) -> bool:
        """
        Embed lyrics into the audio file's metadata.
        Returns True if successful.
        """
        if not lyrics:
            return False
        
        embedder = self._get_embedder(music_file.path)
        if not embedder:
            logger.debug(f"No embedder available for {music_file.path.suffix}")
            return False
        
        if embedder.embed_lyrics(music_file.path, lyrics):
            logger.info(f"✓ Embedded lyrics: {music_file.path.name}")
            return True
        
        return False
    
    def embed_cover(self, music_file: MusicFile, cover_data: bytes) -> bool:
        """
        Embed cover image into the audio file's metadata.
        Returns True if successful.
        """
        if not cover_data:
            return False
        
        embedder = self._get_embedder(music_file.path)
        if not embedder:
            logger.debug(f"No embedder available for {music_file.path.suffix}")
            return False
        
        # Detect mime type from data
        mime_type = self._detect_mime_type(cover_data)
        
        if embedder.embed_cover(music_file.path, cover_data, mime_type):
            logger.info(f"✓ Embedded cover: {music_file.path.name}")
            return True
        
        return False
    
    def has_embedded_lyrics(self, music_file: MusicFile) -> bool:
        """Check if the file already has embedded lyrics."""
        embedder = self._get_embedder(music_file.path)
        if not embedder:
            return False
        return embedder.has_embedded_lyrics(music_file.path)
    
    def has_embedded_cover(self, music_file: MusicFile) -> bool:
        """Check if the file already has an embedded cover."""
        embedder = self._get_embedder(music_file.path)
        if not embedder:
            return False
        return embedder.has_embedded_cover(music_file.path)
    
    def _detect_mime_type(self, data: bytes) -> str:
        """Detect image MIME type from binary data."""
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        elif data[:2] == b"\xff\xd8":
            return "image/jpeg"
        elif data[:4] == b"GIF8":
            return "image/gif"
        elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return "image/webp"
        else:
            return "image/jpeg"  # Default to JPEG
    
    def update_basic_info(
        self, 
        music_file: MusicFile, 
        artist: str, 
        title: str, 
        album: str
    ) -> bool:
        """
        Update basic metadata (artist, title, album) from API results.
        Uses mutagen's easy interface for cross-format compatibility.
        If overwrite_updates is False, only updates empty/missing fields.
        Returns True if any field was updated.
        """
        if not any([artist, title, album]):
            return False
        
        ext = music_file.path.suffix.lower()
        
        # Skip unsupported formats
        if ext not in self.EMBEDDERS:
            logger.debug(f"No embedder available for {ext}")
            return False
        
        try:
            # Use mutagen's easy interface for basic tags
            audio = MutagenFile(music_file.path, easy=True)
            if audio is None:
                return False
            
            updated = False
            
            # Always update fields when this method is called
            if artist:
                audio["artist"] = artist
                updated = True
            
            if title:
                audio["title"] = title
                updated = True
            
            if album:
                audio["album"] = album
                updated = True
            
            if updated:
                audio.save()
                logger.info(f"✓ Updated info: {music_file.path.name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update info for {music_file.path}: {e}")
            return False
    
    def has_basic_info(self, music_file: MusicFile) -> bool:
        """
        Check if the file already has basic metadata (artist, title, album).
        Returns True if all three fields are present and non-empty.
        """
        ext = music_file.path.suffix.lower()
        
        if ext not in self.EMBEDDERS:
            return False
        
        try:
            audio = MutagenFile(music_file.path, easy=True)
            if audio is None:
                return False
            
            # Check if all basic fields exist and have non-empty values
            has_artist = bool(audio.get("artist", [None])[0])
            has_title = bool(audio.get("title", [None])[0])
            has_album = bool(audio.get("album", [None])[0])
            
            return has_artist and has_title and has_album
            
        except Exception:
            return False


