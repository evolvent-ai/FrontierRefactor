#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
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

from __future__ import annotations

from typing import TYPE_CHECKING

import hydrogram
from hydrogram import raw, utils
from hydrogram.types.object import Object

if TYPE_CHECKING:
    from datetime import datetime


class EmojiStatus(Object):
    """A user emoji status.

    Parameters:
        custom_emoji_id (``int``, *optional*):
            Custom emoji id.

        until_date (:py:obj:`~datetime.datetime`, *optional*):
            Valid until date.

        title (``str``, *optional*):
            Title of the collectible.

        gift_id (``int``, *optional*):
            Gift collectible id.

        name (``str``, *optional*):
            Name of the collectible.

        pattern_custom_emoji_id (``int``, *optional*):
            Pattern emoji id.

        center_color (``int``, *optional*):
            Center color of the collectible emoji in decimal format.

        edge_color (``int``, *optional*):
            Edge color of the collectible emoji in decimal format.

        pattern_color (``int``, *optional*):
            Pattern color of the collectible emoji in decimal format.

        text_color (``int``, *optional*):
            Text color of the collectible emoji in decimal format.
    """

    def __init__(
        self,
        *,
        client: hydrogram.Client = None,
        custom_emoji_id: int | None = None,
        gift_id: int | None = None,
        until_date: datetime | None = None,
        title: str | None = None,
        name: str | None = None,
        pattern_custom_emoji_id: int | None = None,
        center_color: int | None = None,
        edge_color: int | None = None,
        pattern_color: int | None = None,
        text_color: int | None = None,
    ):
        super().__init__(client)

        self.custom_emoji_id = custom_emoji_id
        self.gift_id = gift_id
        self.until_date = until_date
        self.title = title
        self.name = name
        self.pattern_custom_emoji_id = pattern_custom_emoji_id
        self.center_color = center_color
        self.edge_color = edge_color
        self.pattern_color = pattern_color
        self.text_color = text_color

    @staticmethod
    def _parse(client, emoji_status: raw.base.EmojiStatus) -> EmojiStatus | None:
        if isinstance(emoji_status, raw.types.EmojiStatus):
            return EmojiStatus(
                client=client,
                custom_emoji_id=emoji_status.document_id,
                until_date=utils.timestamp_to_datetime(getattr(emoji_status, "until", None)),
            )

        if isinstance(emoji_status, raw.types.EmojiStatusCollectible):
            return EmojiStatus(
                client=client,
                custom_emoji_id=emoji_status.document_id,
                gift_id=emoji_status.collectible_id,
                until_date=utils.timestamp_to_datetime(getattr(emoji_status, "until", None)),
                title=emoji_status.title,
                name=emoji_status.slug,
                pattern_custom_emoji_id=emoji_status.pattern_document_id,
                center_color=emoji_status.center_color,
                edge_color=emoji_status.edge_color,
                pattern_color=emoji_status.pattern_color,
                text_color=emoji_status.text_color,
            )

        return None

    def write(self):
        if self.gift_id:
            return raw.types.InputEmojiStatusCollectible(
                collectible_id=self.gift_id, until=utils.datetime_to_timestamp(self.until_date)
            )

        return raw.types.EmojiStatus(
            document_id=self.custom_emoji_id, until=utils.datetime_to_timestamp(self.until_date)
        )
