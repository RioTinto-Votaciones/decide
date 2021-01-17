# Generated by Django 2.0 on 2021-01-06 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0004_yesorno_yesornooption'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='yesornooption',
            name='yesorno',
        ),
        migrations.AddField(
            model_name='yesorno',
            name='choice',
            field=models.CharField(choices=[('Y', 'Yes'), ('N', 'No')], default='N', max_length=1),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='YesOrNoOption',
        ),
    ]