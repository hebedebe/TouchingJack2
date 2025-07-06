from abc import ABC, abstractmethod
import importlib
import sys

from .actor import Actor

class Component(ABC):
    """
    Base class for all components in the game engine.
    Components are used to add functionality to actors.
    """

    def __init__(self):
        self.enabled = True  # Indicates if the component is active
        self.actor: Actor = None  # type: ignore # Reference to the actor this component is attached to

    def setActor(self, actor: Actor):
        """
        Set the actor this component is attached to.
        This method is called by the actor when the component is added.
        """
        self.actor = actor
        self.start()

    def start(self):
        """
        Initialize the component.
        Override this method in derived classes to implement specific initialization behavior.
        """
        pass

    def handle_event(self, event):
        """
        Handle an event.
        Override this method in derived classes to implement specific event handling behavior.
        """
        pass

    def update(self, delta_time):
        """
        Update the component with the given delta time.
        Override this method in derived classes to implement specific behavior.
        """
        pass

    def physUpdate(self, delta_time):
        """
        Physics update the component with the given delta time.
        This is called before the regular update.
        Override this method in derived classes to implement specific physics behavior.
        """
        pass

    def lateUpdate(self, delta_time):
        """
        Late update the component with the given delta time.
        This is called after all components have been updated.
        Override this method in derived classes to implement specific behavior.
        """
        pass

    def render(self):
        """
        Render the component on the given surface.
        Override this method in derived classes to implement specific rendering behavior.
        """
        pass

    def _serialize_value(self, value):
        from .. import serialization_registry
        for type_, (to_json, _) in serialization_registry.items():
            if isinstance(value, type_):
                return {"__type__": type_.__name__, "value": to_json(value)}

        if isinstance(value, Component):  # Avoid recursion
            return None
        if isinstance(value, (int, float, str, bool, list, dict, type(None))):
            return value
        return str(value)  # Fallback — may need refining

    def _deserialize_value(self, data):
        from .. import serialization_registry
        if isinstance(data, dict) and "__type__" in data:
            type_name = data["__type__"]
            for type_, (_, from_json) in serialization_registry.items():
                if type_.__name__ == type_name:
                    return from_json(data["value"])
        return data

    def serialize(self):
        serialized_data = {
            "module": self.__class__.__module__, 
            "type": self.__class__.__name__
            }

        exclude = getattr(self, "__serialization_exclude__", [])
        include = getattr(self, "__serialization_include__", None)
        custom = getattr(self, "__serialization_custom__", {})

        for key, value in self.__dict__.items():
            if key == "actor" or key in exclude:
                continue
            if include is not None and key not in include:
                continue
            if key in custom:
                to_json, _ = custom[key]
                serialized_data[key] = {"__custom__": True, "value": to_json(value)} # type: ignore
            else:
                serialized_data[key] = self._serialize_value(value) # type: ignore

        return serialized_data

    def deserialize(self, data):
        custom = getattr(self, "__serialization_custom__", {})

        for key, value in data.items():
            if key in ["type", "module"]:
                continue
            if isinstance(value, dict) and value.get("__custom__"):
                _, from_json = custom.get(key, (None, None))
                if from_json:
                    setattr(self, key, from_json(value["value"]))
            else:
                setattr(self, key, self._deserialize_value(value))
        return self

    
    @staticmethod
    def createFromData(data: dict):
        """
        Create a component instance from serialized data.
        """
        component_type = data.get("type")
        if not component_type:
            raise ValueError("Serialized data must contain a 'type' field.")

        component_module = data.get("module")
        if not component_module:
            raise ValueError("Serialized data must contain a 'module' field.")

        # Dynamically import the module and get the class
        try:
            if component_module == "__main__":
                # Handle __main__ module specially
                module = sys.modules["__main__"]
            else:
                module = importlib.import_module(component_module)
            
            component_class = getattr(module, component_type)
            if not issubclass(component_class, Component):
                raise ValueError(f"Class {component_type} is not a Component subclass")
                
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Cannot find component class {component_type} in module {component_module}: {e}")

        component = component_class()
        component.deserialize(data)
        return component