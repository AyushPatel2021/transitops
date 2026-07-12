import os
import importlib
import pkgutil
import logging

logger = logging.getLogger(__name__)

def discover_models_recursive(package_name, package_path):
    """
    Recursively discover and import all modules in a package.
    """
    modules = []
    for _, name, is_pkg in pkgutil.iter_modules([package_path]):
        full_module_name = f"{package_name}.{name}"
        try:
            importlib.import_module(full_module_name)
            modules.append(full_module_name)
            logger.info(f"Imported: {full_module_name}")
            
            if is_pkg:
                # Recurse into subpackages
                subpackage_path = os.path.join(package_path, name)
                modules.extend(discover_models_recursive(full_module_name, subpackage_path))
        except Exception as e:
            logger.error(f"Failed to import {full_module_name}: {e}")
            
    return modules

# Perform discovery on import
discovered = discover_models_recursive(__name__, os.path.dirname(__file__))
