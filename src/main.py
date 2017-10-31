# import daemon
import logging

from SocketIOClient import SocketIOClient

logging.getLogger('socketIO-client').setLevel(logging.DEBUG)
logging.basicConfig()

socketIO_client = SocketIOClient()

if __name__ == '__main__':
    # socketIO_client.send_run_task_request("588aa7362589500ca4ad575b")
    # with daemon.DaemonContext():
    socketIO_client.start_main_loop()
