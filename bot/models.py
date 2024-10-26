from django.db import models


class BotUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username or self.telegram_id}"

    class Meta:
        verbose_name = "Участник"
        verbose_name_plural = "Участники"


class BotContent(models.Model):
    intro_circle_video = models.FileField("Intro Circle Video", upload_to='bot_videos/')
    intro_text = models.TextField("Introductory Text")
    intro_image = models.ImageField("Instruction Image", upload_to='bot_images/')
    instruction_text = models.TextField("Instructions")
    wild_inst_video = models.FileField("Wildberries Instruction Video", upload_to='bot_videos/')
    ozon_inst_video = models.FileField("Ozon Instruction Video", upload_to='bot_videos/')
    mega_prize_min = models.IntegerField("Mega prize minimum amount", default=1000)
    updated_at = models.DateTimeField("Updated At", auto_now=True)

    def __str__(self):
        return f"Bot Content {self.updated_at}"

    class Meta:
        verbose_name = "Контент"
        verbose_name_plural = "Контенты"


class Prize(models.Model):
    name = models.CharField("Prize name", max_length=150)
    description = models.CharField("Prize description", max_length=250, null=True, blank=True)
    quantity = models.IntegerField("Playing quantity")
    min_purchase = models.FloatField("Min. Purchase Amt.", default=0, null=True, blank=True)
    available = models.IntegerField("Available quantity", null=True, blank=True)
    updated_at = models.DateTimeField("Updated At", auto_now=True)

    class Meta:
        verbose_name = "Приз"
        verbose_name_plural = "Призы"

    def __str__(self):
        return f'{self.name}: {self.description}'

class QRCheck(models.Model):
    telegram_id = models.BigIntegerField("Telegram unique user ID")
    phone_number = models.CharField("Player phone number", max_length=20)
    purchase_amount = models.FloatField("Sum of purchase amount", null=True, blank=True)
    operation_date = models.CharField("Operation date", max_length=30, null=True, blank=True)
    order_number = models.CharField("Order number", max_length=50, null=True, blank=True)
    qr_data = models.CharField("Data in Qr code", max_length=250, null=True, blank=True)
    buyer_phone_or_address = models.CharField("Buyer phone or email address", max_length=50, null=True, blank=True)
    items = models.TextField("Purchased items", null=True, blank=True)
    organization = models.CharField("Organization name", max_length=100, null=True, blank=True)
    created_at = models.DateTimeField("Created date", auto_now_add=True)

    class Meta:
        verbose_name = "чек"
        verbose_name_plural = "чеки"


class Draw(models.Model):
    telegram_id = models.BigIntegerField("Telegram unique user ID")
    phone_number = models.CharField("Player phone number", max_length=20)
    total_sum = models.IntegerField("Total price of purchase amount")
    prize = models.ForeignKey(Prize, on_delete=models.DO_NOTHING, null=True, blank=True)
    player_info = models.CharField("Player extra info", max_length=250)
    received = models.BooleanField("Checker if the prize presented or not", default=False)
    created_at = models.DateTimeField("Created date",  auto_now_add=True)

    class Meta:
        verbose_name = "розыгрыш"
        verbose_name_plural = "розыгрыши"
