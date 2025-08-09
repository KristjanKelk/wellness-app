from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_set_email_verified_true'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
    ]