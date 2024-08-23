from django.contrib import admin

from failures.parameters.models import Parameter


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ("name", "value")
    list_filter = ("name",)
