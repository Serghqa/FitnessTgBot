# nats_manager.py
import logging

from aiogram import Bot

from nats.aio.client import Client as Nats
from nats.aio.msg import Msg
from nats.js import JetStreamContext
from nats.js.api import StreamConfig

from notification import send_notification


class NatsManager:

    def __init__(self, bot: Bot, servers: list[str]):

        self.bot = bot
        self.servers = servers
        self.nc = Nats()
        self.js = None
        self.logger = logging.getLogger(__name__)

    async def connect(
        self,
        config: StreamConfig | None = None
    ) -> tuple[Nats, JetStreamContext]:

        """Подключение к NATS серверу и настройка JetStream"""

        try:
            await self.nc.connect(servers=self.servers)
            self.js: JetStreamContext = self.nc.jetstream()

            # Создаем поток для уведомлений
            await self.js.add_stream(
                config=config,
            )

            self.logger.info("Успешное подключение к NATS JetStream")

            return self.nc, self.js

        except Exception as error:
            self.logger.error(f"Ошибка подключения к NATS: {error}")

            return False

    async def on_message(self, msg: Msg):

        user_id: str = msg.headers.get('User-Id')
        text: str = msg.data.decode()

        try:
            await send_notification(self.bot, int(user_id), text)
            await msg.ack()

        except Exception:
            await msg.nak()

    async def publish_notification(
        self,
        subject: str,
        headers: dict,
        data_notification: str
    ) -> bool:

        """Публикация уведомления в JetStream"""

        try:
            ack = await self.js.publish(
                subject=subject,
                headers=headers,
                payload=data_notification.encode(),
            )

            self.logger.info(f"Уведомление опубликовано: {ack.seq}")

            return True

        except Exception as error:
            self.logger.error(f"Ошибка публикации уведомления: {error}")

            return False

    async def subscribe_to_notifications(
        self,
        durable: str,
        subject: str,
        stream: str
    ) -> bool:

        """Подписка на уведомления"""

        try:
            await self.js.subscribe(
                subject=subject,
                durable=durable,
                stream=stream,
                cb=self.on_message,
                manual_ack=True,
            )

            self.logger.info("Подписка на уведомления создана")

            return True

        except Exception as error:
            self.logger.error(f"Ошибка создания подписки: {error}")

            return False

    async def close(self):

        """Закрытие соединения"""

        await self.nc.close()
