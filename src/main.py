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
        
        # Statistics
        self.stats = {
            "scanned": 0,
            "lyrics_downloaded": 0,
            "covers_downloaded": 0,
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
        
        for music_file in self.scanner.scan():
            self.stats["scanned"] += 1
            
            # Check what needs processing
            needs_lyrics, needs_cover = self.handler.needs_processing(music_file)
            
            # Skip if cover already processed for this directory
            if music_file.path.parent in processed_dirs:
                needs_cover = False
            
            if not needs_lyrics and not needs_cover:
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
            
            # Download and save lyrics
            if needs_lyrics:
                lyrics = self.client.get_lyrics(best)
                if lyrics and self.handler.save_lyrics(music_file, lyrics):
                    self.stats["lyrics_downloaded"] += 1
            
            # Download and save cover (once per directory)
            if needs_cover:
                cover = self.client.get_cover(best)
                if cover and self.handler.save_cover(music_file, cover):
                    self.stats["covers_downloaded"] += 1
                    processed_dirs.add(music_file.path.parent)
            
            # Small delay to be nice to the API
            time.sleep(0.2)
    
    def _print_stats(self):
        """Print processing statistics."""
        logger.info("=" * 50)
        logger.info("Processing Complete!")
        logger.info(f"  Scanned:    {self.stats['scanned']} files")
        logger.info(f"  Lyrics:     {self.stats['lyrics_downloaded']} downloaded")
        logger.info(f"  Covers:     {self.stats['covers_downloaded']} downloaded")
        logger.info(f"  Skipped:    {self.stats['skipped']} (already exists)")
        logger.info(f"  Failed:     {self.stats['failed']} (no match)")
        logger.info("=" * 50)


def main():
    """Main entry point."""
    config = Config.from_env()
    tool = LyricFlow(config)
    
    if config.scan_interval > 0:
        # Continuous mode with interval
        logger.info(f"Running in continuous mode, interval: {config.scan_interval}s")
        while True:
            tool.run()
            logger.info(f"Sleeping for {config.scan_interval} seconds...")
            time.sleep(config.scan_interval)
            # Reset stats for next run
            tool.stats = {k: 0 for k in tool.stats}
    else:
        # One-time run
        tool.run()


if __name__ == "__main__":
    main()
