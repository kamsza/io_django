# Generated by Django 3.0.6 on 2020-06-28 18:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_side', '0012_auto_20200618_1730'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='subscription',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_side.Subscription'),
        ),
    ]
