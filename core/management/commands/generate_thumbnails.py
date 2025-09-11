from django.core.management.base import BaseCommand
from core.models import Video


class Command(BaseCommand):
    help = 'Generate thumbnails for videos that don\'t have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerate thumbnails even if they already exist',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        if force:
            videos = Video.objects.filter(video_file__isnull=False)
            self.stdout.write(f'Regenerating thumbnails for {videos.count()} videos...')
        else:
            videos = Video.objects.filter(video_file__isnull=False, thumbnail__isnull=True)
            self.stdout.write(f'Generating thumbnails for {videos.count()} videos without thumbnails...')

        success_count = 0
        error_count = 0

        for video in videos:
            try:
                if force and video.thumbnail:
                    # Delete existing thumbnail
                    video.thumbnail.delete(save=False)
                
                if video.generate_thumbnail():
                    video.save()
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Generated thumbnail for: {video.title}')
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to generate thumbnail for: {video.title}')
                    )
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
