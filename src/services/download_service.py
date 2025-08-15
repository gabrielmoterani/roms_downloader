"""
Download Service
Handles downloading of ROM files with progress tracking and resume capability
"""

import os
import requests
import threading
import time
from typing import Dict, List, Callable, Optional, Tuple
from urllib.parse import urljoin, urlparse
from zipfile import ZipFile
import tempfile
from .nsz_service import NSZService


class DownloadTask:
    """Represents a single download task"""
    
    def __init__(self, url: str, filename: str, destination: str):
        self.url = url
        self.filename = filename
        self.destination = destination
        self.status = "pending"  # pending, downloading, completed, failed, paused
        self.progress = 0.0  # 0.0 to 100.0
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.speed = 0.0  # bytes per second
        self.error_message = ""
        self.start_time = None
        self.end_time = None
        
    def get_output_path(self) -> str:
        """Get the full output path for this download"""
        return os.path.join(self.destination, self.filename)


class DownloadService:
    """Service for managing ROM file downloads"""
    
    def __init__(self):
        self.downloads: Dict[str, DownloadTask] = {}
        self.active_downloads = 0
        self.max_concurrent_downloads = 3
        self.download_threads = {}
        self.progress_callbacks: List[Callable] = []
        self.status_callbacks: List[Callable] = []
        self.nsz_service = NSZService()
        
    def add_progress_callback(self, callback: Callable):
        """Add a callback function for progress updates"""
        self.progress_callbacks.append(callback)
        
    def add_status_callback(self, callback: Callable):
        """Add a callback function for status updates"""
        self.status_callbacks.append(callback)
        
    def _notify_progress(self, task_id: str, task: DownloadTask):
        """Notify all progress callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(task_id, task)
            except Exception:
                pass  # Ignore callback errors
                
    def _notify_status(self, task_id: str, status: str, message: str = ""):
        """Notify all status callbacks"""
        for callback in self.status_callbacks:
            try:
                callback(task_id, status, message)
            except Exception:
                pass  # Ignore callback errors
    
    def add_download(self, url: str, filename: str, destination: str) -> str:
        """
        Add a new download task
        
        Args:
            url: URL to download from
            filename: Name for the downloaded file
            destination: Directory to save the file
            
        Returns:
            Unique task ID for this download
        """
        # Create unique task ID
        task_id = f"{filename}_{int(time.time())}"
        
        # Ensure destination directory exists
        os.makedirs(destination, exist_ok=True)
        
        # Create download task
        task = DownloadTask(url, filename, destination)
        self.downloads[task_id] = task
        
        self._notify_status(task_id, "added", f"Added download: {filename}")
        return task_id
    
    def add_game_downloads(self, games_data: List[Dict], system_data: Dict, base_download_dir: str) -> List[str]:
        """
        Add multiple game downloads from system configuration
        
        Args:
            games_data: List of game data dictionaries
            system_data: System configuration data
            base_download_dir: Base directory for downloads
            
        Returns:
            List of task IDs for the added downloads
        """
        task_ids = []
        
        # Create system-specific download directory
        system_folder = system_data.get('roms_folder', 'unknown_system')
        system_download_dir = os.path.join(base_download_dir, system_folder)
        
        for game in games_data:
            # Extract game information based on data structure
            if isinstance(game, dict):
                if 'filename' in game:
                    filename = game['filename']
                    url = game.get('url', game.get('href', ''))
                elif 'name' in game:
                    filename = game['name']
                    url = game.get('url', game.get('href', ''))
                else:
                    continue  # Skip invalid game data
            else:
                # Handle string-based game data
                filename = str(game)
                url = ''
            
            # Construct full URL if needed
            if url and not url.startswith('http'):
                base_url = system_data.get('url', '')
                if base_url:
                    url = urljoin(base_url, url)
            elif not url:
                # Construct URL from system base URL and filename
                base_url = system_data.get('url', '')
                if base_url:
                    url = urljoin(base_url, filename)
                else:
                    continue  # Can't construct URL
            
            # Add the download
            task_id = self.add_download(url, filename, system_download_dir)
            task_ids.append(task_id)
        
        return task_ids
    
    def start_download(self, task_id: str) -> bool:
        """
        Start a specific download
        
        Args:
            task_id: ID of the task to start
            
        Returns:
            True if download started, False if it couldn't start
        """
        if task_id not in self.downloads:
            return False
            
        task = self.downloads[task_id]
        
        if task.status != "pending":
            return False
            
        if self.active_downloads >= self.max_concurrent_downloads:
            return False
            
        # Start download in a separate thread
        thread = threading.Thread(target=self._download_worker, args=(task_id,))
        thread.daemon = True
        thread.start()
        
        self.download_threads[task_id] = thread
        self.active_downloads += 1
        
        return True
    
    def start_all_downloads(self):
        """Start all pending downloads (up to max concurrent limit)"""
        started = 0
        for task_id, task in self.downloads.items():
            if task.status == "pending" and self.active_downloads < self.max_concurrent_downloads:
                if self.start_download(task_id):
                    started += 1
        return started
    
    def pause_download(self, task_id: str):
        """Pause a specific download"""
        if task_id in self.downloads:
            task = self.downloads[task_id]
            if task.status == "downloading":
                task.status = "paused"
                self._notify_status(task_id, "paused", "Download paused")
    
    def resume_download(self, task_id: str):
        """Resume a paused download"""
        if task_id in self.downloads:
            task = self.downloads[task_id]
            if task.status == "paused":
                task.status = "pending"
                self.start_download(task_id)
    
    def cancel_download(self, task_id: str):
        """Cancel a download and remove it from the queue"""
        if task_id in self.downloads:
            task = self.downloads[task_id]
            if task.status == "downloading":
                task.status = "failed"
                task.error_message = "Cancelled by user"
            
            # Clean up partial file
            output_path = task.get_output_path()
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
                    
            # Remove from downloads
            del self.downloads[task_id]
            
            if task_id in self.download_threads:
                del self.download_threads[task_id]
                
            self._notify_status(task_id, "cancelled", "Download cancelled")
    
    def get_download_status(self, task_id: str) -> Optional[DownloadTask]:
        """Get the status of a specific download"""
        return self.downloads.get(task_id)
    
    def get_all_downloads(self) -> Dict[str, DownloadTask]:
        """Get all download tasks"""
        return self.downloads.copy()
    
    def clear_completed_downloads(self):
        """Remove all completed and failed downloads from the list"""
        to_remove = []
        for task_id, task in self.downloads.items():
            if task.status in ["completed", "failed"]:
                to_remove.append(task_id)
                
        for task_id in to_remove:
            del self.downloads[task_id]
            if task_id in self.download_threads:
                del self.download_threads[task_id]
    
    def _download_worker(self, task_id: str):
        """Worker function that performs the actual download"""
        task = self.downloads[task_id]
        task.status = "downloading"
        task.start_time = time.time()
        
        self._notify_status(task_id, "started", f"Starting download: {task.filename}")
        
        try:
            output_path = task.get_output_path()
            
            # Check if file already exists and get resume position
            resume_pos = 0
            if os.path.exists(output_path):
                resume_pos = os.path.getsize(output_path)
                
            # Set up headers for resume
            headers = {}
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'
            
            # Start the download
            response = requests.get(task.url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get total file size
            if 'content-length' in response.headers:
                content_length = int(response.headers['content-length'])
                task.total_bytes = content_length + resume_pos
            else:
                task.total_bytes = 0
                
            task.downloaded_bytes = resume_pos
            
            # Open file for writing (append mode if resuming)
            mode = 'ab' if resume_pos > 0 else 'wb'
            
            chunk_size = 8192
            last_update = time.time()
            bytes_since_update = 0
            
            with open(output_path, mode) as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if task.status != "downloading":
                        break  # Download was paused or cancelled
                        
                    if chunk:
                        f.write(chunk)
                        task.downloaded_bytes += len(chunk)
                        bytes_since_update += len(chunk)
                        
                        # Update progress and speed
                        current_time = time.time()
                        if current_time - last_update >= 0.5:  # Update every 0.5 seconds
                            time_diff = current_time - last_update
                            task.speed = bytes_since_update / time_diff
                            
                            if task.total_bytes > 0:
                                task.progress = (task.downloaded_bytes / task.total_bytes) * 100
                            
                            self._notify_progress(task_id, task)
                            
                            last_update = current_time
                            bytes_since_update = 0
            
            # Check if download completed successfully
            if task.status == "downloading":
                if task.total_bytes == 0 or task.downloaded_bytes >= task.total_bytes:
                    task.status = "completed"
                    task.progress = 100.0
                    task.end_time = time.time()
                    
                    # Handle ZIP extraction if needed
                    self._handle_post_download(task_id)
                    
                    self._notify_status(task_id, "completed", f"Download completed: {task.filename}")
                else:
                    task.status = "failed"
                    task.error_message = "Download incomplete"
                    self._notify_status(task_id, "failed", "Download incomplete")
            
        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            task.end_time = time.time()
            self._notify_status(task_id, "failed", f"Download failed: {str(e)}")
            
        finally:
            self.active_downloads -= 1
            self._notify_progress(task_id, task)
            
            # Start next pending download if available
            self._start_next_pending_download()
    
    def _start_next_pending_download(self):
        """Start the next pending download if we have capacity"""
        if self.active_downloads < self.max_concurrent_downloads:
            for task_id, task in self.downloads.items():
                if task.status == "pending":
                    self.start_download(task_id)
                    break
    
    def _handle_post_download(self, task_id: str):
        """Handle post-download processing like ZIP extraction and NSZ decompression"""
        task = self.downloads[task_id]
        output_path = task.get_output_path()
        
        # Check if file is a ZIP and should be extracted
        if output_path.lower().endswith('.zip'):
            try:
                self._extract_zip(output_path, task.destination)
                
                # Remove the ZIP file after extraction
                os.remove(output_path)
                
                self._notify_status(task_id, "extracted", f"Extracted ZIP: {task.filename}")
                
            except Exception as e:
                # ZIP extraction failed, but download was successful
                task.error_message = f"ZIP extraction failed: {str(e)}"
                self._notify_status(task_id, "extract_failed", f"ZIP extraction failed: {str(e)}")
        
        # Check if file is an NSZ and should be decompressed
        elif output_path.lower().endswith('.nsz'):
            try:
                self._notify_status(task_id, "decompressing", f"Decompressing NSZ: {task.filename}")
                
                success, message = self.nsz_service.decompress_nsz(output_path, task.destination)
                
                if success:
                    # Optionally remove the NSZ file after decompression
                    # (user might want to keep it for space reasons)
                    self._notify_status(task_id, "decompressed", f"Decompressed NSZ: {message}")
                else:
                    # NSZ decompression failed, but download was successful
                    task.error_message = f"NSZ decompression failed: {message}"
                    self._notify_status(task_id, "decompress_failed", f"NSZ decompression failed: {message}")
                    
            except Exception as e:
                # NSZ decompression failed, but download was successful
                task.error_message = f"NSZ decompression failed: {str(e)}"
                self._notify_status(task_id, "decompress_failed", f"NSZ decompression failed: {str(e)}")
    
    def _extract_zip(self, zip_path: str, destination: str):
        """Extract a ZIP file to the destination directory"""
        with ZipFile(zip_path, 'r') as zip_file:
            zip_file.extractall(destination)
    
    def get_download_stats(self) -> Dict[str, int]:
        """Get overall download statistics"""
        stats = {
            'total': len(self.downloads),
            'pending': 0,
            'downloading': 0,
            'completed': 0,
            'failed': 0,
            'paused': 0
        }
        
        for task in self.downloads.values():
            stats[task.status] += 1
            
        return stats