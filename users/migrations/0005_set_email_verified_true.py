# Generated manually to remove email verification requirement

from django.db import migrations, models

def set_email_verified_true(apps, schema_editor):
    """Set email_verified to True for all existing users"""
    User = apps.get_model('users', 'User')
    User.objects.filter(email_verified=False).update(email_verified=True)

def reverse_email_verified(apps, schema_editor):
    """Reverse operation - set email_verified back to False"""
    User = apps.get_model('users', 'User')
    User.objects.filter(email_verified=True).update(email_verified=False)

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_user_email_user_unique_user_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email_verified',
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(
            set_email_verified_true,
            reverse_email_verified
        ),
    ]