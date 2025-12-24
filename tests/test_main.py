"""
Tests for TuneHub Music Metadata Tool
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.config import Config
from src.scanner import MusicScanner, MusicFile
from src.tunehub_client import TuneHubClient, SearchResult
from src.metadata_handler import MetadataHandler


class TestConfig:
    """Test configuration loading."""
    
    def test_default_config(self):
        config = Config()
        assert config.music_path == "/music"
        assert config.scan_interval == 0
        assert config.download_lyrics is True
        assert config.download_cover is True
        assert "netease" in config.platforms
    
    def test_from_env(self):
        with patch.dict("os.environ", {
            "MUSIC_PATH": "/test/music",
            "SCAN_INTERVAL": "3600",
            "OVERWRITE_LYRICS": "true",
            "PLATFORMS": "kuwo,qq",
        }):
            config = Config.from_env()
            assert config.music_path == "/test/music"
            assert config.scan_interval == 3600
            assert config.overwrite_lyrics is True
            assert config.platforms == ["kuwo", "qq"]


class TestSearchResult:
    """Test SearchResult dataclass."""
    
    def test_from_dict(self):
        data = {
            "id": "123",
            "name": "晴天",
            "artist": "周杰伦",
            "album": "叶惠美",
            "platform": "netease",
            "lrc": "https://example.com/lrc",
            "pic": "https://example.com/pic",
        }
        result = SearchResult.from_dict(data)
        assert result.id == "123"
        assert result.name == "晴天"
        assert result.artist == "周杰伦"
        assert result.platform == "netease"


class TestMusicFile:
    """Test MusicFile dataclass."""
    
    def test_lyrics_path(self):
        music = MusicFile(
            path=Path("/music/album/song.mp3"),
            artist="Artist",
            title="Song",
            album="Album",
        )
        assert music.lyrics_path == Path("/music/album/song.lrc")
    
    def test_cover_path(self):
        music = MusicFile(
            path=Path("/music/album/song.mp3"),
            artist="Artist",
            title="Song",
            album="Album",
        )
        assert music.cover_path == Path("/music/album/cover.jpg")


class TestTuneHubClient:
    """Test TuneHub API client."""
    
    def test_find_best_match_exact(self):
        config = Config()
        client = TuneHubClient(config)
        
        results = [
            SearchResult("1", "晴天", "周杰伦", "叶惠美", "netease", "", ""),
            SearchResult("2", "晴天 Live", "周杰伦", "演唱会", "kuwo", "", ""),
        ]
        
        best = client.find_best_match(results, "周杰伦", "晴天")
        assert best.id == "1"
        client.close()
    
    def test_find_best_match_no_results(self):
        config = Config()
        client = TuneHubClient(config)
        
        best = client.find_best_match([], "Artist", "Title")
        assert best is None
        client.close()


class TestMetadataHandler:
    """Test metadata saving."""
    
    def test_needs_processing_no_files(self, tmp_path):
        config = Config(download_lyrics=True, download_cover=True)
        handler = MetadataHandler(config)
        
        music = MusicFile(
            path=tmp_path / "song.mp3",
            artist="Artist",
            title="Song",
            album="Album",
        )
        
        needs_lyrics, needs_cover = handler.needs_processing(music)
        assert needs_lyrics is True
        assert needs_cover is True
    
    def test_needs_processing_existing_files(self, tmp_path):
        config = Config(download_lyrics=True, download_cover=True)
        handler = MetadataHandler(config)
        
        # Create existing files
        (tmp_path / "song.lrc").write_text("lyrics")
        (tmp_path / "cover.jpg").write_bytes(b"image")
        
        music = MusicFile(
            path=tmp_path / "song.mp3",
            artist="Artist",
            title="Song",
            album="Album",
        )
        
        needs_lyrics, needs_cover = handler.needs_processing(music)
        assert needs_lyrics is False
        assert needs_cover is False
    
    def test_save_lyrics(self, tmp_path):
        config = Config()
        handler = MetadataHandler(config)
        
        music = MusicFile(
            path=tmp_path / "song.mp3",
            artist="Artist",
            title="Song",
            album="Album",
        )
        
        result = handler.save_lyrics(music, "[00:00.00]歌词内容")
        assert result is True
        assert (tmp_path / "song.lrc").exists()
        assert "[00:00.00]歌词内容" in (tmp_path / "song.lrc").read_text()
    
    def test_save_cover(self, tmp_path):
        config = Config()
        handler = MetadataHandler(config)
        
        music = MusicFile(
            path=tmp_path / "song.mp3",
            artist="Artist",
            title="Song",
            album="Album",
        )
        
        result = handler.save_cover(music, b"fake image data")
        assert result is True
        assert (tmp_path / "cover.jpg").exists()


class TestIntegration:
    """Integration tests with real API (requires network)."""
    
    @pytest.mark.integration
    def test_search_real_api(self):
        """Test real API search - run with: pytest -m integration"""
        config = Config()
        client = TuneHubClient(config)
        
        results = client.search("周杰伦", "晴天")
        assert len(results) > 0
        assert any("晴天" in r.name for r in results)
        
        client.close()
    
    @pytest.mark.integration
    def test_get_lyrics_real_api(self):
        """Test real API lyrics fetch - run with: pytest -m integration"""
        config = Config()
        client = TuneHubClient(config)
        
        results = client.search("周杰伦", "晴天")
        if results:
            best = client.find_best_match(results, "周杰伦", "晴天")
            if best:
                lyrics = client.get_lyrics(best)
                assert lyrics is not None
                assert "[" in lyrics  # LRC format has timestamps
        
        client.close()
