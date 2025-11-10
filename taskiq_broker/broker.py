from nats.js.api import RetentionPolicy, StreamConfig

from taskiq import TaskiqScheduler
from taskiq_redis import RedisScheduleSource
from taskiq_nats import PullBasedJetStreamBroker


stream_config = StreamConfig(
    name='tg_bot_stream',
    retention=RetentionPolicy.WORK_QUEUE,
)

broker = PullBasedJetStreamBroker(
    servers="nats://nats:4222",
    queue='taskiq_queue',
    stream_config=stream_config,
    )

schedule_source = RedisScheduleSource("redis://redis:6379/0")

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[schedule_source],
)
