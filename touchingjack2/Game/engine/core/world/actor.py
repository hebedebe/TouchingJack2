from pygame import Vector2

class Transform:
    def __init__(self):
        self.position = Vector2(0,0)  # (x, y)
        self.rotation = 0  # in degrees
        self.scale = Vector2(1, 1)  # (scale_x, scale_y)

    def setPosition(self, x: float, y: float) -> None:
        """Set the position of the transform."""
        self.position = Vector2(x, y)

    def setRotation(self, rotation: float) -> None:
        """Set the rotation of the transform."""
        self.rotation = rotation

    def setScale(self, scale_x: float, scale_y: float) -> None:
        """Set the scale of the transform."""
        self.scale = Vector2(scale_x, scale_y)

    def serialize(self) -> dict:
        """Serialize the transform to a dictionary."""
        return {
            "position": self.position,
            "rotation": self.rotation,
            "scale": self.scale
        }

    @staticmethod
    def deserialize(data: dict):
        """Deserialize a transform from a dictionary."""
        return Transform(
            position=tuple(data.get("position", (0, 0))),
            rotation=data.get("rotation", 0),
            scale=tuple(data.get("scale", (1, 1)))
        )

class Actor():
    def __init__(self, name: str = "Actor", components=[]):
        self.name = name
        self.tags = set()  # Using a set for unique tags
        self.components = []
        self.transform = Transform()
        
        self.scene = None  # Reference to the scene this actor belongs to

        # Parent-child relationships
        self.parent: 'Actor' = None
        self.children: list['Actor'] = []

        for component in components: # done here so components are added properly
            self.addComponent(component)

    @property
    def screenPosition(self):
        return self.transform.position - self.scene.worldOffset

    def setName(self, name: str) -> None:
        """Set the name of the actor."""
        self.name = name

    def addComponent(self, component) -> None:
        """Add a component to the actor."""
        assert component not in self.components, "Component already exists in actor"
        self.components.append(component)
        component.setActor(self)
        print(f"Added component {component.__class__.__name__} to actor {self.name}")

    def addComponents(self, *args) -> None:
        """Add multiple components to the actor."""
        for component in args:
            self.addComponent(component)

    def removeComponent(self, component) -> None:
        """Remove a component from the actor."""
        if component in self.components:
            self.components.remove(component)
            component.setActor(None)

    def getComponent(self, component_type, allow_inheritance=False):
        """Get a component of a specific type from the actor."""
        if type(component_type) is str:
            # If a string is passed, treat it as a class name
            component = next((comp for comp in self.components if comp.__class__.__name__ == component_type), None)
            if not component_type:
                return None
            return component
            
        for comp in self.components:
            if isinstance(comp, component_type):
                return comp
        if allow_inheritance:
            for comp in self.components:
                if issubclass(comp, component_type):
                    return comp
        return None

    def addTag(self, tag: str) -> None:
        """Add a tag to the actor."""
        self.tags.add(tag)

    def removeTag(self, tag: str) -> None:
        """Remove a tag from the actor."""
        self.tags.discard(tag)

    def setParent(self, parent: 'Actor') -> None:
        """Set this actor's parent."""
        # Remove from old parent
        if self.parent and self in self.parent.children:
            self.parent.children.remove(self)
            
        # Set new parent
        self.parent = parent
        
        # Add to new parent
        if parent and self not in parent.children:
            parent.children.append(self)
            
    def addChild(self, child: 'Actor') -> None:
        """Add a child actor."""
        child.setParent(self)
        
    def removeChild(self, child: 'Actor') -> None:
        """Remove a child actor."""
        if child in self.children:
            child.setParent(None)
            
    def getParent(self) -> 'Actor':
        """Get this actor's parent."""
        return self.parent
        
    def getChildren(self) -> list['Actor']:
        """Get this actor's children."""
        return self.children.copy()  # Return copy to prevent external modification
    
    def handleEvent(self, event) -> bool:
        """Handle an event and forward it to components."""
        # Forward event to all components that can handle events
        for component in self.components:
            component.handle_event(event)

    def handleUpdate(self, dt: float) -> None:
        """Handle the update logic for the actor."""
        # Update all components
        for component in self.components:
            if component.enabled:
                component.update(dt)
        # Update the actor's own state
        self.update(dt)

    def handlePhysUpdate(self, dt: float) -> None:
        """Handle the physics update logic for the actor."""
        # Update all components in physics update phase
        for component in self.components:
            if component.enabled:
                component.physUpdate(dt)
        # Perform any physics update logic for the actor itself
        self.physUpdate(dt)

    def handleLateUpdate(self, dt: float) -> None:
        """Handle the late update logic for the actor."""
        # Update all components in late update phase
        for component in self.components:
            if component.enabled:
                component.lateUpdate(dt)
        # Perform any late update logic for the actor itself
        self.lateUpdate(dt)

    def update(self, dt: float) -> None:
        """Update the actor's state."""
        # Update logic for the actor
        pass

    def physUpdate(self, dt: float) -> None:
        """Physics update logic for the actor."""
        # Physics update logic for the actor
        pass

    def lateUpdate(self, dt: float) -> None:
        """Late update logic for the actor."""
        # Late update logic for the actor
        pass

    def handleRender(self) -> None:
        """Handle the rendering of the actor."""
        # Render all components
        for component in self.components:
            if component.enabled:
                component.render()
        # Render the actor itself
        self.render()

    def render(self) -> None:
        """Render the actor on the given surface."""
        # Render logic for the actor
        pass

    def serialize(self) -> dict:
        """Serialize the actor to a dictionary."""
        data = {
            "name": self.name,
            "tags": list(self.tags),
            "components": [component.serialize() for component in self.components],
            # Serialize child relationships using names to avoid circular dependencies
            "parent_name": self.parent.name if self.parent else None,
            "children_names": [child.name for child in self.children]
        }
        return data

    def deserialize(self, data: dict) -> None:
        """Deserialize the actor from a dictionary."""
        from .component import Component
        self.name = data.get("name", "Actor")
        self.tags = set(data.get("tags", []))
        self.components = [Component.deserialize(compData) for compData in data.get("components", [])]
        # Note: Parent/child relationships need to be re-established after all actors are deserialized
        # Store the relationship data for later processing
        self._serialized_parent_name = data.get("parent_name")
        self._serialized_children_names = data.get("children_names", [])

    @staticmethod
    def createFromSerializedData(data: dict):
        """
        Create an actor instance from serialized data.
        """
        from .component import Component
        actor = Actor()
        
        # Deserialize basic actor properties
        actor.name = data.get("name", "Actor")
        actor.tags = set(data.get("tags", []))
        
        # Store relationship data for later processing
        actor._serialized_parent_name = data.get("parent_name")
        actor._serialized_children_names = data.get("children_names", [])
        
        # Deserialize and add components
        for component_data in data.get("components", []):
            component = Component.createFromData(component_data)
            actor.addComponent(component)
        return actor

    @staticmethod
    def establishRelationshipsFromSerialization(actors: list['Actor']) -> None:
        """
        Re-establish parent-child relationships after deserializing a list of actors.
        This should be called after all actors have been deserialized.
        """
        # Create a name-to-actor mapping for quick lookup
        actor_map = {actor.name: actor for actor in actors}
        
        # Re-establish relationships
        for actor in actors:
            if hasattr(actor, '_serialized_parent_name') and actor._serialized_parent_name:
                parent = actor_map.get(actor._serialized_parent_name)
                if parent:
                    actor.setParent(parent)
                    
            # Clean up temporary serialization data
            if hasattr(actor, '_serialized_parent_name'):
                delattr(actor, '_serialized_parent_name')
            if hasattr(actor, '_serialized_children_names'):
                delattr(actor, '_serialized_children_names')
                
    def clearSerializationData(self) -> None:
        """Clear temporary serialization data."""
        if hasattr(self, '_serialized_parent_name'):
            delattr(self, '_serialized_parent_name')
        if hasattr(self, '_serialized_children_names'):
            delattr(self, '_serialized_children_names')

    def handleEvent(self, event) -> bool:
        """Handle an event and forward to components."""
        # Forward event to all components that can handle events
        for component in self.components:
            if component.enabled and hasattr(component, 'handle_event'):
                if component.handle_event(event):
                    return True  # Event was handled
        return False