# Generated by Django 3.0.6 on 2020-06-18 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_side', '0010_remove_vpn_public'),
    ]

    operations = [
        migrations.AddField(
            model_name='vpn',
            name='public',
            field=models.BooleanField(default=True),
        ),
    ]
