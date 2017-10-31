import sys
import argparse

from bson.errors import InvalidId
from bson.objectid import ObjectId

from main import socketIO_client


def print_to_logs(action, task_id):
    # TODO Report here
    print action, task_id


def run_task(task_id):
    print_to_logs('run', task_id)
    socketIO_client.handle_run_task_if_conditions_match(task_id)


def stop_task(task_id):
    print_to_logs('stop', task_id)
    socketIO_client.send_stop_task_request(task_id)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', type=str, help="Action. Either 'run' or 'stop'")
    parser.add_argument('task', type=str, help="Task ID")

    args = parser.parse_args()

    if args.task is not None:
        try:
            _id = ObjectId(args.task)  # Variable not used, but this tests that args.task is a valid ObjectId string
        except InvalidId as e:
            sys.stdout.write("ERROR: {}\n".format(str(e)))
            exit(1)
    else:
        sys.stdout.write("ERROR: Task ID not provided\n")
        exit(1)

    if args.action is not None:
        if args.action in ['run', 'stop']:

            if args.action == 'run':
                print 'run task', args.task
                run_task(args.task)
            else:
                print 'stop task', args.task
                stop_task(args.task)
        else:
            sys.stdout.write("ERROR: Acceptable values for 'Action' are either 'run' or 'stop'\n")
            exit(1)

    else:
        sys.stdout.write("ERROR: Action not provided\n")
        exit(1)
