from django.core.management.base import BaseCommand

from django_d2_models.graph_builder import GraphModelBuilder, ModelExportConfig
from django_d2_models.renderer import GraphRenderer


class Command(BaseCommand):
    help = 'Generates d2 diagram for django models and input it into stdout'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-apps-only',
            type=bool,
            default=True,
            help='Determines if third-party app models are included.',
        )
        parser.add_argument(
            '--exclude-apps',
            type=str,
            nargs='+',
        )

    def handle(self, *args, **options):
        graph = GraphModelBuilder(self._config_from_options(options)).build_graph()
        print(GraphRenderer().render_model_graph(graph))

    def _config_from_options(self, options: dict) -> ModelExportConfig:
        args = ('user_apps_only', 'exclude_apps')
        config_options = {}
        for arg in args:
            if arg in options:
                config_options[arg] = options[arg]

        return ModelExportConfig(**config_options)
