from django.db import models
from taggit.managers import TaggableManager

from extras.models import ChangeLoggedModel, TaggedItem
from utilities.querysets import RestrictedQuerySet


class ConfigurationTemplate(ChangeLoggedModel):
    name = models.CharField(
        max_length=100,
        unique=True
    )
    slug = models.SlugField(
        max_length=100,
        unique=True
    )
    tenant = models.ForeignKey(
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='routeros_configuration_templates',
        blank=True,
        null=True
    )
    tags = TaggableManager(through=TaggedItem)
    content = models.TextField()

    objects = RestrictedQuerySet.as_manager()

    def __str__(self):
        return self.name
