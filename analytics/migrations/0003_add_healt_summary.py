from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_add_milestone_model'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HealthSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('summary_type', models.CharField(choices=[('weekly', 'Weekly Summary'), ('monthly', 'Monthly Summary')], max_length=10)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('summary_text', models.TextField(blank=True, null=True)),
                ('key_achievements', models.JSONField(blank=True, default=list)),
                ('areas_for_improvement', models.JSONField(blank=True, default=list)),
                ('recommendations', models.JSONField(blank=True, default=list)),
                ('metrics_summary', models.JSONField(blank=True, default=dict)),
                ('status', models.CharField(choices=[('generating', 'Generating'), ('completed', 'Completed'), ('failed', 'Failed')], default='generating', max_length=12)),
                ('generation_prompt', models.TextField(blank=True, null=True)),
                ('ai_model_used', models.CharField(default='gpt-3.5-turbo', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('generated_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='health_summaries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SummaryMetric',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metric_name', models.CharField(max_length=100)),
                ('metric_value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('metric_unit', models.CharField(blank=True, max_length=20)),
                ('previous_value', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('change_percentage', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('change_direction', models.CharField(choices=[('improved', 'Improved'), ('declined', 'Declined'), ('stable', 'Stable'), ('new', 'New Metric')], default='new', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('summary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detailed_metrics', to='analytics.healthsummary')),
            ],
        ),
        migrations.AddConstraint(
            model_name='healthsummary',
            constraint=models.UniqueConstraint(fields=('user', 'summary_type', 'start_date', 'end_date'), name='unique_user_summary_period'),
        ),
        migrations.AddConstraint(
            model_name='summarymetric',
            constraint=models.UniqueConstraint(fields=('summary', 'metric_name'), name='unique_summary_metric'),
        ),
    ]