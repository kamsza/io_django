# Generated by Django 3.0.6 on 2020-05-28 19:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_side', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
            ],
        ),
        migrations.RenameField(
            model_name='subscription',
            old_name='service',
            new_name='service_id',
        ),
        migrations.RenameField(
            model_name='subscription',
            old_name='user',
            new_name='user_id',
        ),
        migrations.AlterField(
            model_name='dns',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='service',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
