# Generated by Django 4.2.8 on 2023-12-17 11:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_tagihandibayar_dibayar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tagihandibayar',
            name='dibayar',
            field=models.BooleanField(default=False, verbose_name='Dibayar'),
        ),
        migrations.AlterUniqueTogether(
            name='tagihandibayar',
            unique_together={('siswa', 'tagihan')},
        ),
    ]
