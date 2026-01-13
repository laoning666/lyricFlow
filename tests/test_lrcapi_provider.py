"""
Tests for LrcApi Provider
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.config import Config
from src.providers.base import LyricsProviderBase, SearchResult
from src.providers.lrcapi import LrcApiProvider
from src.providers.tunehub import TuneHubProvider
from src.providers import get_provider


class TestProviderFactory:
    """Test provider factory function."""
    
    def test_get_provider_default_tunehub(self):
        """Default provider should be TuneHub."""
        config = Config()
        provider = get_provider(config)
        assert isinstance(provider, TuneHubProvider)
        provider.close()
    
    def test_get_provider_tunehub(self):
        """Explicit TuneHub provider selection."""
        config = Config(api_provider="tunehub")
        provider = get_provider(config)
        assert isinstance(provider, TuneHubProvider)
        provider.close()
    
    def test_get_provider_lrcapi(self):
        """LrcApi provider selection."""
        config = Config(api_provider="lrcapi")
        provider = get_provider(config)
        assert isinstance(provider, LrcApiProvider)
        provider.close()
    
    def test_get_provider_lrcapi_case_insensitive(self):
        """Provider selection should be case insensitive."""
        config = Config(api_provider="LrcApi")
        provider = get_provider(config)
        assert isinstance(provider, LrcApiProvider)
        provider.close()


class TestLrcApiProviderConfig:
    """Test LrcApi provider configuration."""

    def test_lrcapi_config_defaults(self):
        """Test default LrcApi configuration values."""
        config = Config()
        assert config.api_provider == "tunehub"
        assert config.lrcapi_url == "https://api.lrc.cx"
        assert config.lrcapi_auth == ""
    
    def test_lrcapi_config_from_env(self):
        """Test LrcApi configuration from environment variables."""
        with patch.dict("os.environ", {
            "API_PROVIDER": "lrcapi",
            "LRCAPI_URL": "http://192.168.1.100:28883",
            "LRCAPI_AUTH": "test_auth_key",
        }):
            config = Config.from_env()
            assert config.api_provider == "lrcapi"
            assert config.lrcapi_url == "http://192.168.1.100:28883"
            assert config.lrcapi_auth == "test_auth_key"


class TestLrcApiProvider:
    """Test LrcApi provider implementation."""
    
    def test_init(self):
        """Test provider initialization."""
        config = Config(
            api_provider="lrcapi",
            lrcapi_url="http://test.example.com:28883",
            lrcapi_auth="test_key"
        )
        provider = LrcApiProvider(config)
        assert provider.base_url == "http://test.example.com:28883"
        assert provider.auth_key == "test_key"
        provider.close()
    
    def test_init_strips_trailing_slash(self):
        """URL trailing slash should be stripped."""
        config = Config(
            lrcapi_url="http://test.example.com:28883/"
        )
        provider = LrcApiProvider(config)
        assert provider.base_url == "http://test.example.com:28883"
        provider.close()
    
    def test_get_headers_with_auth(self):
        """Headers should include Authorization when auth key is set."""
        config = Config(lrcapi_auth="my_secret_key")
        provider = LrcApiProvider(config)
        headers = provider._get_headers()
        assert headers["Authorization"] == "my_secret_key"
        provider.close()
    
    def test_get_headers_without_auth(self):
        """Headers should be empty when no auth key is set."""
        config = Config(lrcapi_auth="")
        provider = LrcApiProvider(config)
        headers = provider._get_headers()
        assert "Authorization" not in headers
        provider.close()
    
    def test_search_returns_synthetic_result(self):
        """Search should return a synthetic SearchResult with the query params."""
        config = Config()
        provider = LrcApiProvider(config)
        
        results = provider.search("Taylor Swift", "Love Story", "Fearless")
        
        assert len(results) == 1
        result = results[0]
        assert result.name == "Love Story"
        assert result.artist == "Taylor Swift"
        assert result.album == "Fearless"
        assert result.platform == "lrcapi"
        provider.close()
    
    def test_search_empty_title_returns_empty(self):
        """Search with empty title should return empty list."""
        config = Config()
        provider = LrcApiProvider(config)
        
        results = provider.search("Taylor Swift", "", "")
        
        assert results == []
        provider.close()
    
    def test_find_best_match_returns_first(self):
        """find_best_match should return the first result."""
        config = Config()
        provider = LrcApiProvider(config)
        
        results = [
            SearchResult("1", "Song1", "Artist1", "Album1", "lrcapi", "", ""),
            SearchResult("2", "Song2", "Artist2", "Album2", "lrcapi", "", ""),
        ]
        
        best = provider.find_best_match(results, "Artist1", "Song1")
        assert best.id == "1"
        provider.close()
    
    def test_find_best_match_empty_returns_none(self):
        """find_best_match with empty list should return None."""
        config = Config()
        provider = LrcApiProvider(config)
        
        best = provider.find_best_match([], "Artist", "Title")
        assert best is None
        provider.close()


class TestLrcApiProviderMocked:
    """Test LrcApi provider with mocked HTTP responses."""
    
    def test_get_lyrics_success(self):
        """Test successful lyrics fetch."""
        config = Config(
            lrcapi_url="http://test.example.com",
            lrcapi_auth="test_key"
        )
        provider = LrcApiProvider(config)
        
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.text = "[00:00.00]Test lyrics content\n[00:05.00]Line 2"
        mock_response.raise_for_status = Mock()
        
        with patch.object(provider.client, 'get', return_value=mock_response) as mock_get:
            result = SearchResult("1", "Test Song", "Test Artist", "Test Album", "lrcapi", "", "")
            lyrics = provider.get_lyrics(result)
            
            assert lyrics == "[00:00.00]Test lyrics content\n[00:05.00]Line 2"
            mock_get.assert_called_once()
            # Check that auth header was included
            call_kwargs = mock_get.call_args[1]
            assert call_kwargs["headers"]["Authorization"] == "test_key"
        
        provider.close()
    
    def test_get_lyrics_invalid_response(self):
        """Test lyrics fetch with invalid response (no LRC format)."""
        config = Config()
        provider = LrcApiProvider(config)
        
        mock_response = Mock()
        mock_response.text = '{"error": "not found"}'  # JSON error response
        mock_response.raise_for_status = Mock()
        
        with patch.object(provider.client, 'get', return_value=mock_response):
            result = SearchResult("1", "Test", "Test", "", "lrcapi", "", "")
            lyrics = provider.get_lyrics(result)
            
            assert lyrics is None
        
        provider.close()
    
    def test_get_cover_success(self):
        """Test successful cover fetch."""
        config = Config()
        provider = LrcApiProvider(config)
        
        mock_response = Mock()
        mock_response.content = b"\xff\xd8\xff\xe0" + b"x" * 5000  # Fake JPEG data
        mock_response.headers = {"content-type": "image/jpeg"}
        mock_response.raise_for_status = Mock()
        
        with patch.object(provider.client, 'get', return_value=mock_response):
            result = SearchResult("1", "Test", "Test Artist", "Test Album", "lrcapi", "", "")
            cover = provider.get_cover(result)
            
            assert cover is not None
            assert len(cover) > 1000
        
        provider.close()
    
    def test_get_cover_non_image_response(self):
        """Test cover fetch with non-image response."""
        config = Config()
        provider = LrcApiProvider(config)
        
        mock_response = Mock()
        mock_response.content = b"error"  # Small non-image response
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = Mock()
        
        with patch.object(provider.client, 'get', return_value=mock_response):
            result = SearchResult("1", "Test", "Test", "", "lrcapi", "", "")
            cover = provider.get_cover(result)
            
            assert cover is None
        
        provider.close()


class TestSearchResult:
    """Test SearchResult from providers.base."""
    
    def test_from_dict(self):
        """Test creating SearchResult from dictionary."""
        data = {
            "id": "123",
            "name": "Test Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "platform": "lrcapi",
            "lrc": "http://example.com/lrc",
            "pic": "http://example.com/pic",
        }
        result = SearchResult.from_dict(data)
        
        assert result.id == "123"
        assert result.name == "Test Song"
        assert result.artist == "Test Artist"
        assert result.album == "Test Album"
        assert result.platform == "lrcapi"
        assert result.lrc_url == "http://example.com/lrc"
        assert result.pic_url == "http://example.com/pic"
    
    def test_from_dict_missing_fields(self):
        """Test creating SearchResult with missing fields."""
        data = {"name": "Test Song"}
        result = SearchResult.from_dict(data)
        
        assert result.name == "Test Song"
        assert result.id == ""
        assert result.artist == ""
        assert result.album == ""


@pytest.mark.integration
class TestLrcApiIntegration:
    """Integration tests for LrcApi provider (requires network)."""
    
    def test_get_lyrics_public_api(self):
        """Test lyrics fetch from public LrcApi."""
        config = Config(
            api_provider="lrcapi",
            lrcapi_url="https://api.lrc.cx"
        )
        provider = LrcApiProvider(config)
        
        try:
            results = provider.search("Taylor Swift", "Love Story")
            assert len(results) > 0
            
            lyrics = provider.get_lyrics(results[0])
            assert lyrics is not None
            assert "[" in lyrics  # LRC format has timestamps
        finally:
            provider.close()
    
    def test_get_cover_public_api(self):
        """Test cover fetch from public LrcApi."""
        config = Config(
            api_provider="lrcapi",
            lrcapi_url="https://api.lrc.cx"
        )
        provider = LrcApiProvider(config)
        
        try:
            results = provider.search("Taylor Swift", "Love Story", "Fearless")
            assert len(results) > 0
            
            cover = provider.get_cover(results[0])
            assert cover is not None
            assert len(cover) > 1000  # Should be a reasonable image size
        finally:
            provider.close()
