from typing import Type

from django.db.models import Model

from .graph_builder import ModelGraph, Relation


class GraphRenderer:
    def render_model_graph(self, graph: ModelGraph) -> str:
        models = '\n'.join(self.render_model(model) for model in graph.nodes)
        relations = '\n'.join(self.render_relation(rel) for rel in graph.relations)
        return f'# Models:\n\n{models}\n# Relations:\n\n{relations}'


    def render_model(self, model: Type[Model]) -> str:
        return (
            f'{model._meta.label}: {{\n'
            '\tshape: sql_table\n'
            + self.render_model_fields(model)
            + '\n}\n'
        )


    def render_model_fields(self, model: Type[Model]) -> str:
        return '\n'.join(
            f'\t.{field_.name}: .{field_.name}'
            for field_ in model._meta.fields
        )


    def render_relation(self, relation: Relation) -> str:
        return f'{relation.source_model} -> {relation.target}\n'
