"""
This script is responsible for generating database table schema
in d2 diagram language.
"""

import os
from dataclasses import dataclass, field
from typing import Type, Optional, Sequence, Iterator
from enum import Enum

from django.db.models import Model, Field
from django.db.models.fields.related import (
    RelatedField, ForeignKey, ManyToManyField, OneToOneField,
)
from django.apps import apps


class RelationKind(Enum):
    MANY_TO_MANY = 'm2m'
    FOREIGN_KEY = 'fk'
    ONE_TO_ONE = 'o2o'


@dataclass(frozen=True)
class BaseRelation:
    source_model: str
    target_model: str


@dataclass(frozen=True)
class Relation(BaseRelation):
    source_field: str
    target_field: str
    kind: RelationKind
    allow_null: bool


@dataclass(frozen=True)
class InheritanceRelation(BaseRelation):
    pass


@dataclass
class ModelView:
    model: Type[Model]
    fields: Sequence[Field]


@dataclass
class ModelGraph:
    nodes: list[ModelView]
    inheritance: list[InheritanceRelation]
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
    show_ref: bool = True
    """
    Show references even if referenced model is excluded from rendering
    """
    abstract_models_depth: int = 1


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
        inheritance_builder = InheritanceRelationBuilder(self._config.abstract_models_depth)
        for model in nodes:
            inheritance_builder.add_model(model)

        models = {
            model.model._meta.label: model.model
            for model in inheritance_builder.models
        }
        relations = []
        for node in inheritance_builder.models:
            relations += self.get_model_relations(models, node)

        return ModelGraph(
            nodes=inheritance_builder.models,
            relations=relations,
            inheritance=inheritance_builder.relations,
        )

    def get_model_relations(
        self,
        models: dict[str, Type[Model]],
        model: ModelView,
    ) -> list[Relation]:
        result = []
        for field_ in model.fields:
            if isinstance(field_, RelatedField):
                if relation := self.build_relation_from_field(models, model.model, field_):
                    result.append(relation)

        return result

    def build_relation_from_field(
        self,
        models: dict[str, Type[Model]],
        model: Type[Model],
        field: RelatedField,
    ) -> Optional[Relation]:
        to = field.related_model
        # Django does not resolve related fields in abstract models
        if isinstance(to, str):
            to = apps.get_model(to)

        related = models.get(to._meta.label)
        if related is None and not self._config.show_ref:
            return

        kind_map: dict[Type[RelatedField], RelationKind] = {
            ForeignKey: RelationKind.FOREIGN_KEY,
            ManyToManyField: RelationKind.MANY_TO_MANY,
            OneToOneField: RelationKind.ONE_TO_ONE,
        }
        kind = kind_map.get(field.__class__)

        if kind is None:
            return

        return Relation(
            source_model=model._meta.label,
            source_field=field.name,
            target_model=to._meta.label,
            target_field='id',
            kind=kind,
            allow_null=field.null,
        )

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


class InheritanceRelationBuilder:
    def __init__(self, max_depth: int):
        self._max_depth = max_depth
        self.models: list[ModelView] = []
        self._visited = set()
        self.relations: list[InheritanceRelation] = []

    def add_model(self, model: Type[Model], depth: int = 0):
        if model._meta.label in self._visited:
            return
        self._visited.add(model._meta.label)

        if depth >= self._max_depth:
            self.models.append(ModelView(model, model._meta.fields))
            return

        parents: list[Type[Model]] = [
            base
            for base in model.__bases__
            if is_abstract_model(base)
        ]
        parent_fields = {
            field.name
            for base in parents
            for field in base._meta.fields
        }
        fields = [
            field
            for field in model._meta.fields
            if field.name not in parent_fields
        ]
        self.models.append(ModelView(model, fields))
        for base in parents:
            self.relations.append(InheritanceRelation(
                source_model=model._meta.label,
                target_model=base._meta.label,
            ))
            self.add_model(base, depth + 1)


def is_local_dep(module) -> bool:
    if not module.__file__:
        return False
    path = str(os.path.abspath(module.__file__))
    return 'site-packages' not in path


def is_abstract_model(base: Type) -> bool:
    return (
        issubclass(base, Model)
        and base != Model
        and base._meta.abstract
    )
