# Generated by Django 4.2.16 on 2024-10-22 09:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0002_botcontent_prize'),
    ]

    operations = [
        migrations.CreateModel(
            name='QRCheck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_id', models.BigIntegerField(verbose_name='Telegram unique user ID')),
                ('phone_number', models.CharField(max_length=20, verbose_name='Player phone number')),
                ('purchase_amount', models.FloatField(blank=True, null=True, verbose_name='Sum of purchase amount')),
                ('operation_date', models.CharField(blank=True, max_length=30, null=True, verbose_name='Operation date')),
                ('order_number', models.CharField(blank=True, max_length=50, null=True, verbose_name='Order number')),
                ('qr_data', models.CharField(blank=True, max_length=250, null=True, verbose_name='Data in Qr code')),
                ('buyer_phone_or_address', models.CharField(blank=True, max_length=50, null=True, verbose_name='Buyer phone or email address')),
                ('items', models.TextField(blank=True, null=True, verbose_name='Purchased items')),
                ('organization', models.CharField(blank=True, max_length=100, null=True, verbose_name='Organization name')),
            ],
        ),
        migrations.AddField(
            model_name='prize',
            name='available',
            field=models.IntegerField(blank=True, null=True, verbose_name='Available quantity'),
        ),
        migrations.CreateModel(
            name='Winner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_id', models.BigIntegerField(verbose_name='Telegram unique user ID')),
                ('phone_number', models.CharField(max_length=20, verbose_name='Player phone number')),
                ('total_sum', models.IntegerField(verbose_name='Total price of purchase amount')),
                ('fio', models.CharField(max_length=100, verbose_name='User full name')),
                ('received', models.BooleanField(default=False, verbose_name='Checker if the prize received or not')),
                ('prize', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='bot.prize')),
            ],
        ),
    ]