import importlib

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = '''Run a bodge script'''

    def add_arguments(self, parser):
        parser.add_argument('--bodge', type=str)

    def handle(self, *args, **options):
        spec = importlib.util.spec_from_file_location("module.name", options['bodge'])
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)
        foo.run()
