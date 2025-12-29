"""
Tests for embed_handler module - metadata embedding functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from io import BytesIO

from src.config import Config
from src.embed_handler import (
    EmbedHandler,
    MP3Embedder,
    FLACEmbedder,
    M4AEmbedder,
    OGGEmbedder,
)
from src.scanner import MusicFile


class TestEmbedHandler:
    """Test EmbedHandler main class."""
    
    def test_get_embedder_mp3(self):
        config = Config()
        handler = EmbedHandler(config)
        
        music_file = MusicFile(
            path=Path("/music/test.mp3"),
            artist="Artist",
            title="Title",
            album="Album",
        )
        
        embedder = handler._get_embedder(music_file.path)
        assert isinstance(embedder, MP3Embedder)
    
    def test_get_embedder_flac(self):
        config = Config()
        handler = EmbedHandler(config)
        
        music_file = MusicFile(
            path=Path("/music/test.flac"),
            artist="Artist",
            title="Title",
            album="Album",
        )
        
        embedder = handler._get_embedder(music_file.path)
        assert isinstance(embedder, FLACEmbedder)
    
    def test_get_embedder_m4a(self):
        config = Config()
        handler = EmbedHandler(config)
        
        music_file = MusicFile(
            path=Path("/music/test.m4a"),
            artist="Artist",
            title="Title",
            album="Album",
        )
        
        embedder = handler._get_embedder(music_file.path)
        assert isinstance(embedder, M4AEmbedder)
    
    def test_get_embedder_ogg(self):
        config = Config()
        handler = EmbedHandler(config)
        
        music_file = MusicFile(
            path=Path("/music/test.ogg"),
            artist="Artist",
            title="Title",
            album="Album",
        )
        
        embedder = handler._get_embedder(music_file.path)
        assert isinstance(embedder, OGGEmbedder)
    
    def test_get_embedder_unsupported(self):
        config = Config()
        handler = EmbedHandler(config)
        
        music_file = MusicFile(
            path=Path("/music/test.wav"),
            artist="Artist",
            title="Title",
            album="Album",
        )
        
        embedder = handler._get_embedder(music_file.path)
        assert embedder is None
    
    def test_detect_mime_type_jpeg(self):
        config = Config()
        handler = EmbedHandler(config)
        
        # JPEG magic bytes
        jpeg_data = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        assert handler._detect_mime_type(jpeg_data) == "image/jpeg"
    
    def test_detect_mime_type_png(self):
        config = Config()
        handler = EmbedHandler(config)
        
        # PNG magic bytes
        png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00"
        assert handler._detect_mime_type(png_data) == "image/png"
    
    def test_detect_mime_type_gif(self):
        config = Config()
        handler = EmbedHandler(config)
        
        # GIF magic bytes
        gif_data = b"GIF89a\x00\x00\x00"
        assert handler._detect_mime_type(gif_data) == "image/gif"
    
    def test_detect_mime_type_webp(self):
        config = Config()
        handler = EmbedHandler(config)
        
        # WebP magic bytes
        webp_data = b"RIFF\x00\x00\x00\x00WEBP"
        assert handler._detect_mime_type(webp_data) == "image/webp"
    
    def test_detect_mime_type_unknown(self):
        config = Config()
        handler = EmbedHandler(config)
        
        # Unknown bytes - defaults to JPEG
        unknown_data = b"\x00\x00\x00\x00"
        assert handler._detect_mime_type(unknown_data) == "image/jpeg"
    
    def test_embed_lyrics_empty_string(self):
        config = Config(embed_lyrics=True)
        handler = EmbedHandler(config)
        
        music_file = MusicFile(
            path=Path("/music/test.mp3"),
            artist="Artist",
            title="Title",
            album="Album",
        )
        
        result = handler.embed_lyrics(music_file, "")
        assert result is False
    
    def test_embed_cover_empty_bytes(self):
        config = Config(embed_cover=True)
        handler = EmbedHandler(config)
        
        music_file = MusicFile(
            path=Path("/music/test.mp3"),
            artist="Artist",
            title="Title",
            album="Album",
        )
        
        result = handler.embed_cover(music_file, b"")
        assert result is False
    
    def test_embed_lyrics_unsupported_format(self):
        config = Config(embed_lyrics=True)
        handler = EmbedHandler(config)
        
        music_file = MusicFile(
            path=Path("/music/test.wav"),
            artist="Artist",
            title="Title",
            album="Album",
        )
        
        result = handler.embed_lyrics(music_file, "[00:00.00]Lyrics")
        assert result is False
    
    def test_embed_cover_unsupported_format(self):
        config = Config(embed_cover=True)
        handler = EmbedHandler(config)
        
        music_file = MusicFile(
            path=Path("/music/test.wav"),
            artist="Artist",
            title="Title",
            album="Album",
        )
        
        result = handler.embed_cover(music_file, b"fake image data")
        assert result is False


class TestConfigEmbedOptions:
    """Test new embedding configuration options."""
    
    def test_default_embed_config(self):
        config = Config()
        assert config.embed_lyrics is False
        assert config.embed_cover is False
        assert config.overwrite_embedded is False
    
    def test_from_env_embed_options(self):
        with patch.dict("os.environ", {
            "EMBED_LYRICS": "true",
            "EMBED_COVER": "true",
            "OVERWRITE_EMBEDDED": "true",
        }):
            config = Config.from_env()
            assert config.embed_lyrics is True
            assert config.embed_cover is True
            assert config.overwrite_embedded is True
    
    def test_from_env_embed_options_false(self):
        with patch.dict("os.environ", {
            "EMBED_LYRICS": "false",
            "EMBED_COVER": "false",
            "OVERWRITE_EMBEDDED": "false",
        }):
            config = Config.from_env()
            assert config.embed_lyrics is False
            assert config.embed_cover is False
            assert config.overwrite_embedded is False


class TestMP3Embedder:
    """Test MP3 embedder format detection."""
    
    def test_has_embedded_lyrics_no_file(self, tmp_path):
        embedder = MP3Embedder()
        result = embedder.has_embedded_lyrics(tmp_path / "nonexistent.mp3")
        assert result is False
    
    def test_has_embedded_cover_no_file(self, tmp_path):
        embedder = MP3Embedder()
        result = embedder.has_embedded_cover(tmp_path / "nonexistent.mp3")
        assert result is False


class TestFLACEmbedder:
    """Test FLAC embedder format detection."""
    
    def test_has_embedded_lyrics_no_file(self, tmp_path):
        embedder = FLACEmbedder()
        result = embedder.has_embedded_lyrics(tmp_path / "nonexistent.flac")
        assert result is False
    
    def test_has_embedded_cover_no_file(self, tmp_path):
        embedder = FLACEmbedder()
        result = embedder.has_embedded_cover(tmp_path / "nonexistent.flac")
        assert result is False


class TestM4AEmbedder:
    """Test M4A embedder format detection."""
    
    def test_has_embedded_lyrics_no_file(self, tmp_path):
        embedder = M4AEmbedder()
        result = embedder.has_embedded_lyrics(tmp_path / "nonexistent.m4a")
        assert result is False
    
    def test_has_embedded_cover_no_file(self, tmp_path):
        embedder = M4AEmbedder()
        result = embedder.has_embedded_cover(tmp_path / "nonexistent.m4a")
        assert result is False


class TestOGGEmbedder:
    """Test OGG embedder format detection."""
    
    def test_has_embedded_lyrics_no_file(self, tmp_path):
        embedder = OGGEmbedder()
        result = embedder.has_embedded_lyrics(tmp_path / "nonexistent.ogg")
        assert result is False
    
    def test_has_embedded_cover_no_file(self, tmp_path):
        embedder = OGGEmbedder()
        result = embedder.has_embedded_cover(tmp_path / "nonexistent.ogg")
        assert result is False
