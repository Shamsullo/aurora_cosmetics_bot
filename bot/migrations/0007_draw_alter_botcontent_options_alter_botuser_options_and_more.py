# Generated by Django 4.2.16 on 2024-10-26 09:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0006_botcontent_mega_prize_min'),
    ]

    operations = [
        migrations.CreateModel(
            name='Draw',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_id', models.BigIntegerField(verbose_name='Telegram unique user ID')),
                ('phone_number', models.CharField(max_length=20, verbose_name='Player phone number')),
                ('total_sum', models.IntegerField(verbose_name='Total price of purchase amount')),
                ('player_info', models.CharField(max_length=250, verbose_name='Player extra info')),
                ('received', models.BooleanField(default=False, verbose_name='Checker if the prize presented or not')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created date')),
            ],
            options={
                'verbose_name': 'Розыгрыш',
                'verbose_name_plural': 'Розыгрыши',
            },
        ),
        migrations.AlterModelOptions(
            name='botcontent',
            options={'verbose_name': 'Контент', 'verbose_name_plural': 'Контенты'},
        ),
        migrations.AlterModelOptions(
            name='botuser',
            options={'verbose_name': 'Участник', 'verbose_name_plural': 'Участники'},
        ),
        migrations.AlterModelOptions(
            name='prize',
            options={'verbose_name': 'Приз', 'verbose_name_plural': 'Призы'},
        ),
        migrations.AlterModelOptions(
            name='qrcheck',
            options={'verbose_name': 'Чек', 'verbose_name_plural': 'Чеки'},
        ),
        migrations.DeleteModel(
            name='Winner',
        ),
        migrations.AddField(
            model_name='draw',
            name='prize',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='bot.prize'),
        ),
    ]
