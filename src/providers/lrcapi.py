# LrcApi Provider
import httpx
import logging
from typing import Optional
from urllib.parse import urlencode
from .base import LyricsProviderBase, SearchResult
from ..config import Config

logger = logging.getLogger(__name__)


class LrcApiProvider(LyricsProviderBase):
    """Provider for LrcApi.
    
    LrcApi is a Flask API for lyrics and cover search.
    Project: https://github.com/HisAtri/LrcApi
    Documentation: https://docs.lrc.cx/
    
    This provider uses the legacy API endpoints:
    - /lyrics - Get lyrics (returns LRC text directly)
    - /cover - Get cover image (returns image or redirect)
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.lrcapi_url.rstrip("/")
        self.auth_key = config.lrcapi_auth
        self.client = httpx.Client(timeout=30.0, follow_redirects=True)
    
    def _get_headers(self) -> dict:
        """Get request headers with optional authentication."""
        headers = {}
        if self.auth_key:
            headers["Authorization"] = self.auth_key
        return headers
    
    def search(self, artist: str, title: str, album: str = "") -> list[SearchResult]:
        """
        Search for a song using LrcApi.
        
        LrcApi doesn't have a separate search endpoint - it directly returns
        lyrics/cover for the given parameters. We create a synthetic SearchResult
        that holds the search parameters for later use in get_lyrics/get_cover.
        """
        if not title:
            return []
        
        # Create a synthetic result that holds the search parameters
        # LrcApi will use these parameters directly when fetching lyrics/cover
        result = SearchResult(
            id=f"{artist}_{title}_{album}",
            name=title,
            artist=artist,
            album=album,
            platform="lrcapi",
            lrc_url="",  # Will be constructed when fetching
            pic_url="",  # Will be constructed when fetching
        )
        
        logger.info(f"LrcApi search: {artist} - {title}")
        return [result]
    
    def get_lyrics(self, result: SearchResult) -> Optional[str]:
        """
        Fetch lyrics from LrcApi.
        
        Uses /lyrics endpoint with title and artist parameters.
        Returns LRC format text directly.
        """
        try:
            params = {}
            if result.name:
                params["title"] = result.name
            if result.artist:
                params["artist"] = result.artist
            
            url = f"{self.base_url}/lyrics"
            logger.info(f"Fetching lyrics from LrcApi: {result.artist} - {result.name}")
            
            response = self.client.get(
                url,
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            content = response.text
            # Check if it's valid LRC content (should contain timestamps like [00:00.00])
            if content and "[" in content and not content.startswith("{"):
                return content
            
            logger.warning(f"LrcApi returned invalid lyrics for {result.name}")
            return None
            
        except httpx.HTTPStatusError as e:
            logger.error(f"LrcApi lyrics request failed with status {e.response.status_code}: {result.name}")
            return None
        except Exception as e:
            logger.error(f"Failed to get lyrics from LrcApi for {result.name}: {e}")
            return None
    
    def get_cover(self, result: SearchResult) -> Optional[bytes]:
        """
        Fetch cover image from LrcApi.
        
        Uses /cover endpoint with title, album, and artist parameters.
        - title + album + artist: Get song cover
        - album + artist: Get album cover
        - artist only: Get artist avatar
        """
        try:
            params = {}
            if result.name:
                params["title"] = result.name
            if result.album:
                params["album"] = result.album
            if result.artist:
                params["artist"] = result.artist
            
            url = f"{self.base_url}/cover"
            logger.info(f"Fetching cover from LrcApi: {result.artist} - {result.name}")
            
            response = self.client.get(
                url,
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            content_type = response.headers.get("content-type", "")
            if "image" in content_type or len(response.content) > 1000:
                return response.content
            
            logger.warning(f"LrcApi returned non-image content for {result.name}")
            return None
            
        except httpx.HTTPStatusError as e:
            logger.error(f"LrcApi cover request failed with status {e.response.status_code}: {result.name}")
            return None
        except Exception as e:
            logger.error(f"Failed to get cover from LrcApi for {result.name}: {e}")
            return None
    
    def find_best_match(
        self,
        results: list[SearchResult],
        artist: str,
        title: str
    ) -> Optional[SearchResult]:
        """
        Find the best matching result.
        
        For LrcApi, we only have one synthetic result from search(),
        so we simply return it if available.
        """
        if not results:
            return None
        return results[0]
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
