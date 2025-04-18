# Generated by Django 5.1.4 on 2024-12-12 03:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_customuser_about_customuser_is_creator'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='background_picture',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
        migrations.AddField(
            model_name='customuser',
            name='instagram',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
        migrations.AddField(
            model_name='customuser',
            name='youtube',
            field=models.URLField(blank=True, null=True),
        ),
    ]
