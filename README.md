# ATTP Client

A Python SDK client for interacting with AgentHub's ATTP (Agent Tool Transport Protocol).

## Overview

The ATTP Client provides a comprehensive Python interface for connecting to and interacting with AgentHub's ATTP protocol. It enables real-time communication with AI agents, tool management, and inference operations through a high-performance async/await interface.

## Features

- **Async/Await Support**: Built with modern Python async patterns for optimal performance
- **Agent Communication**: Direct communication with AI agents through the ATTP protocol
- **Tool Management**: Register, unregister, and manage tools in organized catalogs
- **Inference API**: Invoke AI agent inference with configurable parameters
- **Real-time Messaging**: Stream responses and handle real-time agent interactions
- **Event Handling**: Register custom event handlers for connect/disconnect and custom routes
- **Authentication**: Secure token-based authentication with organization support

## Installation

```bash
pip install attp-client
```

Or with Poetry:

```bash
poetry add attp-client
```

## Quick Start

### Basic Connection

```python
import asyncio
from attp_client.client import ATTPClient

async def main():
    # Initialize the client
    client = ATTPClient(
        agt_token="your_agent_token_here",
        organization_id=1,
        connection_url="attp://localhost:6563"  # Optional, defaults to localhost
    )
    
    # Connect to AgentHub
    await client.connect()
    
    # Your code here...
    
    # Close the connection
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Agent Inference

```python
from attp_client.interfaces.inference.message import IMessageDTOV2
from attp_client.interfaces.inference.enums.message_type import MessageTypeEnum
from uuid import UUID

# Invoke inference by agent ID
response = await client.inference.invoke_inference(
    agent_id=17,
    input_configuration={},
    messages=[
        IMessageDTOV2(
            content="Hello, how can you help me?",
            message_type=MessageTypeEnum.USER_MESSAGE,
            chat_id=UUID("your-chat-id-here")
        )
    ],
    stream=False,
    timeout=30
)

print("Agent response:", response)
```

### Tool Management

```python
# Register a tool
tool_id = await client.tools.register(
    catalog_name="my_catalog",
    name="example_tool",
    description="An example tool for demonstration",
    schema_id="tool_schema_v1",
    return_direct=False,
    timeout_ms=20000
)

# Access a specific catalog
catalog = await client.catalog("my_catalog")

# Unregister a tool
await client.tools.unregister("my_catalog", str(tool_id))
```

### Event Handling

```python
def on_connect():
    print("Connected to AgentHub!")

def on_disconnect():
    print("Disconnected from AgentHub!")

def handle_custom_event(data):
    print(f"Received custom event: {data}")

# Register event handlers
client.add_event_handler("", "connect", on_connect)
client.add_event_handler("", "disconnect", on_disconnect)
client.add_event_handler("custom:pattern", "custom", handle_custom_event)
```

## Configuration

### Client Parameters

- `agt_token` (str): Your AgentHub authentication token
- `organization_id` (int): Your organization ID
- `connection_url` (str, optional): ATTP server URL (default: "attp://localhost:6563")
- `max_retries` (int, optional): Maximum connection retry attempts (default: 20)
- `limits` (Limits, optional): Connection limits configuration
- `logger` (Logger, optional): Custom logger instance

### Connection Limits

```python
from attp_core.rs_api import Limits

limits = Limits(max_payload_size=50000)
client = ATTPClient(
    agt_token="...",
    organization_id=1,
    limits=limits
)
```

## API Reference

### ATTPClient

The main client class for ATTP communication.

#### Methods

- `connect()`: Establish connection to AgentHub
- `close()`: Close the connection
- `catalog(catalog_name: str)`: Access a specific tool catalog
- `add_event_handler(pattern: str, route_type: RouteType, callback: Callable)`: Register event handlers

#### Properties

- `inference`: Access to the inference API
- `tools`: Access to the tools manager
- `router`: Access to the low-level router

### AttpInferenceAPI

Handles AI agent inference operations.

#### Methods

- `invoke_inference()`: Invoke inference for a specific agent
- `invoke_chat_inference()`: Invoke inference for a chat session

### ToolsManager

Manages tool registration and organization.

#### Methods

- `register()`: Register a new tool
- `unregister()`: Remove tool registration

## Error Handling

The client includes comprehensive error handling:

```python
from attp_client.errors import (
    AttpException,
    DeadSessionError,
    NotFoundError,
    SerializationError,
    UnauthenticatedError
)

try:
    await client.connect()
except UnauthenticatedError:
    print("Authentication failed - check your token")
except DeadSessionError:
    print("Session has died - reconnection required")
except AttpException as e:
    print(f"ATTP error: {e}")
```

## Requirements

- Python 3.11 - 3.13
- Dependencies:
  - `pydantic` (>=2.11.7,<3.0.0)
  - `attp-core` (==0.1.10)
  - `msgpack` (>=1.1.1,<2.0.0)
  - `ascender-framework` (>=2.0rc7,<3.0)

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/AscenderTeam/attp-client.git
cd attp-client

# Install dependencies
poetry install

# Run tests
python -m pytest tests/
```

### Project Structure

```
src/
├── attp_client/           # Main package
│   ├── client.py         # Main client class
│   ├── inference.py      # AI inference API
│   ├── tools.py          # Tool management
│   ├── catalog.py        # Catalog operations
│   ├── router.py         # Message routing
│   ├── session.py        # Session management
│   ├── errors/           # Exception classes
│   ├── interfaces/       # Protocol interfaces
│   ├── misc/             # Utilities
│   ├── types/            # Type definitions
│   └── utils/            # Helper utilities
└── tests/                # Test suite
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please use the GitHub Issues page or contact the Ascender Team.