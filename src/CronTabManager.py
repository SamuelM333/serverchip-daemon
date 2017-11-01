from crontab import CronTab


DOWS = {
    'Monday': 'MON',
    'Tuesday': 'TUE',
    'Wednesday': 'WED',
    'Thursday': 'THU',
    'Friday': 'FRI',
    'Saturday': 'SAT',
    'Sunday': 'SUN'
}


class CronTabManager:
    def __init__(self):
        self.cron = CronTab(user='ubuntu')

    @staticmethod
    def parse_crontab_dict(crontab_dict):
        start = '{} {} * * {}'.format(
            crontab_dict['start'][3:],
            crontab_dict['start'][:2],
            DOWS[crontab_dict['day']]
        )

        end = '{} {} * * {}'.format(
            crontab_dict['end'][3:],
            crontab_dict['end'][:2],
            DOWS[crontab_dict['day']]
        )

        return start, end

    def add_task_condition(self, task_id, condition_dict):
        """
        task_id
        condition_dict:
            start
            end
            day
        """
        print condition_dict
        # TODO Check path of the script. cd $SERVERCHIP_DIR ; then run script?

        task_runner_crontab_string, task_stopper_crontab_string = CronTabManager.parse_crontab_dict(condition_dict)

        task_runner = self.cron.new(
            command='python ./task_management.py run ' + task_id,
            comment='start ' + task_id
        )

        task_runner.setall(task_runner_crontab_string)

        task_stopper = self.cron.new(
            command='python ./task_management.py stop ' + task_id,
            comment='stop ' + task_id
        )

        task_stopper.setall(task_stopper_crontab_string)

        if task_runner.is_valid() and task_stopper.is_valid():
            self.cron.write()
        else:
            print "Not valid"

        return task_runner.is_valid() and task_stopper.is_valid()
