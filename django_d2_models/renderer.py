from typing import Type

from django.db.models import Model, Field
from django.db.models.fields.related import ForeignKey

from .graph_builder import ModelGraph, Relation, RelationKind


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
            f'\t".{field_.name}": ".{field_.name}" {self.render_model_field_properties(field_)}'
            for field_ in model._meta.fields
        )

    def render_model_field_properties(self, field: Field) -> str:
        items = [
            self.render_field_constraints(field),
        ]
        items = [item for item in items if item]
        if not items:
            return ''

        return '{\n' + '\n'.join(f'\t\t{item}' for item in items) + '\n\t}'

    def render_field_constraints(self, field: Field) -> str:
        if field.name == 'id':
            constraints = 'primary_key'
        elif isinstance(field, ForeignKey):
            constraints = 'foreign_key'
        else:
            constraints = None

        if constraints:
            return f'constraint: {constraints}'
        else:
            return ''

    def render_relation(self, relation: Relation) -> str:
        source = f'{relation.source_model}.".{relation.source_field}"'
        target = f'{relation.target_model}.".{relation.target_field}"'
        properties = self.render_relation_properties(relation)
        return f'{source} <-> {target} {properties}\n'

    def render_relation_properties(self, relation: Relation) -> str:
        if relation.kind == RelationKind.FOREIGN_KEY:
            source = 'cf-many'
            target = 'cf-one'
        elif relation.kind == RelationKind.MANY_TO_MANY:
            source = 'cf-many'
            target = 'cf-many'
        else:
            source = 'cf-one'
            target = 'cf-one'

        return (
            '{\n'
            f'\tsource-arrowhead.shape: {source}\n'
            f'\ttarget-arrowhead.shape: {target}\n'
            '}'
        )
