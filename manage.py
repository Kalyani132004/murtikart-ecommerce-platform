#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from murtikart_project import VERSION
from django.core.management.base import BaseCommand
#set the project version at manually 
from murtikart_project import VERSION #main folder 
class Command(BaseCommand):
    help = 'Displays the current application version'

    def handle(self, *args, **options):
        self.stdout.write(f"Application Version: {VERSION}")
        
def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'murtikart_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
