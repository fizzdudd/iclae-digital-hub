from django.apps import AppConfig as DjangoAppConfig


class AppsConfig(DjangoAppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps'
