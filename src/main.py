#!/usr/bin/env python3
"""
LyricFlow - Music Metadata Tool

Automatically download lyrics and album covers for your music library.
"""
import sys
import time
import logging
from .config import Config
from .scanner import MusicScanner
from .tunehub_client import TuneHubClient
from .metadata_handler import MetadataHandler
from .embed_handler import EmbedHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class LyricFlow:
    """Main application class."""
    
    def __init__(self, config: Config):
        self.config = config
        self.scanner = MusicScanner(config)
        self.client = TuneHubClient(config)
        self.handler = MetadataHandler(config)
        self.embedder = EmbedHandler(config)
        
        # Statistics
        self.stats = {
            "scanned": 0,
            "lyrics_saved": 0,
            "covers_saved": 0,
            "lyrics_updated": 0,
            "covers_updated": 0,
            "info_updated": 0,
            "skipped": 0,
            "failed": 0,
        }
    
    def run(self):
        """Run the metadata tool."""
        logger.info("=" * 50)
        logger.info("LyricFlow - Music Metadata Tool")
        logger.info("=" * 50)
        logger.info(f"Music path: {self.config.music_path}")
        logger.info(f"Download lyrics: {self.config.download_lyrics}")
        logger.info(f"Download covers: {self.config.download_cover}")
        logger.info(f"Update lyrics: {self.config.update_lyrics}")
        logger.info(f"Update covers: {self.config.update_cover}")
        logger.info(f"Update basic info: {self.config.update_basic_info}")
        logger.info(f"Platforms: {', '.join(self.config.platforms)}")
        logger.info("=" * 50)
        
        try:
            self._process_all()
        finally:
            self.client.close()
            self._print_stats()
    
    def _process_all(self):
        """Process all music files."""
        # Track which directories have been processed for covers
        processed_dirs = set()
        embedded_dirs = set()  # Track dirs with embedded covers
        
        for music_file in self.scanner.scan():
            self.stats["scanned"] += 1
            
            # Check what needs processing (file saving)
            needs_lyrics, needs_cover = self.handler.needs_processing(music_file)
            
            # Check what needs updating (write to audio metadata)
            # When UPDATE_*=true and FORCE_UPDATE_*=true, always update (overwrite)
            # When UPDATE_*=true and FORCE_UPDATE_*=false, only update if no existing metadata
            needs_update_lyrics = self.config.update_lyrics
            needs_update_cover = self.config.update_cover
            needs_update_basic_info = self.config.update_basic_info
            
            # If force_update is false, check if metadata already exists
            if needs_update_lyrics and not self.config.force_update_lyrics:
                if not music_file.is_strm and self.embedder.has_embedded_lyrics(music_file):
                    needs_update_lyrics = False
                    logger.debug(f"Skipping lyrics update (already exists): {music_file.path.name}")
            
            if needs_update_cover and not self.config.force_update_cover:
                if not music_file.is_strm and self.embedder.has_embedded_cover(music_file):
                    needs_update_cover = False
                    logger.debug(f"Skipping cover update (already exists): {music_file.path.name}")
            
            if needs_update_basic_info and not self.config.force_update_basic_info:
                if not music_file.is_strm and self.embedder.has_basic_info(music_file):
                    needs_update_basic_info = False
                    logger.debug(f"Skipping basic info update (already exists): {music_file.path.name}")
            
            # Skip if cover already processed for this directory
            if music_file.path.parent in processed_dirs:
                needs_cover = False
            
            # Check if anything needs processing
            if not any([needs_lyrics, needs_cover, needs_update_lyrics, needs_update_cover, needs_update_basic_info]):
                self.stats["skipped"] += 1
                continue
            
            # Search for the song
            results = self.client.search(music_file.artist, music_file.title)
            if not results:
                logger.warning(f"✗ No results: {music_file.artist} - {music_file.title}")
                self.stats["failed"] += 1
                continue
            
            # Find best match
            best = self.client.find_best_match(results, music_file.artist, music_file.title)
            if not best:
                self.stats["failed"] += 1
                continue
            
            # Update basic metadata from API (artist, title, album)
            # Skip for STRM files (they are text files, cannot embed metadata)
            if needs_update_basic_info and not music_file.is_strm:
                if self.embedder.update_basic_info(
                    music_file, best.artist, best.name, best.album
                ):
                    self.stats["info_updated"] += 1
            elif needs_update_basic_info and music_file.is_strm:
                logger.debug(f"Skipping basic info embed for STRM file: {music_file.path.name}")
            
            # Handle lyrics (download once, use for both saving and updating)
            lyrics = None
            if needs_lyrics or needs_update_lyrics:
                lyrics = self.client.get_lyrics(best)
                
                if lyrics:
                    # Save to file
                    if needs_lyrics and self.handler.save_lyrics(music_file, lyrics):
                        self.stats["lyrics_saved"] += 1
                    
                    # Update in metadata (skip for STRM files)
                    if needs_update_lyrics and not music_file.is_strm and self.embedder.embed_lyrics(music_file, lyrics):
                        self.stats["lyrics_updated"] += 1
                    elif needs_update_lyrics and music_file.is_strm:
                        logger.debug(f"Skipping lyrics embed for STRM file: {music_file.path.name}")
            
            # Handle cover (download once, use for both saving and updating)
            cover = None
            if needs_cover or needs_update_cover:
                cover = self.client.get_cover(best)
                
                if cover:
                    # Save to file (once per directory)
                    if needs_cover and self.handler.save_cover(music_file, cover):
                        self.stats["covers_saved"] += 1
                        processed_dirs.add(music_file.path.parent)
                    
                    # Update in metadata (for each file, skip for STRM)
                    if needs_update_cover and not music_file.is_strm and self.embedder.embed_cover(music_file, cover):
                        self.stats["covers_updated"] += 1
                    elif needs_update_cover and music_file.is_strm:
                        logger.debug(f"Skipping cover embed for STRM file: {music_file.path.name}")
            
            # Small delay to be nice to the API
            time.sleep(0.2)
    
    def _print_stats(self):
        """Print processing statistics."""
        logger.info("=" * 50)
        logger.info("Processing Complete!")
        logger.info(f"  Scanned:         {self.stats['scanned']} files")
        logger.info(f"  Lyrics saved:    {self.stats['lyrics_saved']}")
        logger.info(f"  Covers saved:    {self.stats['covers_saved']}")
        logger.info(f"  Lyrics updated:  {self.stats['lyrics_updated']}")
        logger.info(f"  Covers updated:  {self.stats['covers_updated']}")
        logger.info(f"  Info updated:    {self.stats['info_updated']}")
        logger.info(f"  Skipped:         {self.stats['skipped']} (already exists)")
        logger.info(f"  Failed:          {self.stats['failed']} (no match)")
        logger.info("=" * 50)


def main():
    """Main entry point."""
    config = Config.from_env()
    tool = LyricFlow(config)
    
    if config.scan_interval_days > 0:
        # Continuous mode with interval
        interval_seconds = config.scan_interval_days * 24 * 60 * 60
        logger.info(f"Running in continuous mode, interval: {config.scan_interval_days} day(s)")
        while True:
            tool.run()
            logger.info(f"Sleeping for {config.scan_interval_days} day(s)...")
            time.sleep(interval_seconds)
            # Reset stats for next run
            tool.stats = {k: 0 for k in tool.stats}
    else:
        # One-time run
        tool.run()


if __name__ == "__main__":
    main()
