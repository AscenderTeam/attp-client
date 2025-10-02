"""ATTP Client Library

A Python client library for the ATTP (Agent Transfer Transfer Protocol) framework.
"""

# Main client class
from .client import ATTPClient

# Core API classes
from .catalog import AttpCatalog
from .inference import AttpInferenceAPI
from .router import AttpRouter
from .session import SessionDriver
from .tools import ToolsManager

# Exception classes
from .errors.attp_exception import AttpException
from .errors.correlated_rpc_exception import CorrelatedRPCException
from .errors.dead_session import DeadSessionError
from .errors.not_found import NotFoundError
from .errors.serialization_error import SerializationError
from .errors.unauthenticated_error import UnauthenticatedError

# Interface classes
from .interfaces.error import IErr
from .interfaces.route_mappings import IRouteMapping
from .interfaces.catalogs.catalog import ICatalogResponse
from .interfaces.catalogs.tools.envelope import IEnvelope
from .interfaces.handshake.auth import IAuth
from .interfaces.handshake.hello import IHello
from .interfaces.handshake.ready import IReady
from .interfaces.inference.message import IMessageResponse, IMessageDTOV2
from .interfaces.inference.tool import ToolV2
from .interfaces.inference.enums.message_data_type import MessageDataTypeEnum
from .interfaces.inference.enums.message_emergency_type import MessageEmergencyTypeEnum
from .interfaces.inference.enums.message_type import MessageTypeEnum

# Type definitions
from .types.route_mapping import AttpRouteMapping, RouteType

# Utility classes
from .utils.context_awaiter import ContextAwaiter
from .utils.route_mapper import resolve_route_by_id
from .utils.serializer import serialize, deserialize

# Misc classes
from .misc.fixed_basemodel import FixedBaseModel
from .misc.serializable import Serializable

# Constants
from .consts import ATTP_VERSION

__version__ = "0.1.0"
__all__ = [
    # Main client
    "ATTPClient",
    
    # Core API classes
    "AttpCatalog",
    "AttpInferenceAPI", 
    "AttpRouter",
    "SessionDriver",
    "ToolsManager",
    
    # Exceptions
    "AttpException",
    "CorrelatedRPCException",
    "DeadSessionError",
    "NotFoundError",
    "SerializationError",
    "UnauthenticatedError",
    
    # Interfaces
    "IErr",
    "IRouteMapping",
    "ICatalogResponse",
    "IEnvelope",
    "IAuth",
    "IHello",
    "IReady",
    "IMessageResponse",
    "IMessageDTOV2",
    "ToolV2",
    "MessageDataTypeEnum",
    "MessageEmergencyTypeEnum",
    "MessageTypeEnum",
    
    # Types
    "AttpRouteMapping",
    "RouteType",
    
    # Utils
    "ContextAwaiter",
    "resolve_route_by_id",
    "serialize",
    "deserialize",
    
    # Misc
    "FixedBaseModel",
    "Serializable",
    
    # Constants
    "ATTP_VERSION",
]