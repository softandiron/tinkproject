import configparser
import logging
import os.path


from datetime import datetime
from pytz import timezone

logger = logging.getLogger("Config")


class Config:
    __instance = None

    __config = configparser.ConfigParser()

    def __new__(self, *args):
        # Singleton - позволяет иметь только один экземпляр класса
        if self.__instance is None:
            self.__instance = object.__new__(self, *args)
        return self.__instance

    def __init__(self, config_file_name="config.ini"):
        self.config_file_name = config_file_name

        if os.path.isfile(config_file_name):
            #  config file found
            self.__config.read(config_file_name)
        else:
            #  Если файла нет - пробуем заполнить его из старой версии конфигурации
            logger.info('getting account data..')
            with open(file='my_account.txt') as token_file:
                my_token = token_file.readline().rstrip('\n')
                my_timezone = timezone(token_file.readline().rstrip('\n'))
                start_year = token_file.readline().rstrip('\n')
                start_month = token_file.readline().rstrip('\n')
                start_day = token_file.readline().rstrip('\n')

            self.__config['DEFAULT'] = {
                'token': my_token,
                'timezone': my_timezone,
                'start_year': int(start_year),
                'start_month': int(start_month),
                'start_day': int(start_day),
                'start_date': datetime(int(start_year), int(start_month), int(start_day), 0, 0, 0,
                                       tzinfo=my_timezone)
            }
            self._write_config_to_file()

    def _write_config_to_file(self):
        with open(self.config_file_name, 'w') as config_file:
            self.__config.write(config_file)

    def check_accounts_config(self, accounts):
        # проверяет наличие конфигурации для аккаунтов, если надо - дописывает ее в файл
        for account in accounts:
            id = account.broker_account_id
            acc_type = account.broker_account_type
            if id not in self.__config:
                logger.info(f"New account found - {id} - adding config")
                self.__config[id] = {
                    'id': id,
                    'type': str(acc_type),
                }
                self._write_config_to_file()
            defaults = {
                'parse': True,
                'name': f'account-{id}',
                'filename': f'tinkoffReport_%%Y.%%b.%%d_{id}',
            }
            # Check default values and set them as necessary
            for key, value in defaults.items():
                if key not in self.__config[str(id)]:
                    self.__config[str(id)][key] = str(value)
                    self._write_config_to_file()
            pass
        pass

    @property
    def token(self):
        return self.__config['DEFAULT']['token']

    def parse_account(self, account_id):
        logger.debug(f"Get parse status for account {account_id}")
        status = self.__config[str(account_id)].getboolean('parse')
        logger.debug(status)
        return bool(status)
