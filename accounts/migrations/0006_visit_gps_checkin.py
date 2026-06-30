from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_visit'),
    ]

    operations = [
        migrations.AddField(
            model_name='visit',
            name='check_in_lat',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='visit',
            name='check_in_lng',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='visit',
            name='check_in_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='visit',
            name='check_out_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
