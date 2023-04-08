"""
This script is responsible for generating database table schema
in d2 diagram language.
"""

import os
from dataclasses import dataclass, field
from typing import Type, Optional
from enum import Enum

from django.db.models import Model
from django.db.models.fields.related import RelatedField, ForeignKey, ManyToManyField, OneToOneField
from django.apps import apps


class RelationKind(Enum):
    MANY_TO_MANY = 'm2m'
    FOREIGN_KEY = 'fk'
    ONE_TO_ONE = 'o2o'


@dataclass(frozen=True)
class Relation:
    source_model: str
    target: str
    kind: RelationKind
    allow_null: bool


@dataclass
class ModelGraph:
    nodes: list[Type[Model]]
    relations: list[Relation]


@dataclass
class ModelExportConfig:
    user_apps_only: bool = True
    """
    If set to true, models from third-party apps and internal
    django models will be excluded from diagram.
    """
    exclude_apps: list[str] = field(default_factory=list)
    """
    Specify list of application names that will be excluded from diagram.
    """


class GraphModelBuilder:
    def __init__(self, config: ModelExportConfig):
        self._config = config

    def build_graph(self) -> ModelGraph:
        nodes = [
            model
            for app_name, models in apps.all_models.items()
            if self.should_export_app(app_name)
            for _, model in models.items()
            if self.should_export_model(model)
        ]

        models = {model._meta.label: model for model in nodes}
        relations = []
        for node in nodes:
            relations += self.get_model_relations(models, node)

        return ModelGraph(nodes=nodes, relations=relations)

    def get_model_relations(
        self,
        models: dict[str, Type[Model]],
        model: Type[Model],
    ) -> list[Relation]:
        result = []
        for field_ in model._meta.fields:
            if isinstance(field_, RelatedField):
                if relation := self.build_relation_from_field(models, model, field_):
                    result.append(relation)

        return result

    def build_relation_from_field(
        self,
        models: dict[str, Type[Model]],
        model: Type[Model],
        field: RelatedField,
    ) -> Optional[Relation]:
        to = field.related_model
        related = models.get(to._meta.label)
        if related is None:
            return

        kind_map: dict[Type[RelatedField], RelationKind] = {
            ForeignKey: RelationKind.FOREIGN_KEY,
            ManyToManyField: RelationKind.MANY_TO_MANY,
            OneToOneField: RelationKind.ONE_TO_ONE,
        }
        kind = kind_map.get(field.__class__)

        if kind is None:
            return

        return Relation(model._meta.label, related._meta.label, kind, field.null)

    def should_export_model(self, model: Type[Model]) -> bool:
        return not model._meta.abstract

    def should_export_app(self, app_name: str) -> bool:
        return (
            app_name not in self._config.exclude_apps
            and (
                not self._config.user_apps_only
                or is_local_dep(apps.get_app_config(app_name).module)
            )
        )


def is_local_dep(module) -> bool:
    if not module.__file__:
        return False
    path = str(os.path.abspath(module.__file__))
    return 'site-packages' not in path
