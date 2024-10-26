from django.contrib import admin

from .models import BotContent, BotUser, Draw, Prize, QRCheck


class BotUserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'username', 'first_name', 'last_name', 'date_joined')  # Columns to display
    search_fields = ('telegram_id', 'username', 'first_name', 'last_name')  # Searchable fields
    list_filter = ('date_joined',)  # Filters for the sidebar


class BotContentAdmin(admin.ModelAdmin):
    list_display = ('intro_text', 'updated_at')  # Columns to display
    search_fields = ('intro_text', 'updated_at', 'instruction_text')  # Searchable fields
    list_filter = ('updated_at',)  # Filters for the sidebar


class PrizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'quantity', 'min_purchase', 'updated_at')  # Columns to display
    search_fields = ('name', 'description', 'quantity', 'min_purchase')  # Searchable fields
    list_filter = ('updated_at',)  # Filters for the sidebar


class QRCheckAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'purchase_amount', 'operation_date', 'buyer_phone_or_address', 'organization', 'created_at')  # Columns to display
    search_fields = ('phone_number', 'purchase_amount', 'operation_date', 'buyer_phone_or_address', 'items', 'created_at')  # Searchable fields
    list_filter = ('created_at', 'operation_date', 'organization')  # Filters for the sidebar


class DrawAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'telegram_id', 'total_sum', 'prize', 'created_at', 'player_info', 'received')  # Columns to display
    search_fields = ('phone_number', 'telegram_id', 'total_sum', 'prize', 'player_info')  # Searchable fields
    list_filter = ('created_at', 'prize', 'received')  # Filters for the sidebar


admin.site.register(BotUser, BotUserAdmin)
admin.site.register(BotContent, BotContentAdmin)
admin.site.register(Prize, PrizeAdmin)
admin.site.register(QRCheck, QRCheckAdmin)
admin.site.register(Draw, DrawAdmin)
