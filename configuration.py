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
            }
            self._write_config_to_file()

    def _write_config_to_file(self):
        with open(self.config_file_name, 'w') as config_file:
            self.__config.write(config_file)

    def check_accounts_config(self, accounts):
        # проверяет наличие конфигурации для аккаунтов, если надо - дописывает ее в файл
        for account in accounts:
            id = account.broker_account_id
            if id not in self.__config:
                logger.info(f"New account found - {id} - adding config")
                self.__config[id] = {
                    'id': id,
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

    @property
    def start_date(self):
        start_date = datetime(int(self.__config['DEFAULT']['start_year']),
                              int(self.__config['DEFAULT']['start_month']),
                              int(self.__config['DEFAULT']['start_day']),
                              0, 0, 0, tzinfo=timezone(self.__config['DEFAULT']['timezone']))
        return start_date

    @property
    def now_date(self):
        """Возвращает текущую дату.
           Оставлено для обратной совместимости.

        Returns:
            [datetime]: текущие время и дата
        """
        return datetime.now()

    def get_account_parse_status(self, account_id):
        """Возвращает надо ли обрабатывать запрашиваемый счет

        Args:
            account_id (int): номер брокерского счета для API

        Returns:
            [boolean]: True - если обрабатывать.
        """
        logger.debug(f"Get parse status for account {account_id}")
        status = self.__config[str(account_id)].getboolean('parse')
        logger.debug(status)
        return bool(status)

    def get_account_name(self, account_id):
        """Возвращает пользовательское название запрашиваемого счета

        Args:
            account_id (int): номер брокерского счета для API

        Returns:
            [str]: пользовательское имя счета
        """
        logger.debug(f"Get name for account {account_id}")
        name = self.__config[str(account_id)]['name']
        logger.debug(name)
        return str(name)
