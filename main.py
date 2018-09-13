from aiopg.sa import create_engine
from sanic import Sanic
from sanic.views import HTTPMethodView
from sanic import response
from sanic.exceptions import ServerError
from sqlalchemy import select, update

from models import Student


app = Sanic()
app.config.DB_SETTINGS = {
    'user': 'postgres',
    'password': '',
    'database': 'sber_test',
    'host': 'db'
}


async def get_student(conn, by_id):
    """
    Возвращает из БД соварь с данными о Студенте.

    :param conn: aiopg.Connection
    :param by_id: id Студента
    :return: dict, данные о Студенте
    """
    query = select([Student.__table__]).where(Student.id==by_id)
    results = await conn.execute(query)
    item = await results.fetchone()
    if not item:
        raise ServerError('Student not found.', status_code=404)
    return {
        'id': item.id,
        'name': item.name,
        'created_at': str(item.created_at),
        'active': item.active
    }


class StudentsListView(HTTPMethodView):

    async def get(self, request):
        async with create_engine(**app.config.DB_SETTINGS) as engine:
            async with engine.acquire() as conn:
                query = select([Student])
                results = await conn.execute(query)
                return response.json([
                    {
                        'id': item.id,
                        'name': item.name,
                        'created_at': str(item.created_at),
                        'active': item.active
                    } for item in results
                ])

    async def post(self, request):
        if not 'name' in request.json:
            raise ServerError('Student has to have "name" field.', status_code=400)
        new_student_name = request.json['name']

        async with create_engine(**app.config.DB_SETTINGS) as engine:
            async with engine.acquire() as conn:
                new_student_id = await conn.scalar(
                    Student.__table__.insert().values(name=new_student_name)
                )
                query = select([Student.__table__]).where(Student.id==new_student_id)
                results = await conn.execute(query)
                item = await results.fetchone()
                return response.json({
                    'id': item.id,
                    'name': item.name,
                    'created_at': str(item.created_at),
                    'active': item.active
                })


class StudentsDetailView(HTTPMethodView):

    async def get(self, request, student_id):
        async with create_engine(**app.config.DB_SETTINGS) as engine:
            async with engine.acquire() as conn:
                student_data = await get_student(conn, student_id)
                return response.json(student_data)

    async def put(self, request, student_id):
        update_data = request.json
        if not ('name' in  update_data and
                'active' in  update_data):
            raise ServerError('Student has to have "name" and "active" fields.', status_code=400)

        query = update(Student)\
        .where(Student.id==student_id)\
        .values(
            name=update_data['name'],
            active=update_data['active']
        )

        async with create_engine(**app.config.DB_SETTINGS) as engine:
            async with engine.acquire() as conn:

                results = await conn.execute(query)
                if not results.rowcount:
                    raise ServerError('Student not found.', status_code=404)

                student_data = await get_student(conn, student_id)
                return response.json(student_data)

    async def delete(self, request, student_id):
        async with create_engine(**app.config.DB_SETTINGS) as engine:
            async with engine.acquire() as conn:
                query = Student.__table__.delete().where(Student.id==student_id)
                results = await conn.execute(query)
                if not results.rowcount:
                    raise ServerError('Student not found.', status_code=404)

                return response.json({}, status=204 )


app.add_route(StudentsListView.as_view(), '/students')
app.add_route(StudentsDetailView.as_view(), '/students/<student_id:int>')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)


