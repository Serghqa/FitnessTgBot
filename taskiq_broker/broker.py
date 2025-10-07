import taskiq_aiogram

from nats.js.api import RetentionPolicy, StreamConfig

from taskiq import TaskiqScheduler
from taskiq_redis import RedisScheduleSource
from taskiq_nats import PullBasedJetStreamBroker


stream_config = StreamConfig(
    name='tg_bot_stream',
    retention=RetentionPolicy.WORK_QUEUE,
)

broker = PullBasedJetStreamBroker(
    servers="nats://localhost:4222",
    queue='taskiq_queue',
    stream_config=stream_config,
    )

taskiq_aiogram.init(
        broker=broker,
        dispatcher='main:dp',
        bot='main:bot',
    )

schedule_source = RedisScheduleSource("redis://localhost:6379/0")

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[schedule_source],
)
