import sys
import datetime


from flask import Flask
from flask_restful import Resource, Api, reqparse, inputs
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields


app = Flask('super-app')
api = Api(app)
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///name.db'


class TaskSchema(Schema):
    class Meta:
        ordered = True
    message = fields.String()
    date = fields.String()
    event = fields.String()


class Database(db.Model):
    __tablename__ = 'Calendar Events'
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String(300), nullable=False)
    date = db.Column(db.Date, nullable=False)


db.create_all()


class EventID(Resource):
    @staticmethod
    def get(event_id):
        event = Database.query.filter(Database.id == event_id).first()
        if event:
            return {'id': event.id, 'event': event.event, 'date': str(event.date)}
        return {"message": "The event doesn't exist!"}, 404

    @staticmethod
    def delete(event_id):
        event = Database.query.filter(Database.id == event_id).first()
        if event:
            db.session.delete(event)
            db.session.commit()
            return {"message": "The event has been deleted!"}
        return {"message": "The event doesn't exist!"}, 404


class TodayEvent(Resource):
    @staticmethod
    def get():
        today = datetime.date.today()
        today_events = []
        for row in Database.query.all():
            if row.date == today:
                today_events.append({'id': row.id, 'event': row.event, 'date': str(row.date)})
        return today_events


class Event(Resource):
    @staticmethod
    def get():
        get_parser = reqparse.RequestParser()
        get_parser.add_argument('start_time',
                                type=inputs.date)
        get_parser.add_argument('end_time',
                                type=inputs.date)
        data = get_parser.parse_args()

        all_events = []
        for row in Database.query.all():
            all_events.append({'id': row.id, 'event': row.event, 'date': str(row.date)})

        if data['start_time']:
            data['start_time'] = data['start_time'].date()
            data['end_time'] = data['end_time'].date()

            entered_events = []
            for row in Database.query.all():
                if data['end_time'] >= row.date >= data['start_time']:
                    entered_events.append({'id': row.id, 'event': row.event, 'date': str(row.date)})
            return entered_events

        return all_events

    @staticmethod
    def post():
        schema = TaskSchema()
        post_parser = reqparse.RequestParser()
        post_parser.add_argument('message',
                                 type=str,
                                 default='The event has been added!'
                                 )

        post_parser.add_argument('date',
                                 type=inputs.date,
                                 help='The event date with the correct format is required! The correct format is YYYY-MM-DD!',
                                 required=True)
        post_parser.add_argument('event',
                                 type=str,
                                 help='The event name is required!',
                                 required=True)
        data = post_parser.parse_args()
        data['date'] = data['date'].date()
        if data:
            new_event = Database(event=data['event'], date=data['date'])
            db.session.add(new_event)
            db.session.commit()

        return schema.dump(data)


api.add_resource(EventID, '/event/<int:event_id>')
api.add_resource(TodayEvent, '/event/today')
api.add_resource(Event, '/event')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
