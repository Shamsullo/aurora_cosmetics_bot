# management/commands/runbot.py
from django.core.management.base import BaseCommand

from ...bot import main


class Command(BaseCommand):
    help = "Starts the Telegram bot"

    def handle(self, *args, **options):
        main()
