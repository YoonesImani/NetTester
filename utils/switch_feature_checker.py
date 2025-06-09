"""
Module to check if the switch supports features listed in tasks.md.
"""

import logging
from typing import Dict, List, Optional

# Define feature support based on switch model and IOS version
# This is a simplified example; you should expand this based on your actual switch models and versions
FEATURE_SUPPORT: Dict[str, Dict[str, List[str]]] = {
    "WS-C2960-24TT-L": {
        "15.0(2)SE": [
            "VLAN Testing",
            "MAC Learning Testing",
            "Port Testing",
            "Spanning Tree Testing",
            "Security Testing",
            "QoS Testing",
            "Monitoring and Management",
            "Configuration Management"
        ]
    },
    # Add more switch models and their supported features here
}

def check_feature_support(model: str, ios_version: str, feature: str) -> bool:
    """
    Check if the switch supports a specific feature based on its model and IOS version.

    Args:
        model (str): The switch model (e.g., "WS-C2960-24TT-L").
        ios_version (str): The IOS version of the switch (e.g., "15.0(2)SE").
        feature (str): The feature to check (e.g., "VLAN Testing").

    Returns:
        bool: True if the feature is supported, False otherwise.
    """
    if model in FEATURE_SUPPORT and ios_version in FEATURE_SUPPORT[model]:
        return feature in FEATURE_SUPPORT[model][ios_version]
    return False

def get_supported_features(model: str, ios_version: str) -> List[str]:
    """
    Get a list of features supported by the switch based on its model and IOS version.

    Args:
        model (str): The switch model (e.g., "WS-C2960-24TT-L").
        ios_version (str): The IOS version of the switch (e.g., "15.0(2)SE").

    Returns:
        List[str]: A list of supported features.
    """
    if model in FEATURE_SUPPORT and ios_version in FEATURE_SUPPORT[model]:
        return FEATURE_SUPPORT[model][ios_version]
    return []

def log_feature_support(model: str, ios_version: str, logger: logging.Logger) -> None:
    """
    Log the features supported by the switch.

    Args:
        model (str): The switch model (e.g., "WS-C2960-24TT-L").
        ios_version (str): The IOS version of the switch (e.g., "15.0(2)SE").
        logger (logging.Logger): Logger object for output.
    """
    supported_features = get_supported_features(model, ios_version)
    if supported_features:
        logger.info(f"Switch {model} (IOS {ios_version}) supports the following features:")
        for feature in supported_features:
            logger.info(f"- {feature}")
    else:
        logger.warning(f"No supported features found for switch {model} (IOS {ios_version}).") 