def test_data_all_none(data: dict):

    assert all(attr is None for attr in data.values()), 'the values ​​of all attributes must be None'


def test_trainer_true(data: dict):

    assert data['trainer'], 'attribute must be True'
    assert data['client'] is None, 'client must be None'
    assert data['id'] == 6831061444, 'id does not match'
    assert data['name'] == 'Sergh', 'sergh does not match'
    assert data['group'] is None, 'group must be None'
    assert data['workouts'] is None, 'workouts must be None'
    assert data['trainer_id'] is None, 'trainer_id must be None'


def test_group_true(data: dict):

    assert data['trainer'], 'attribute must be True'
    assert data['client'] is None, 'client must be None'
    assert data['id'] == 6831061444, 'id does not match'
    assert data['name'] == 'Sergh', 'sergh does not match'
    assert isinstance(data['group'], list), 'group must be List'
    assert data['workouts'] is None, 'workouts must be None'
    assert data['trainer_id'] is None, 'trainer_id must be None'
    assert isinstance(data['frame'], dict), 'frame must be Dict'


    for client in data['group']:
        assert client['client'], 'client must be True'
        assert client['trainer_id'] == 6831061444, 'trainer_id must be 6831061444'


def test_not_data(data: dict):

    assert len(data) == 0, 'data must be empty'
