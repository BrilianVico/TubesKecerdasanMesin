from django.apps import AppConfig

class MlEngineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml_engine'

    def ready(self):
        # Trigger the initial loading of the models via SentimentInferenceService
        # This ensures models are warmed up as soon as Django or Celery starts
        from .services import SentimentInferenceService
        inference_service = SentimentInferenceService()
        inference_service.load_models()
