# Generated by Django 2.0 on 2021-01-01 18:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0003_auto_20180605_0842'),
    ]

    operations = [
        migrations.AddField(
            model_name='voting',
            name='url',
            field=models.CharField(default='_voting_decide_example', max_length=40),
            preserve_default=False,
        ),
    ]