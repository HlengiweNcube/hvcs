from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_caregiver'),
    ]

    operations = [
        migrations.RenameField(
            model_name='client',
            old_name='phone',
            new_name='contact_phone',
        ),
        migrations.RemoveField(
            model_name='client',
            name='email',
        ),
        migrations.RemoveField(
            model_name='client',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='client',
            name='updated_at',
        ),
        migrations.AddField(
            model_name='client',
            name='care_needs',
            field=models.TextField(blank=True),
        ),
    ]