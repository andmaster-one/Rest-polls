# Generated by Django 3.1.4 on 2020-12-08 14:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('worksheet', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='useranswers',
            name='user_id',
        ),
    ]
