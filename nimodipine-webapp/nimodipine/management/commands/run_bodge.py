import importlib

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = '''Run a bodge script'''

    def add_arguments(self, parser):
        parser.add_argument('--bodge', type=str)

    def handle(self, *args, **options):
        if hasattr(importlib.util, 'module_from_spec'):  # python > 3.4
            spec = importlib.util.spec_from_file_location("module.name", options['bodge'])
            foo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(foo)
        else:
            from importlib.machinery import SourceFileLoader
            foo = SourceFileLoader("module.name", options['bodge']).load_module()
        foo.run()
