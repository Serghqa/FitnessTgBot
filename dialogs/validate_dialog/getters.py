import logging

from tmp_db import data_base

logger = logging.getLogger(__name__)


async def get_data(**kwargs):
    user_id = str(kwargs['event_from_user'].id)
    is_trainer = user_id in data_base['trainers']
    is_client = user_id in data_base['clients']
    return {
        'user': is_trainer or is_client,
        'trainer': is_trainer,
        'client': is_client
    }
