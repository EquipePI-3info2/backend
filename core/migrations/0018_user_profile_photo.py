import core.validators
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_merge_20260424_0336'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='profile_photo',
            field=models.ImageField(
                blank=True,
                help_text='Foto de perfil do usuário (opcional). Formatos aceitos: JPG, PNG, WEBP. Máx. 5MB.',
                null=True,
                upload_to='users/avatars/',
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=['jpg', 'jpeg', 'png', 'webp']
                    ),
                    core.validators.validate_image_size,
                ],
                verbose_name='foto de perfil',
            ),
        ),
    ]
