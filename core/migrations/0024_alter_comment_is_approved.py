from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0023_video_core_video_is_acti_7b12ff_idx_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="is_approved",
            field=models.BooleanField(default=False),
        ),
    ]
