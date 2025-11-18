from .broker import broker, scheduler
from common import bot, Session


broker.add_dependency_context({'bot': bot, 'session': Session})
