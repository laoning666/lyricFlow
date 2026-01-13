# Configuration management
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration from environment variables."""
    
    # API Provider selection
    api_provider: str = "tunehub"  # "tunehub" or "lrcapi"
    
    # TuneHub API
    api_base_url: str = "https://music-dl.sayqz.com"
    
    # LrcApi settings
    lrcapi_url: str = "https://api.lrc.cx"  # LrcApi server URL
    lrcapi_auth: str = ""  # LrcApi authentication key (optional)
    
    # Scanning
    music_path: str = "/music"
    scan_interval_days: int = 0  # 0 = run once, >0 = interval in days
    
    # Download behavior (save as external files)
    download_lyrics: bool = True
    download_cover: bool = True
    overwrite_lyrics: bool = False
    overwrite_cover: bool = False
    
    # Update behavior (write to audio file metadata)
    update_lyrics: bool = False      # Write lyrics to audio metadata
    update_cover: bool = False       # Write cover to audio metadata
    update_basic_info: bool = False  # Write artist/title/album from API
    
    # Default artist (used when ID3 tag has no artist info and folder inference fails)
    default_artist: str = ""
    
    # Infer artist/album from folder structure: Artist/Album/song.mp3
    # If enabled, grandparent folder = artist, parent folder = album
    use_folder_structure: bool = True
    
    # Platforms priority for search
    platforms: list[str] = None
    
    # Supported audio extensions (including .strm for streaming files)
    audio_extensions: tuple[str, ...] = (".mp3", ".flac", ".m4a", ".wav", ".ogg", ".wma", ".ape", ".strm")
    
    def __post_init__(self):
        if self.platforms is None:
            self.platforms = ["netease", "kuwo", "qq"]
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        platforms_str = os.getenv("PLATFORMS", "netease,kuwo,qq")
        platforms = [p.strip() for p in platforms_str.split(",") if p.strip()]
        
        return cls(
            api_provider=os.getenv("API_PROVIDER", "tunehub"),
            api_base_url=os.getenv("API_BASE_URL", "https://music-dl.sayqz.com"),
            lrcapi_url=os.getenv("LRCAPI_URL", "https://api.lrc.cx"),
            lrcapi_auth=os.getenv("LRCAPI_AUTH", ""),
            music_path=os.getenv("MUSIC_PATH", "/music"),
            scan_interval_days=int(os.getenv("SCAN_INTERVAL_DAYS", "0")),
            download_lyrics=os.getenv("DOWNLOAD_LYRICS", "true").lower() == "true",
            download_cover=os.getenv("DOWNLOAD_COVER", "true").lower() == "true",
            overwrite_lyrics=os.getenv("OVERWRITE_LYRICS", "false").lower() == "true",
            overwrite_cover=os.getenv("OVERWRITE_COVER", "false").lower() == "true",
            update_lyrics=os.getenv("UPDATE_LYRICS", "false").lower() == "true",
            update_cover=os.getenv("UPDATE_COVER", "false").lower() == "true",
            update_basic_info=os.getenv("UPDATE_BASIC_INFO", "false").lower() == "true",
            default_artist=os.getenv("DEFAULT_ARTIST", ""),
            use_folder_structure=os.getenv("USE_FOLDER_STRUCTURE", "true").lower() == "true",
            platforms=platforms,
        )

