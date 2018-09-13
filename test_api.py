# encoding: utf-8
import json

from alembic.config import Config
from alembic.command import upgrade, downgrade
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from models import Student


app.config.DB_SETTINGS['database'] = 'sber_test_test'


def get_alembic_config():
    """
    Возвращает alembic.config.Config, который отличается от оригинального
    только заменённым именем БД, чтобы все манипуляции с данными происходили в БД для тестов.

    :return:  alembic.config.Config
    """
    config = Config('alembic.ini')
    sqlalchemy_url = config.get_main_option('sqlalchemy.url')

    # Подменяем db_url для тестовой БД.
    # Подразумевается, что тестовая БД от продуктовой отличается только названием,
    # находится на том же сервере и доступна для того же пользователя, что и продуктовая.
    last_slash_index = sqlalchemy_url.rfind('/')
    new_db_url = sqlalchemy_url[:last_slash_index+1] + app.config.DB_SETTINGS['database']

    config.set_main_option('sqlalchemy.url', new_db_url)
    return config


alembic_config = get_alembic_config()


def setup_function():
    """ В начале запуска каждого теста запускаем миграцию БД. """
    upgrade(alembic_config, 'head')


def teardown_function():
    """ После каждого теста приводим БД к 'нулевому' состоянию. """
    downgrade(alembic_config, 'base')


def create_new_student(name):
    """
    Создаёт нового Студента, возвращает id вновь созданного Студента.

    :return: int, id нового студента
    """
    engine = create_engine(
        'postgresql://{user}:{password}@{host}/{database}'.format(
            **app.config.DB_SETTINGS
        )
    )
    Session = sessionmaker(bind=engine)
    session = Session()

    new_student = Student(name=name)
    session.add(new_student)
    session.commit()
    new_student_id = new_student.id
    session.close()
    return new_student_id


### TESTS ###

def test_get_students_list():
    _, response = app.test_client.get('/students')
    print('response: ', response)
    assert response.status == 200
    assert response.json


def test_post_student():
    # Посылаем НЕ json
    _, response = app.test_client.post('/students', data='some data')
    assert response.status == 400

    # Посылаем json с неправильным полем
    bad_data = {'surname': 'Petrov'}
    _, response = app.test_client.post('/students', data=json.dumps(bad_data))
    assert response.status == 400

    # Посылаем json с правильным полем
    data = {'name': 'Vasiliy'}
    _, response = app.test_client.post('/students', data=json.dumps(data))
    assert response.status == 200
    assert response.json
    for expected_filed in  ['id', 'name', 'created_at', 'active']:
        assert expected_filed in response.json


def test_get_student_detail():
    new_student_id = create_new_student('Vasiliy')

    # неправильный ид
    _, response = app.test_client.get('/students/9999')
    assert response.status == 404

    # правильный ид
    _, response = app.test_client.get('/students/{0}'.format(new_student_id))
    assert response.status == 200
    assert response.json['name'] == 'Vasiliy'

    for expected_filed in  ['id', 'name', 'created_at', 'active']:
        assert expected_filed in response.json


def test_delete_student():
    new_student_id = create_new_student('Vasiliy')

    # неправильный ид
    _, response = app.test_client.delete('/students/9999')
    assert response.status == 404

    # правильный ид
    _, response = app.test_client.delete('/students/{0}'.format(new_student_id))
    assert response.status == 204


def test_put_student():
    new_student_id = create_new_student('Vasiliy')

    new_data = {'name': 'Ivan', 'active': False}
    # неправильный ид
    _, response = app.test_client.put('/students/9999', data=json.dumps(new_data))
    assert response.status == 404

    # неправильный формат данных
    _, response = app.test_client.put('/students/{0}'.format(new_student_id), data='new_data')
    assert response.status == 400

    # не те поля
    bad_data = {'created_at': '2018-09-12 17:45:06.502463', 'id': 10}
    _, response = app.test_client.put('/students/{0}'.format(new_student_id), data=json.dumps(bad_data))
    assert response.status == 400

    # пытаемся перезаписать поля, недоступные для редактирования
    tricky_data = {
        'id': 9999,
        'name': 'Ivan',
        'created_at': '1010-09-12 17:45:06.502463',
        'active': False
    }
    _, response = app.test_client.put('/students/{0}'.format(new_student_id), data=json.dumps(tricky_data))
    assert response.status == 200
    assert response.json['id'] != 9999
    assert response.json['created_at'] != '1010-09-12 17:45:06.502463'

    # всё ок
    _, response = app.test_client.put('/students/{0}'.format(new_student_id), data=json.dumps(new_data))
    assert response.status == 200

    for expected_filed in  ['id', 'name', 'created_at', 'active']:
        assert expected_filed in response.json
