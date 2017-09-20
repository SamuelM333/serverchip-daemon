# from bson.json_util import dumps
from bson.objectid import ObjectId
from pymongo import MongoClient
from socketIO_client import SocketIO, ConnectionError
from pprint import pprint

from CronTabManager import CronTabManager


class SocketIOClient(object):
    def __init__(self, host='127.0.0.1', port=5000):
        # TODO Handle server not available
        # try:
        self.client = SocketIO(host, port)
        self.cronTabManager = CronTabManager()
        self.db = MongoClient()['serverchip']

        # except ConnectionError:
        #     print('The server is down. Try again later.')
        #     self.client = None

    @staticmethod
    def handle_response(data):
        print(data)

    def stop_task(self, task_id):
        # TODO Write this
        pass

    def send_run_task_request(self, task_id):
        # TODO Emit something here
        pass

    def check_conditions_of_task(self, task_id):
        # TODO Is it really needed to hit the DB here?
        task = self.db.task.find_one({'_id': ObjectId(task_id)})
        pprint(task)
        if task is not None:
            # Get port status
            status = self.send_get_port_status_request(str(task['microchip']))
            match = False
            for condition in task['conditions']:
                port = condition['input_port']['number']
                if status[port] == condition['input_port']['state']:
                    match = True

            if match:
                self.send_run_task_request(task_id)

    def send_new_input_port_condition(self, microchip_ip, task_id, condition):
        self.client.emit(
            'new_input_port_condition', {
                'microchip_ip': microchip_ip,
                'task_id': task_id,
                'condition': condition
            }
        )

    def send_get_port_status_request(self, microchip_id):
        ports_status = dict()

        def _get_status(data):
            global ports_status
            ports_status = data

        def _done():
            # TODO Needed?
            print '_done'

        self.client.once('get_port_status_response_client', _get_status, _done)
        self.client.emit('get_port_status_request', {'microchip_id': microchip_id})

        return ports_status

    def handle_new_task(self, task):
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
        # Start listening for the WS server
        self.client.on('new_task', self.handle_new_task)

        # Emit daemon connected to the WS server
        # TODO Wait for ack
        self.client.emit('daemon_connected', 'daemon_connected')

        while True:
            self.client.wait()
