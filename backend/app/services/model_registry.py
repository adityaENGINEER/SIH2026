from app.core.config import settings
from app.services.ollama_service import ollama_service

class ModelRegistry:
    def __init__(self):
        self.configured_models = {
            "general": settings.general_model,
            "vision": settings.vision_model,
            "embedding": settings.embedding_model,
        }

    async def get_registry_status(self) -> dict:
        installed_models = await ollama_service.list_models()
        installed_names = [m.get("name") for m in installed_models]

        registry = {}
        for role, name in self.configured_models.items():
            registry[role] = {
                "name": name,
                "installed": ollama_service.resolve_installed_name(name, installed_names) is not None
            }
        return registry

    async def get_all_models_detailed(self) -> list:
        installed_models = await ollama_service.list_models()
        installed_names = {m.get("name"): m for m in installed_models}

        models_list = []
        handled_names = set()
        
        for role, name in self.configured_models.items():
            installed_name = ollama_service.resolve_installed_name(name, installed_names)
            is_installed = installed_name is not None
            model_info = {
                "name": installed_name or name,
                "role": role,
                "installed": is_installed,
                "available": is_installed
            }
            if is_installed:
                ollama_meta = installed_names[installed_name]
                model_info["size"] = ollama_meta.get("size")
                model_info["modified_at"] = ollama_meta.get("modified_at")
                model_info["family"] = (ollama_meta.get("details") or {}).get("family")
                model_info["parameter_size"] = (ollama_meta.get("details") or {}).get("parameter_size")
                handled_names.add(installed_name)
                
            models_list.append(model_info)
            
        # Add other downloaded models not mapped to specific roles
        for name, m in installed_names.items():
            if name not in handled_names:
                models_list.append({
                    "name": name,
                    "role": "unassigned",
                    "installed": True,
                    "available": True,
                    "size": m.get("size"),
                    "modified_at": m.get("modified_at")
                })
                
        return models_list

model_registry = ModelRegistry()
