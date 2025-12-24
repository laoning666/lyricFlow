#!/usr/bin/env python3
"""
Local test runner - test with a real music folder or mock data.
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.tunehub_client import TuneHubClient


def test_api_connection():
    """Test TuneHub API connectivity."""
    print("=" * 50)
    print("Testing TuneHub API Connection...")
    print("=" * 50)
    
    config = Config()
    client = TuneHubClient(config)
    
    try:
        # Test search
        print("\n1. Testing search for '周杰伦 晴天'...")
        results = client.search("周杰伦", "晴天")
        print(f"   Found {len(results)} results")
        
        if results:
            print("\n   Top 3 results:")
            for i, r in enumerate(results[:3]):
                print(f"   [{i+1}] {r.artist} - {r.name} ({r.platform})")
            
            # Test best match
            best = client.find_best_match(results, "周杰伦", "晴天")
            if best:
                print(f"\n2. Best match: {best.artist} - {best.name}")
                
                # Test lyrics
                print("\n3. Testing lyrics fetch...")
                lyrics = client.get_lyrics(best)
                if lyrics:
                    lines = lyrics.strip().split("\n")
                    print(f"   Got {len(lines)} lines of lyrics")
                    print(f"   First line: {lines[0][:50]}...")
                else:
                    print("   ✗ Failed to get lyrics")
                
                # Test cover
                print("\n4. Testing cover fetch...")
                cover = client.get_cover(best)
                if cover:
                    print(f"   Got cover image: {len(cover)} bytes")
                else:
                    print("   ✗ Failed to get cover")
        
        print("\n" + "=" * 50)
        print("✓ API connection test PASSED!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return False
    finally:
        client.close()
    
    return True


def test_with_folder(music_path: str):
    """Test with an actual music folder."""
    print("=" * 50)
    print(f"Testing with music folder: {music_path}")
    print("=" * 50)
    
    from src.scanner import MusicScanner
    from src.metadata_handler import MetadataHandler
    
    config = Config(
        music_path=music_path,
        download_lyrics=True,
        download_cover=True,
        overwrite_lyrics=False,
        overwrite_cover=False,
    )
    
    scanner = MusicScanner(config)
    client = TuneHubClient(config)
    handler = MetadataHandler(config)
    
    count = 0
    for music_file in scanner.scan():
        count += 1
        needs_lyrics, needs_cover = handler.needs_processing(music_file)
        
        status = []
        if needs_lyrics:
            status.append("needs lyrics")
        if needs_cover:
            status.append("needs cover")
        
        print(f"  [{count}] {music_file.artist} - {music_file.title}")
        print(f"      Path: {music_file.path}")
        print(f"      Status: {', '.join(status) if status else 'already complete'}")
        
        if count >= 10:
            print(f"\n  ... and more (showing first 10 only)")
            break
    
    print(f"\nTotal files found: {count}")
    client.close()


def main():
    print("\n🎵 TuneHub Music Metadata Tool - Local Test\n")
    
    # Check if music path provided
    if len(sys.argv) > 1:
        music_path = sys.argv[1]
        if os.path.isdir(music_path):
            test_with_folder(music_path)
        else:
            print(f"Error: Directory not found: {music_path}")
            sys.exit(1)
    else:
        # Just test API connection
        if not test_api_connection():
            sys.exit(1)
    
    print("\n💡 To test with your music folder:")
    print("   python test_local.py /path/to/your/music")
    print("\n💡 To run full tool:")
    print("   MUSIC_PATH=/path/to/music python -m src.main")


if __name__ == "__main__":
    main()
