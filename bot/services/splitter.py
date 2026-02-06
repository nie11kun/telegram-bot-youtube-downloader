import os
import asyncio
import logging
import math
from bot.config import settings

logger = logging.getLogger(__name__)

class MediaProcessor:
    async def get_video_duration(self, file_path: str) -> float:
        """Get video duration using ffprobe."""
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            file_path
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            logger.error(f"FFprobe failed: {stderr.decode()}")
            raise Exception("Failed to get video duration")
            
        try:
            return float(stdout.decode().strip())
        except ValueError:
            return 0.0

    async def split_file(self, file_path: str, chunk_size_bytes: int = settings.MAX_FILE_SIZE) -> list[str]:
        """
        Split file into chunks less than chunk_size_bytes.
        Returns list of paths to chunks.
        """
        file_size = os.path.getsize(file_path)
        
        if file_size <= chunk_size_bytes:
            return [file_path]
            
        logger.info(f"File {file_path} ({file_size} bytes) exceeds limit {chunk_size_bytes}. Splitting...")
        
        duration = await self.get_video_duration(file_path)
        if duration == 0:
             # Fallback to binary split if duration unknown? 
             # Telegram requires video parts to be playable. Binary split breaks headers.
             # We must fail or try a safe split.
             logger.warning("Could not determine duration, cannot split safely by time.")
             # For this implementation, we simply return the original and let Telegram fail or user handle.
             # Or we could return None to signal failure.
             raise Exception("Cannot split file: unable to determine duration.")

        # Calculate split duration
        # Heuristic: file_size / duration = bitrate (bytes/sec)
        # target_duration = chunk_size / bitrate
        avg_bitrate = file_size / duration
        # Safety factor 0.95 to account for variable bitrate spikes
        split_duration = (chunk_size_bytes / avg_bitrate) * 0.95
        
        num_parts = math.ceil(duration / split_duration)
        
        base_name, ext = os.path.splitext(file_path)
        output_files = []
        
        for i in range(num_parts):
            start_time = i * split_duration
            part_path = f"{base_name}_part{i+1}{ext}"
            
            # -ss before -i is faster / different seeking
            # -c copy is fast but might not be accurate for cutting. 
            # Re-encoding is slow. Telegram supports safe cutting with -c copy if keyframes align?
            # We'll use -c copy for speed, understanding it might be imprecise.
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start_time),
                "-t", str(split_duration),
                "-i", file_path,
                "-c", "copy",
                part_path
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                logger.error(f"FFmpeg split failed: {stderr.decode()}")
                # cleanup?
                raise Exception("FFmpeg split failed")
            
            output_files.append(part_path)
            
        return output_files
