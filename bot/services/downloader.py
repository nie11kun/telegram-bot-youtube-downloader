import asyncio
import logging
import yt_dlp
from typing import Dict, List, Any
from bot.config import settings

logger = logging.getLogger(__name__)

class DownloadService:
    def __init__(self):
        self.ydl_opts_base = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': f'{settings.TEMP_DIR}/%(id)s_%(title)s.%(ext)s',
            'restrictfilenames': True,  # ASCII only filenames
            'cookiefile': 'cookies.txt',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            }
        }

    async def get_info(self, url: str, extra_opts: Dict = None) -> Dict[str, Any]:
        """Get video information without downloading."""
        def _extract():
            opts = self.ydl_opts_base.copy()
            if extra_opts:
                opts.update(extra_opts)
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _extract)

    async def get_formats(self, url: str) -> List[Dict[str, Any]]:
        """Extract available formats."""
        info = await self.get_info(url)
        
    async def get_formats(self, url: str) -> List[Dict[str, Any]]:
        """Extract available formats or playlist items."""
        logger.info(f"Fetching info for: {url}")
        info = await self.get_info(url)
        
        # Check if it's a playlist/carousel
        if 'entries' in info:
            entries = info['entries']
            
            # RETRY LOGIC: If entries empty, try extract_flat=True
            if not entries:
                logger.warning("Entries empty, retrying with extract_flat=True")
                info_flat = await self.get_info(url, {'extract_flat': True})
                entries = info_flat.get('entries', [])
            
            if entries:
                logger.info(f"Found playlist with {len(entries)} entries")
                options = []
                
                # Add "Download All" option
                options.append({
                    'format_id': 'playlist_all',
                    'ext': 'zip', # Conceptual
                    'resolution': f'{len(entries)} items',
                    'note': 'Download All',
                    'filesize': 0
                })
                
                # Add individual items
                for idx, entry in enumerate(entries):
                    if not entry: 
                        logger.warning(f"Entry {idx} is empty/None")
                        continue
                    
                    # Determine type
                    e_ext = entry.get('ext', 'unknown')
                    e_res = entry.get('resolution') or f"{entry.get('width')}x{entry.get('height')}" or 'unknown'
                    e_title = entry.get('title') or 'Unknown'
                    e_id = entry.get('id')
                    e_url = entry.get('url') # Crucial for flat extraction
                    
                    logger.info(f"Entry {idx}: id={e_id}, ext={e_ext}, res={e_res}, title={e_title}, url={e_url}")
                    
                    # Store URL in format_id if we used flat extraction (since indices might be unreliable or we prefer direct links)
                    # But download_video needs to handle it.
                    # Let's use a new prefix "playlist_url:" if we have a url, otherwise keep "playlist_item:"
                    
                    if e_url:
                        f_id_str = f'playlist_url:{e_url}'
                    else:
                        f_id_str = f'playlist_item:{idx+1}'

                    options.append({
                         'format_id': f_id_str,
                         'ext': e_ext,
                         'resolution': e_res,
                         'note': e_title,
                         'filesize': entry.get('filesize'),
                    })
                
                logger.info(f"Generated {len(options)} options from playlist")
                return options
        
        if 'entries' in info and not info.get('entries'):
             logger.warning("Found 'entries' key but it is still empty after retry. Falling back to single item logic.")

        # Standard Single Video/Image Logic
        formats = info.get('formats')
        logger.info(f"Single item. Formats present: {bool(formats)}")
        
        # Log keys to debug structure
        logger.info(f"Info Keys: {list(info.keys())}")
        
        # Fallback for direct video/image (Instagram images often land here)
        if not formats:
            if info.get('url'):
                logger.info("No formats, utilizing direct URL as metadata")
                formats = [info]
            elif info.get('thumbnails'):
                # Try to use best thumbnail as image source
                logger.info("No formats/url, checking thumbnails...")
                thumbnails = info.get('thumbnails', [])
                # Get the largest thumbnail
                if thumbnails:
                    best_thumb = thumbnails[-1] # Usually sorted, last is best
                    logger.info(f"Using best thumbnail as source: {best_thumb.get('url')}")
                    # Synthesize a format entry
                    synthetic_fmt = best_thumb.copy()
                    synthetic_fmt['ext'] = 'jpg' # Assume jpg if not present
                    if 'id' in best_thumb: synthetic_fmt['format_id'] = best_thumb['id']
                    else: synthetic_fmt['format_id'] = 'thumb_best'
                    
                    formats = [synthetic_fmt]

        if not formats:
            logger.warning("No formats and no direct URL found. Attempting Force Download option.")
            # Fallback: Offer a "Force Download" button using the URL itself
            # This relies on yt-dlp's download capability handling the URL better than extract_info
            return [{
                'format_id': 'force_download',
                'ext': 'unknown',
                'resolution': 'unknown',
                'note': 'Force Download (Blind)',
                'filesize': 0
            }]

        # Filter and process formats
        processed_formats = []
        seen = set()
        
        for f in formats:
            ext = f.get('ext', 'mp4')
            res = f.get('resolution') or f.get('height') or 'unknown'
            note = f.get('format_note', '')
            f_id = f.get('format_id', 'default')
            
            logger.info(f"Format: id={f_id}, ext={ext}, res={res}")
            
            # Basic deduplication
            key = (ext, res)
            if key not in seen and ext != 'mhtml': 
                 processed_formats.append({
                     'format_id': f_id,
                     'ext': ext,
                     'resolution': res,
                     'note': note,
                     'filesize': f.get('filesize'),
                     'vcodec': f.get('vcodec'),
                     'acodec': f.get('acodec')
                 })
                 seen.add(key)
                 
        logger.info(f"Returned {len(processed_formats)} processed single formats")
        return processed_formats

    async def download_video(self, url: str, format_id: str) -> List[str]:
        """
        Download video with specific format or playlist item.
        Returns the list of paths to the downloaded file(s).
        """
        opts = self.ydl_opts_base.copy()
        
        # Handle Playlist/Carousel logic
        if format_id == 'playlist_all':
            # Download all items
            opts['format'] = 'best' # Best for each item
            # No playlist_items constraint means download all
        elif format_id.startswith('playlist_item:'):
            # Download specific item by index
            _, idx = format_id.split(':', 1)
            opts['playlist_items'] = idx
            opts['format'] = 'best'
        elif format_id.startswith('playlist_url:'):
            # Download specific item by URL (from flat extraction)
            _, item_url = format_id.split(':', 1)
            # When downloading a specific child URL, we treat it as a new download
            url = item_url
            opts['format'] = 'best'
        elif format_id == 'force_download':
            # Blind download
            opts['format'] = 'best'
        else:
            # Standard single video format
            opts['format'] = format_id
        
        # Hook to capture filename(s)
        filename_collector = []
        def progress_hook(d):
            if d['status'] == 'finished':
                filename_collector.append(d['filename'])

        opts['progress_hooks'] = [progress_hook]

        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _download)
        
        if not filename_collector:
            raise Exception("Download finished but filename not captured.")
            
        return filename_collector

    async def download_best(self, url: str) -> str:
        """Download best format (default behavior)."""
        opts = self.ydl_opts_base.copy()
        
        filename_collector = []
        def progress_hook(d):
            if d['status'] == 'finished':
                filename_collector.append(d['filename'])
        opts['progress_hooks'] = [progress_hook]

        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _download)
        
        if not filename_collector:
             raise Exception("Download finished but filename not captured.")
        
        return filename_collector[0]
