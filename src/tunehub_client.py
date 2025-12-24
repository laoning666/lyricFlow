# TuneHub API Client
import httpx
import logging
from dataclasses import dataclass
from typing import Optional
from .config import Config

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result from TuneHub API."""
    id: str
    name: str
    artist: str
    album: str
    platform: str
    lrc_url: str
    pic_url: str
    
    @classmethod
    def from_dict(cls, data: dict) -> "SearchResult":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            artist=data.get("artist", ""),
            album=data.get("album", ""),
            platform=data.get("platform", ""),
            lrc_url=data.get("lrc", ""),
            pic_url=data.get("pic", ""),
        )


class TuneHubClient:
    """Client for TuneHub API."""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.api_base_url
        self.client = httpx.Client(timeout=30.0, follow_redirects=True)
    
    def search(self, artist: str, title: str) -> list[SearchResult]:
        """
        Search for a song using aggregate search.
        Returns list of matching results from all platforms.
        """
        keyword = f"{artist} {title}".strip()
        if not keyword:
            return []
        
        try:
            url = f"{self.base_url}/api/"
            params = {
                "type": "aggregateSearch",
                "keyword": keyword,
            }
            
            logger.info(f"Searching for: {keyword}")
            response = self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") != 200:
                logger.warning(f"API returned non-200 code: {data}")
                return []
            
            results = data.get("data", {}).get("results", [])
            return [SearchResult.from_dict(r) for r in results]
            
        except Exception as e:
            logger.error(f"Search failed for '{keyword}': {e}")
            return []
    
    def get_lyrics(self, result: SearchResult) -> Optional[str]:
        """
        Fetch lyrics content for a search result.
        Returns LRC format lyrics string or None.
        """
        try:
            logger.info(f"Fetching lyrics from {result.platform}: {result.name}")
            response = self.client.get(result.lrc_url)
            response.raise_for_status()
            
            # LRC is returned as plain text
            content = response.text
            if content and not content.startswith("{"):  # Not an error JSON
                return content
            return None
            
        except Exception as e:
            logger.error(f"Failed to get lyrics for {result.name}: {e}")
            return None
    
    def get_cover(self, result: SearchResult) -> Optional[bytes]:
        """
        Fetch album cover image for a search result.
        Returns image bytes or None.
        """
        try:
            logger.info(f"Fetching cover from {result.platform}: {result.name}")
            response = self.client.get(result.pic_url)
            response.raise_for_status()
            
            content_type = response.headers.get("content-type", "")
            if "image" in content_type or len(response.content) > 1000:
                return response.content
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cover for {result.name}: {e}")
            return None
    
    def find_best_match(
        self, 
        results: list[SearchResult], 
        artist: str, 
        title: str
    ) -> Optional[SearchResult]:
        """
        Find the best matching result from search results.
        Prioritizes exact matches and preferred platforms.
        """
        if not results:
            return None
        
        artist_lower = artist.lower()
        title_lower = title.lower()
        
        # Score each result
        scored = []
        for r in results:
            score = 0
            r_artist = r.artist.lower()
            r_name = r.name.lower()
            
            # Exact title match
            if r_name == title_lower:
                score += 100
            elif title_lower in r_name:
                score += 50
            
            # Artist match
            if artist_lower in r_artist or r_artist in artist_lower:
                score += 30
            
            # Platform priority
            try:
                platform_idx = self.config.platforms.index(r.platform)
                score += (10 - platform_idx)
            except ValueError:
                pass
            
            scored.append((score, r))
        
        # Return highest scored result
        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best_result = scored[0]
        
        # Require minimum score to avoid bad matches
        if best_score >= 30:
            return best_result
        
        logger.warning(f"No good match found for {artist} - {title}")
        return None
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
