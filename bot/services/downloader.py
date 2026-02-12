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
        
        formats = info.get('formats')
        if not formats:
            # Fallback for direct video or missing formats
            if info.get('url'):
                formats = [info]
            elif 'entries' in info:
                # For playlists/carousels, just take first entry for now to correctly error or handle?
                # or technically we should download all? 
                # Current logic implies 1 link = 1 selection. 
                # Let's try to flatten entries?
                # Ideally we returns formats for all? No, too messy.
                # Just take the first video.
                if info['entries']:
                    formats = info['entries'][0].get('formats') or [info['entries'][0]]

        if not formats:
            return []

        # Filter and process formats
        processed_formats = []
        seen = set()
        
        for f in formats:
            ext = f.get('ext', 'mp4')
            res = f.get('resolution') or f.get('height') or 'unknown'
            note = f.get('format_note', '')
            f_id = f.get('format_id', 'default') # Default ID if missing
            
            # Basic deduplication similar to original logic
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

    async def download_video(self, url: str, format_id: str) -> str:
        """
        Download video with specific format.
        Returns the path to the downloaded file.
        """
        opts = self.ydl_opts_base.copy()
        opts['format'] = format_id
        
        # Hook to capture filename
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
