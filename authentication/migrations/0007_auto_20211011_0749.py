# Generated by Django 3.1.7 on 2021-10-11 07:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0006_merge_20211009_1215'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='bio',
            field=models.TextField(default='Hello'),
        ),
    ]
