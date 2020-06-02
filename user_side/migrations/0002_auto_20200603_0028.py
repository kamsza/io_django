# Generated by Django 3.0.6 on 2020-06-02 22:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_side', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Service_DNS',
            new_name='Queries',
        ),
        migrations.RenameField(
            model_name='vpn',
            old_name='nlconfig_file',
            new_name='ovpn_config',
        ),
        migrations.RemoveField(
            model_name='history',
            name='returned_ip',
        ),
        migrations.AddField(
            model_name='vpn',
            name='ovpn_config_sha256',
            field=models.CharField(default='', max_length=64),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='ReturnedIP',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('returned_ip', models.GenericIPAddressField()),
                ('vpn', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_side.History')),
            ],
        ),
        migrations.AddField(
            model_name='history',
            name='returned_ips',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='user_side.ReturnedIP'),
            preserve_default=False,
        ),
    ]
