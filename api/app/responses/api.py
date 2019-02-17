import flask_restful as restful
from flask import g, request
import datetime
from flask_restful import reqparse, fields, marshal_with
from app.applicationModel.mixins import ApplicationFormMixin
from app.responses.models import Response, Answer
from app.applicationModel.models import ApplicationForm
from app.events.models import Event
from app.utils.auth import auth_required

from app.utils import errors

from app import db, bcrypt

# TODO: Refactor ApplicationFormMixin
class ResponseAPI(ApplicationFormMixin, restful.Resource):

    answer_fields = {
        'id': fields.Integer,
        'question_id': fields.Integer,
        'value': fields.String
    }

    response_fields = {
        'id': fields.Integer,
        'application_form_id': fields.Integer,
        'user_id': fields.Integer,
        'is_submitted': fields.Boolean,
        'submitted_timestamp': fields.DateTime(dt_format='iso8601'),
        'is_withdrawn': fields.Boolean,
        'withdrawn_timestamp': fields.DateTime(dt_format='iso8601'),
        'started_timestamp': fields.DateTime(dt_format='iso8601'),
        'answers': fields.List(fields.Nested(answer_fields))
    }

    @auth_required
    @marshal_with(response_fields)
    def get(self):
        args = self.req_parser.parse_args()

        try:
            event = db.session.query(Event).filter(Event.id == args['event_id']).first()
            if not event:
                return errors.EVENT_NOT_FOUND

            form = db.session.query(ApplicationForm).filter(ApplicationForm.event_id == args['event_id']).first()     
            if not form:
                return errors.FORM_NOT_FOUND
            
            response = db.session.query(Response).filter(
                Response.application_form_id == form.id, Response.user_id == g.current_user['id']).first()
            if not response:
                return errors.RESPONSE_NOT_FOUND
            
            answers = db.session.query(Answer).filter(Answer.response_id == response.id).all()
            response.answers = list(answers)

            return response
        except:
            return errors.DB_NOT_AVAILABLE

    @auth_required
    def post(self):
        # Save a new response for the logged-in user.
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('is_submitted', type=bool, required=True)
        req_parser.add_argument('application_form_id', type=int, required=True)
        req_parser.add_argument('answers', type=list, required=True, location='json')
        args = req_parser.parse_args()

        user_id = g.current_user['id']
        try: 
            response = Response(args['application_form_id'], user_id)
            response.is_submitted = args['is_submitted']
            if args['is_submitted']:
                response.submitted_timestamp = datetime.datetime.now()
            db.session.add(response)
            db.session.commit()

            for answer_args in args['answers']:
                answer = Answer(response.id, answer_args['question_id'], answer_args['value'])
                db.session.add(answer)
            db.session.commit()

            return {'id': response.id, 'user_id': user_id}, 201  # 201 is 'CREATED' status code
        except:
            return errors.DB_NOT_AVAILABLE

    @auth_required
    def put(self):
        # Update an existing response for the logged-in user.
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('id', type=int, required=True)
        req_parser.add_argument('is_submitted', type=bool, required=True)
        req_parser.add_argument('application_form_id', type=int, required=True)
        req_parser.add_argument('answers', type=list, required=True, location='json')
        args = req_parser.parse_args()

        user_id = g.current_user['id']
        try: 
            old_response = db.session.query(Response).filter(Response.id == args['id']).first()
            if not old_response:
                return errors.RESPONSE_NOT_FOUND
            if old_response.user_id != user_id:
                return errors.UNAUTHORIZED
            if old_response.application_form_id != args['application_form_id']:
                return errors.UPDATE_CONFLICT

            old_response.is_submitted = args['is_submitted']
            if args['is_submitted']:
                old_response.submitted_timestamp = datetime.datetime.now()

            for answer_args in args['answers']:
                old_answer = db.session.query(Answer).filter(Answer.response_id == old_response.id, Answer.question_id == answer_args['question_id']).first()
                if old_answer:  # Update the existing answer
                    old_answer.value = answer_args['value']
                else:
                    answer = Answer(old_response.id, answer_args['question_id'], answer_args['value'])
                    db.session.add(answer)
            db.session.commit()
            db.session.flush()

            return {}, 204
        except Exception as e:
            return errors.DB_NOT_AVAILABLE

    @auth_required
    def delete(self):
        # Delete an existing response for the logged-in user.
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('id', type=int, required=True)
        args = req_parser.parse_args()

        try:
            response = db.session.query(Response).filter(Response.id == args['id']).first()
            if not response:
                return errors.RESPONSE_NOT_FOUND

            if response.user_id != g.current_user['id']:
                return errors.UNAUTHORIZED
            
            response.is_withdrawn = True
            response.withdrawn_timestamp = datetime.datetime.now()
            response.is_submitted = False
            response.submitted_timestamp = None

            db.session.commit()
            db.session.flush()
        except:
            return errors.DB_NOT_AVAILABLE

        return {}, 204