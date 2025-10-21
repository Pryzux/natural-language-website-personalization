"""all available action types that can be applied to DOM elements."""

from .types import Action

ACTION_DEFINITIONS = [

    Action(
        action="color",
        description="Modify color properties",
        param_examples={
            "background-color": "#E0F7FA",
            "color": "rgb(255, 0, 0)",
            "border-color": "blue"
        }
    ),

    Action(
        action="text",
        description="Modify text content of elements",
        param_examples={
            "replace": "New text content"
        }
    ),

    Action(
        action="layout",
        description="Modify layout properties (positioning, sizing, spacing)",
        param_examples={
            "margin": "10px",
            "padding": "20px",
            "width": "100%",
            "height": "200px",
            "display": "flex",
            "flex-direction": "column"
        }
    ),

    Action(
        action="visibility",
        description="Control element visibility",
        param_examples={
            "display": "none",
            "visibility": "hidden",
            "opacity": "0.5"
        }
    ),

    Action(
        action="style",
        description="Apply any other CSS styles not covered by specific actions",
        param_examples={
            "font-size": "18px",
            "font-weight": "bold",
            "border-radius": "10px",
            "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
            "transition": "all 0.3s ease"
        }
    )

]
