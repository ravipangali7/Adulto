from django.core.management.base import BaseCommand
from core.models import Video
import time


class Command(BaseCommand):
    help = 'Generate thumbnails for videos that don\'t have them (with progress tracking)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerate thumbnails even if they already exist',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of videos to process',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.5,
            help='Delay between thumbnail generations (seconds)',
        )

    def handle(self, *args, **options):
        force = options['force']
        limit = options['limit']
        delay = options['delay']
        
        if force:
            videos = Video.objects.filter(video_file__isnull=False)
            self.stdout.write(f'Regenerating thumbnails for {videos.count()} videos...')
        else:
            videos = Video.objects.filter(video_file__isnull=False, thumbnail__isnull=True)
            self.stdout.write(f'Generating thumbnails for {videos.count()} videos without thumbnails...')

        if limit:
            videos = videos[:limit]
            self.stdout.write(f'Limited to {limit} videos')

        success_count = 0
        error_count = 0
        total_videos = videos.count()

        for i, video in enumerate(videos, 1):
            try:
                self.stdout.write(f'[{i}/{total_videos}] Processing: {video.title}')
                
                if force and video.thumbnail:
                    # Delete existing thumbnail
                    video.thumbnail.delete(save=False)
                
                if video.generate_thumbnail():
                    video.save(update_fields=['thumbnail'])
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Generated thumbnail for: {video.title}')
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to generate thumbnail for: {video.title}')
                    )
                
                # Add delay to prevent overwhelming the system
                if delay > 0:
                    time.sleep(delay)
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Error processing {video.title}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Generated {success_count} thumbnails, {error_count} errors.'
            )
        )
