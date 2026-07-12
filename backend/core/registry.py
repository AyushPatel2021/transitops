class ModelRegistry:
    _models = {}

    @classmethod
    def register(cls, name, model_cls):
        cls._models[name] = model_cls

    @classmethod
    def get_model(cls, name):
        return cls._models.get(name)

    @classmethod
    def list_models(cls):
        return list(cls._models.keys())

    @classmethod
    def is_transient(cls, name):
        """Check if a registered model is a TransientModel (wizard)."""
        model_cls = cls._models.get(name)
        return getattr(model_cls, '_transient', False) if model_cls else False

    @classmethod
    def get_transient_models(cls):
        """Return all registered transient model classes."""
        return {
            name: model_cls 
            for name, model_cls in cls._models.items() 
            if getattr(model_cls, '_transient', False)
        }

registry = ModelRegistry()
