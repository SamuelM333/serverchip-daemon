# from bson.json_util import dumps
from datetime import datetime, time
from bson.objectid import ObjectId
from bson.json_util import loads
from json import loads
from mongoengine import connect
from pymongo import MongoClient
from socketIO_client import SocketIO, ConnectionError
from pprint import pprint

from CronTabManager import CronTabManager
from models import (
    Task,
    Microchip,
    Report,
    ReportDetails,
    ReportStatus
)

WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

condition_ports_status = dict()


class SocketIOClient(object):
    def __init__(self, host='127.0.0.1', port=5000):
        # TODO Handle server not available
        # try:
        connect('serverchip', host=host)
        self.client = SocketIO(host, port)
        self.cronTabManager = CronTabManager()
        # self.db = MongoClient()['serverchip']
        # except ConnectionError:
        #     print('The server is down. Try again later.')
        #     self.client = None

    # TODO Remove
    @staticmethod
    def handle_response(data):
        print(data)

    def send_stop_task_request(self, task_id):
        # TODO Log here
        print 'send_stop_task_request', task_id
        self.client.emit('stop_task_request_server', task_id)

    def send_run_task_request(self, task, microchip):
        payload = {
            'output_port': {
                'number': task['output_port']['number'],
                'state': task['output_port']['state'],
            },
            'ip': microchip['ip']
        }
        print 'send_run_task_request', task['name']
        self.client.emit('run_task_request_server', payload)

    def send_new_input_port_condition(self, microchip_ip, task_id, condition):
        # TODO Report here
        self.client.emit(
            'new_input_port_condition', {
                'microchip_ip': microchip_ip,
                'task_id': task_id,
                'condition': condition
            }
        )

    @staticmethod
    def _set_condition_ports_status(data):
        global condition_ports_status
        condition_ports_status = data

    def send_get_ports_status_request(self, microchip_id):
        # TODO Check the naming on this events
        print 'microchip_id', microchip_id
        self.client.emit('get_port_status_request', {'microchip_id': microchip_id})
        self.client.wait(seconds=0.1)  # TODO How to not do this?

    def handle_run_task_if_conditions_match(self, payload):
        print "payload", payload
        task = loads(payload)
        if task is not None:
            task = Task.objects.get(_id=ObjectId(task['_id']['$oid']))
            microchip = Microchip.objects.get(_id=task.microchip)
            datetime_match = False
            port_match = False
            self.send_get_ports_status_request(str(microchip['_id']))
            print 'condition_ports_status', condition_ports_status

            for condition in task['conditions']:
                # Check datetime conditions, if any
                if condition.day_hour:
                    if WEEKDAYS[datetime.date.today().weekday()] in condition.day_hour.days:
                        start = time(condition['datetime']['hour']['start'][:2],
                                     condition['datetime']['hour']['start'][3:])

                        end = time(condition['datetime']['hour']['end'][:2],
                                   condition['datetime']['hour']['end'][3:])

                        # datetime_match = start <= datetime.now() <= end # TODO Use this

                        if start <= datetime.now() <= end:
                            datetime_match = True
                        else:
                            print 'hour/minutes mismatch'  # TODO Remove? Or log here?
                            report = Report(
                                microchip=ObjectId(microchip["_id"]),
                                details=ReportDetails(
                                    task=ObjectId(task["_id"]),
                                    status=ReportStatus(
                                        code="Not Executed",
                                        reason="Conditions were not given",  # TODO Check this
                                    )
                                )
                            )
                            print 'report', report
                            report.save()  # TODO Call .validate here?
                    else:
                        print 'weekday mismatch'  # TODO Remove? Or log here?
                        report = Report(
                            microchip=ObjectId(microchip["_id"]),
                            details=ReportDetails(
                                task=ObjectId(task["_id"]),
                                status=ReportStatus(
                                    code="Not Executed",
                                    reason="Conditions were not given",  # TODO Check this
                                )
                            )
                        )
                        print 'report', report
                        report.save()  # TODO Call .validate here?
                else:
                    # If there's no datetime condition, set to True
                    print 'datetime_match fallback'
                    datetime_match = True

                if datetime_match:
                    if condition.input_port:
                        port_number = condition.input_port.number
                        if condition_ports_status[str(port_number)] == condition.input_port.state:
                            print 'YAYY'
                            # TODO Do or & and logic here
                            port_match = True
                            # break  # TODO Remove when or & and logic is implemented
                        else:
                            report = Report(
                                microchip=ObjectId(microchip["_id"]),
                                details=ReportDetails(
                                    task=ObjectId(task["_id"]),
                                    status=ReportStatus(
                                        code="Not Executed",
                                        reason="Conditions were not given",  # TODO Check this
                                    )
                                )
                            )
                            print 'report', report
                            report.save()  # TODO Call .validate here?
                            print 'not yay :('
                    else:
                        # If there's no port condition, set to True
                        print 'port_match fallback'
                        port_match = True

            if datetime_match and port_match:
                report = Report(
                    microchip=ObjectId(microchip["_id"]),
                    details=ReportDetails(
                        task=ObjectId(task["_id"]),
                        status=ReportStatus(
                            code="Executed",
                            reason="Conditions were given",  # TODO Check this
                        )
                    )
                )
                print 'report', report
                report.save()  # TODO Call .validate here?
                self.send_run_task_request(task, microchip)
        else:
            print "task not found"

    def handle_new_task(self, task):
        # TODO Report here

        print 'handle_new_task'
        print task
        for condition in task['conditions']:
            if condition.get('datetime', False):
                datetime_condition = {
                    'start': condition['datetime']['start'],
                    'end': condition['datetime']['end'],
                    'day': condition['datetime']['day']
                }

                self.cronTabManager.add_task_condition(str(task['_id']), datetime_condition)

            if condition.get('input_port', False):
                self.send_new_input_port_condition(
                    task['microchip']['ip'],
                    str(task['_id']),
                    condition
                )

    def start_main_loop(self):
        # Start listening for WS events
        self.client.on('new_task', self.handle_new_task)
        self.client.on('run_task_if_conditions_match', self.handle_run_task_if_conditions_match)
        self.client.on('get_port_status_response_daemon', SocketIOClient._set_condition_ports_status)

        # Emit daemon connected to the WS server
        # TODO Wait for ack
        self.client.emit('daemon_connected', 'daemon connected')

        self.client.wait()
