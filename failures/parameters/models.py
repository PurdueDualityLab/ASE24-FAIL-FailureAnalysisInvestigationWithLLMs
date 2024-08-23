from django.db import models
from django.utils.translation import gettext_lazy as _

from typing import Optional, Any
from django.core.exceptions import ObjectDoesNotExist

class Parameter(models.Model):
    class ValueType(models.IntegerChoices):
        INTEGER = 1, _("Integer")
        FLOAT = 2, _("Float")
        STRING = 3, _("String")
        BOOLEAN = 4, _("Boolean")

    value_type = models.IntegerField(_("Value Type"), choices=ValueType.choices)

    name = models.CharField(_("Name"), max_length=255, unique=True)

    # help text to say that true and false strings for boolean values
    value = models.CharField(
        _("Value"),
        max_length=255,
        help_text=_('Type "True" or "False" for boolean values.'),
    )

    description = models.TextField(_("Description"), blank=True)

    class Meta:
        verbose_name = _("Parameter")
        verbose_name_plural = _("Parameters")

    def __str__(self):
        return self.name

    @classmethod
    def get(cls, name: str, default: Optional[Any] = None) -> Any:
        try:
            instance = cls.objects.get(name=name)
        except ObjectDoesNotExist:
            return default

        if instance.value_type == cls.ValueType.INTEGER:
            return int(instance.value)
        elif instance.value_type == cls.ValueType.FLOAT:
            return float(instance.value)
        elif instance.value_type == cls.ValueType.STRING:
            return instance.value
        elif instance.value_type == cls.ValueType.BOOLEAN:
            return instance.value.lower() == "true"
        else:
            raise ValueError("Unknown value type")
        
    '''
    @classmethod
    def set(cls, name: str, default: Optional[Any] = None) -> Any:
        try:
            instance = cls.objects.get(name=name)
        except ObjectDoesNotExist:
    '''
            

'''
TODO: Do we even need Parameters?
#Need to set up multiple classes of parameters:
1. Ones that only need to be run once 
2. Ones that need to be run each time a new parameter is added
'''