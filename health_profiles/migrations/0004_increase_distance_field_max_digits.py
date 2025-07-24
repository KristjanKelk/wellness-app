# Generated manually to fix distance field constraint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('health_profiles', '0003_activity_weighthistory_unique_weight_entry_timestamp_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='distance_km',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True),
        ),
    ]