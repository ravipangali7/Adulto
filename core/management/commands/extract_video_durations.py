from django.core.management.base import BaseCommand
from core.models import Video


class Command(BaseCommand):
    help = 'Extract duration from video files for all videos that don\'t have duration set'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-extraction of duration for all videos',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        if force:
            videos = Video.objects.filter(video_file__isnull=False)
            self.stdout.write(f'Processing {videos.count()} videos (force mode)...')
        else:
            videos = Video.objects.filter(
                video_file__isnull=False,
                duration=0
            )
            self.stdout.write(f'Processing {videos.count()} videos without duration...')

        success_count = 0
        error_count = 0

        for video in videos:
            try:
                self.stdout.write(f'Processing: {video.title}')
                
                if video.extract_duration():
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Duration extracted: {video.get_duration_display()}')
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to extract duration')
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Error processing {video.title}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Success: {success_count}, Errors: {error_count}'
            )
        )
