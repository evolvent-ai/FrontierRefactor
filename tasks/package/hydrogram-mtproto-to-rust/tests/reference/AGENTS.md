# Hydrogram AGENTS.md

## Project Overview

Hydrogram is a Python MTProto client library for the Telegram API. It's an async-first framework supporting Python 3.9+ (CPython and PyPy), forked from Pyrogram with continued development.

**Key Characteristics:**
- **License**: LGPL-3.0
- **Python**: 3.9+ (supports CPython and PyPy)
- **Architecture**: Async/await-based with optional uvloop support
- **Crypto**: Uses pyaes (pure Python) or TgCrypto (C extension for performance)

---

## Project Structure

```
hydrogram/
├── client.py              # Main Client class (extends Methods)
├── methods/               # API method implementations
│   ├── __init__.py        # Methods class (mixin of all method categories)
│   ├── auth/             # Authentication methods
│   ├── messages/         # Message operations
│   ├── chats/            # Chat/channel operations
│   ├── users/            # User operations
│   ├── bots/             # Bot-specific methods
│   ├── advanced/         # Advanced MTProto methods
│   ├── utilities/        # Utility methods (idle, compose, handlers)
│   └── pyromod/          # pyromod extensions (get_listener, etc.)
├── types/                # Telegram API type definitions
│   ├── object.py         # Base Object class
│   ├── user_and_chats/   # User, Chat, etc.
│   ├── messages_and_media/  # Message, Photo, etc.
│   ├── input_media/      # Input media types
│   └── input_message_content/  # Input content types
├── filters.py            # Message/update filters
├── handlers/             # Handler classes
├── dispatcher.py         # Update dispatching
├── session/              # MTProto session management
│   ├── session.py
│   └── internals/
├── connection/           # Network connection layer
│   ├── connection.py
│   └── transport/tcp/    # TCP transports (abridged, intermediate, full)
├── storage/              # Session storage backends
│   ├── base.py          # Abstract base
│   └── sqlite_storage.py
├── crypto/               # Cryptographic operations
├── raw/                    # Raw MTProto layer (auto-generated)
├── enums/                  # Enumeration definitions
├── errors/                 # Exception classes
├── parser/                 # HTML/Markdown parsers
└── helpers/                # Utility helpers
```

---

## Code Style & Standards

### Linting & Formatting
- **Ruff** is used for both linting and formatting (line length: 99)
- Pre-commit hooks enforce style
- Run `ruff check .` before committing

### Key Ruff Rules (ruff.toml)
- `FURB` - refurb suggestions
- `I` - isort import sorting
- `E`, `W` - pycodestyle
- `UP` - pyupgrade
- `SIM` - simplification
- `PERF` - performance lints
- `N` - PEP8 naming
- `FA` - future annotations
- Type-checking imports in `TYPE_CHECKING` blocks

### Code Patterns

**1. License Header**
All new Python files must include the following LGPL header:

```python
#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2023-present Hydrogram <https://hydrogram.org>
#
#  This file is part of Hydrogram.
#
#  Hydrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Hydrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Hydrogram.  If not, see <http://www.gnu.org/licenses/>.
```

**Note**: Existing files retain both copyright holders (Dan + Hydrogram). New files should ONLY have the Hydrogram copyright line.

**2. Future Annotations**
Always use `from __future__ import annotations` for forward references.

**3. Type Hinting**
- Full type hints on all public APIs
- Use `TYPE_CHECKING` blocks for circular imports
- Prefer `str | None` over `Optional[str]` (Python 3.10+ style)

---

## Architecture Patterns

### 1. Client Class Hierarchy
```python
# methods/__init__.py
class Methods(
    Advanced, Auth, Bots, Contacts, Password, Chats,
    Users, Messages, Pyromod, Decorators, Utilities, InviteLinks, Phone
):
    pass

# client.py
class Client(Methods):
    """Main client class, inherits all methods"""
```

### 2. Object Model (types/object.py)
All Telegram types inherit from `Object`:
```python
class Object:
    def __init__(self, client: "hydrogram.Client" = None):
        self._client = client

    def bind(self, client: "hydrogram.Client"):
        """Bind client to this and nested objects"""

    def __str__(self) -> str:  # JSON serialization
    def __repr__(self) -> str:  # Python repr
    def __eq__(self, other) -> bool:  # Deep equality
```

### 3. Method Implementation Pattern
```python
from __future__ import annotations

from typing import TYPE_CHECKING

import hydrogram
from hydrogram import enums, raw, types, utils

if TYPE_CHECKING:
    from datetime import datetime


class SendMessage:  # Class name in PascalCase matching method name
    async def send_message(
        self: hydrogram.Client,
        chat_id: int | str,
        text: str,
        *,  # Force keyword-only arguments after required params
        message_thread_id: int | None = None,
        parse_mode: enums.ParseMode | None = None,
        entities: list[types.MessageEntity] | None = None,
        disable_web_page_preview: bool | None = None,
        disable_notification: bool | None = None,
        reply_to_message_id: int | None = None,
        schedule_date: datetime | None = None,
        protect_content: bool | None = None,
        reply_markup: types.InlineKeyboardMarkup
        | types.ReplyKeyboardMarkup
        | types.ReplyKeyboardRemove
        | types.ForceReply = None,
    ) -> types.Message:
        """Send text messages.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).

            text (``str``):
                Text of the message to be sent.

            message_thread_id (``int``, *optional*):
                Unique identifier for the target message thread (topic) of the forum.
                for forum supergroups only.

            parse_mode (:obj:`~hydrogram.enums.ParseMode`, *optional*):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.

            entities (List of :obj:`~hydrogram.types.MessageEntity`):
                List of special entities that appear in message text, which can be specified instead of *parse_mode*.

            disable_web_page_preview (``bool``, *optional*):
                Disables link previews for links in this message.

            disable_notification (``bool``, *optional*):
                Sends the message silently.
                Users will receive a notification with no sound.

        Returns:
            :obj:`~hydrogram.types.Message`: On success, the sent message is returned.

        Example:
            .. code-block:: python

                # Simple send
                await app.send_message(chat_id, "Hello")

                # With formatting
                await app.send_message(chat_id, "**Bold** text", parse_mode=enums.ParseMode.MARKDOWN)
        """
        # Method implementation...
```

**CRITICAL**: After creating the method file, you MUST add it to the category mixin class:

```python
# File: hydrogram/methods/messages/__init__.py
from .send_message import SendMessage  # Import the new method class
# ... other imports ...

class Messages(
    # ... other method classes ...
    SendMessage,  # Add the class here (inherits the method)
):
    pass
```

The mixin class inherits from all individual method classes, making their methods available on the Client via multiple inheritance.

### 4. Filter System (filters.py)
Filters are callable classes:
```python
class Filter:
    async def __call__(self, client: hydrogram.Client, update: Update) -> bool:
        raise NotImplementedError

    # Support logical operators
    def __invert__(self) -> InvertFilter
    def __and__(self, other: Filter) -> AndFilter
    def __or__(self, other: Filter) -> OrFilter
```

Built-in filters: `filters.command`, `filters.private`, `filters.chat`, etc.

### 5. Handler Pattern (handlers/)
Handlers wrap callback functions:
```python
from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    import hydrogram
    from hydrogram.filters import Filter
    from hydrogram.types import Update


class Handler:
    def __init__(self, callback: Callable, filters: Filter | None = None):
        self.callback = callback
        self.filters = filters

    async def check(self, client: hydrogram.Client, update: Update):
        if callable(self.filters):
            if inspect.iscoroutinefunction(self.filters.__call__):
                return await self.filters(client, update)
            return await client.loop.run_in_executor(client.executor, self.filters, client, update)

        return True
```

Specialized handlers inherit from Handler:
- `MessageHandler`
- `CallbackQueryHandler`
- `InlineQueryHandler`
- etc.

### 6. Storage Pattern (storage/)
Storage backends implement `BaseStorage`:
```python
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Union

from hydrogram import raw

InputPeer = Union[raw.types.InputPeerUser, raw.types.InputPeerChat, raw.types.InputPeerChannel]


class BaseStorage(ABC):
    """Abstract base class for storage engines."""

    SESSION_STRING_FORMAT: str = ">BI?256sQ?"

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    async def open(self) -> None: ...

    @abstractmethod
    async def save(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...

    @abstractmethod
    async def dc_id(self, value: int | None = None) -> int: ...

    @abstractmethod
    async def api_id(self, value: int | None = None) -> int: ...

    @abstractmethod
    async def auth_key(self, value: bytes | None = None) -> bytes: ...

    @abstractmethod
    async def update_peers(self, peers: list[tuple[int, int, str, str, str]]) -> None: ...

    @abstractmethod
    async def get_peer_by_id(self, peer_id: int) -> InputPeer: ...
```

### 7. Error Hierarchy (errors/)
```python
# Custom exceptions for RPC errors
class SomeTelegramError(Exception):
    """Description of when this occurs"""
```

---

## Testing Patterns

### Test Structure
Tests use pytest and follow this pattern:

```python
#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2023-present Hydrogram <https://hydrogram.org>
#
#  This file is part of Hydrogram.
#  ... (license header)

import pytest

from hydrogram.module import ThingToTest


def test_something():
    result = ThingToTest.method()
    assert result == expected


async def test_async_something():
    result = await ThingToTest.async_method()
    assert result == expected
```

### Running Tests
```bash
pytest tests/           # Run all tests
pytest tests/test_file.py::test_func  # Run specific test
pytest --cov=hydrogram  # With coverage
```

---

## Development Workflow

### Dependencies
- Use `uv` for dependency management: `uv sync --all-extras`
- Dev dependencies: ruff, pytest, pre-commit, httpx, lxml, hatchling
- Optional: tgcrypto, uvloop (for performance)

### Testing
```bash
pytest tests/           # Run all tests
pytest tests/test_file.py::test_func  # Run specific test
pytest --cov=hydrogram  # With coverage
```

### Pre-commit
```bash
pre-commit install     # Install hooks
pre-commit run --all-files  # Run manually
```

### Code Generation
The compiler generates raw MTProto layer from TL schema:
- `compiler/api/` - API schema compiler
- `compiler/errors/` - Error compiler
- `compiler/docs/` - Documentation compiler

Run via hatch build hooks.

---

## Adding New Features

### New Method
1. Create method file in appropriate category (e.g., `methods/messages/send_sticker.py`)
2. Follow signature pattern with type hints (see Method Implementation Pattern above)
3. Include docstring with Parameters/Returns sections
4. **IMPORTANT**: Import and add to category mixin class in `methods/<category>/__init__.py`
5. Write test in `tests/`
6. Add news fragment: `news/<issue>.feature.rst`

### New Type
1. Create in appropriate `types/` subpackage
2. Inherit from `Object`
3. Define `__init__` with all fields
4. Add to subpackage `__init__.py`
5. Add to main `types/__init__.py`

### New Filter
1. Add to `filters.py`
2. Create filter class inheriting from `Filter` or use filter decorator
3. Export in `filters` module

---

## Common Gotchas

1. **Async Context**: All API calls are async - never use blocking I/O
2. **Client Binding**: Objects must be bound to a client to use bound methods
3. **Raw Layer**: Use `raw` module for low-level MTProto if high-level API lacks something
4. **Session Storage**: SQLite is default; storage is pluggable via `BaseStorage`
5. **Crypto Executor**: CPU-intensive crypto runs in `ThreadPoolExecutor(1)`

---

## Documentation

- Sphinx docs in `docs/`
- Live preview: `sphinx-autobuild docs/source/ docs/build/ --watch hydrogram/`
- Follow Google docstring style
- Reference external Telegram docs where applicable

---

## Release Process

- Uses `towncrier` for changelog management
- Fragments in `news/` directory:
  - `.feature.rst` - new features
  - `.bugfix.rst` - bug fixes
  - `.doc.rst` - documentation
  - `.removal.rst` - deprecations
  - `.misc.rst` - other changes
- Version defined in `hydrogram/__init__.py:__version__`

---

## Important Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project config, dependencies, hatch build |
| `ruff.toml` | Linting/formatting rules |
| `hatch_build.py` | Custom build hooks (generates raw layer) |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `compiler/api/source/main_api.tl` | TL schema source |
| `hydrogram/__init__.py` | Public API exports |

---

## Resources

- Docs: https://docs.hydrogram.org
- Homepage: https://hydrogram.org
- Telegram: https://t.me/HydrogramNews
- Issues: https://github.com/hydrogram/hydrogram/issues
- Based on: https://github.com/pyrogram/pyrogram
