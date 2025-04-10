# Generated by Django 5.2 on 2025-04-06 16:46

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('health_profiles', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AIInsight',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('priority', models.CharField(choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], default='medium', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_insights', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WellnessScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bmi_score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('activity_score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('progress_score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('habits_score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('total_score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('health_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wellness_scores', to='health_profiles.healthprofile')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
