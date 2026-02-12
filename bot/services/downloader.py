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

    async def get_info(self, url: str) -> Dict[str, Any]:
        """Get video information without downloading."""
        def _extract():
            with yt_dlp.YoutubeDL(self.ydl_opts_base) as ydl:
                return ydl.extract_info(url, download=False)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _extract)

    async def get_formats(self, url: str) -> List[Dict[str, Any]]:
        """Extract available formats."""
        info = await self.get_info(url)
        
    async def get_formats(self, url: str) -> List[Dict[str, Any]]:
        """Extract available formats or playlist items."""
        info = await self.get_info(url)
        
        # Check if it's a playlist/carousel
        if 'entries' in info:
            entries = info['entries']
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
                if not entry: continue
                # Determine type
                e_ext = entry.get('ext', 'unknown')
                e_res = entry.get('resolution') or f"{entry.get('width')}x{entry.get('height')}" or 'unknown'
                e_note = entry.get('title', f'Item {idx+1}')
                
                # We use specific format_id syntax: playlist_item:<index>
                options.append({
                     'format_id': f'playlist_item:{idx+1}',
                     'ext': e_ext,
                     'resolution': e_res,
                     'note': e_note,
                     'filesize': entry.get('filesize'),
                })
            return options

        # Standard Single Video/Image Logic
        formats = info.get('formats')
        
        # Fallback for direct video/image (Instagram images often land here)
        if not formats:
            if info.get('url'):
                formats = [info]

        if not formats:
            return []

        # Filter and process formats
        processed_formats = []
        seen = set()
        
        for f in formats:
            ext = f.get('ext', 'mp4')
            res = f.get('resolution') or f.get('height') or 'unknown'
            note = f.get('format_note', '')
            f_id = f.get('format_id', 'default')
            
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
            # Download specific item
            _, idx = format_id.split(':', 1)
            opts['playlist_items'] = idx
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
