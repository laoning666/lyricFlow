# Configuration management
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration from environment variables."""
    
    # TuneHub API
    api_base_url: str = "https://music-dl.sayqz.com"
    
    # Scanning
    music_path: str = "/music"
    scan_interval_days: int = 0  # 0 = run once, >0 = interval in days
    
    # Behavior
    overwrite_lyrics: bool = False
    overwrite_cover: bool = False
    download_lyrics: bool = True
    download_cover: bool = True
    
    # Default artist (used when ID3 tag has no artist info and folder inference fails)
    default_artist: str = ""
    
    # Infer artist/album from folder structure: Artist/Album/song.mp3
    # If enabled, grandparent folder = artist, parent folder = album
    use_folder_structure: bool = True
    
    # Platforms priority for search
    platforms: list[str] = None
    
    # Supported audio extensions
    audio_extensions: tuple[str, ...] = (".mp3", ".flac", ".m4a", ".wav", ".ogg", ".wma", ".ape")
    
    def __post_init__(self):
        if self.platforms is None:
            self.platforms = ["netease", "kuwo", "qq"]
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        platforms_str = os.getenv("PLATFORMS", "netease,kuwo,qq")
        platforms = [p.strip() for p in platforms_str.split(",") if p.strip()]
        
        return cls(
            api_base_url=os.getenv("API_BASE_URL", "https://music-dl.sayqz.com"),
            music_path=os.getenv("MUSIC_PATH", "/music"),
            scan_interval_days=int(os.getenv("SCAN_INTERVAL_DAYS", "0")),
            overwrite_lyrics=os.getenv("OVERWRITE_LYRICS", "false").lower() == "true",
            overwrite_cover=os.getenv("OVERWRITE_COVER", "false").lower() == "true",
            download_lyrics=os.getenv("DOWNLOAD_LYRICS", "true").lower() == "true",
            download_cover=os.getenv("DOWNLOAD_COVER", "true").lower() == "true",
            default_artist=os.getenv("DEFAULT_ARTIST", ""),
            use_folder_structure=os.getenv("USE_FOLDER_STRUCTURE", "true").lower() == "true",
            platforms=platforms,
        )
