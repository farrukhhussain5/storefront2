from django.core.management.base import BaseCommand
from django.db import connection
import os

class Command(BaseCommand):
    help = 'Seeds the database with data from seed.sql'

    def handle(self, *args, **options):
        seed_file = os.path.join(os.path.dirname(__file__), '../../../seed.sql')
        with open(seed_file, 'r') as f:
            sql = f.read()
        with connection.cursor() as cursor:
            cursor.execute(sql)
        self.stdout.write(self.style.SUCCESS('Database seeded successfully'))