# Generated by Django 2.0 on 2018-01-05 20:30

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0021_auto_20180106_0146'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newsarticle',
            name='topic',
        ),
        migrations.AlterModelOptions(
            name='news',
            options={},
        ),
        migrations.RemoveField(
            model_name='news',
            name='publish_on',
        ),
        migrations.RemoveField(
            model_name='news',
            name='source_name',
        ),
        migrations.AddField(
            model_name='news',
            name='cycle',
            field=models.IntegerField(default=-1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='news',
            name='new',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='news',
            name='topic',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='blog.NewsTopic'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='news',
            name='content',
            field=models.CharField(max_length=160),
        ),
        migrations.AlterField(
            model_name='news',
            name='link',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='news',
            name='posted_on',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.DeleteModel(
            name='NewsArticle',
        ),
    ]
