from django.core.management.base import BaseCommand
import os
import tempfile
import time
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Clean up old video chunk files from temporary directory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--older-than',
            type=int,
            default=24,
            help='Delete chunks older than X hours (default: 24)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        older_than_hours = options['older_than']
        dry_run = options['dry_run']
        
        temp_dir = os.path.join(tempfile.gettempdir(), 'video_chunks')
        
        if not os.path.exists(temp_dir):
            self.stdout.write(self.style.WARNING('No chunk directory found'))
            return
        
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        deleted_count = 0
        total_size = 0
        
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            
            if os.path.isdir(item_path):
                # Check if directory is older than cutoff
                dir_mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
                
                if dir_mtime < cutoff_time:
                    if dry_run:
                        self.stdout.write(f'Would delete: {item_path}')
                    else:
                        try:
                            import shutil
                            shutil.rmtree(item_path)
                            self.stdout.write(f'Deleted: {item_path}')
                            deleted_count += 1
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f'Error deleting {item_path}: {e}')
                            )
                else:
                    # Calculate size for reporting
                    dir_size = self.get_directory_size(item_path)
                    total_size += dir_size
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'Dry run: Would delete {deleted_count} directories')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Cleaned up {deleted_count} old chunk directories')
            )
        
        self.stdout.write(f'Total size of remaining chunks: {total_size / (1024*1024):.2f} MB')

    def get_directory_size(self, path):
        """Calculate total size of directory"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception:
            pass
        return total_size
