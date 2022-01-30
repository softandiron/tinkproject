import logging
import os.path

from datetime import datetime
from pytz import timezone

logger = logging.getLogger("Config")

try:
    import yaml
    yaml_installed = True
except ImportError:
    yaml_installed = False
    logger.critical("YAML не установлен. Функциональность ограничена")
    logger.critical("Для получения полной функциональности выполните pip3 install pyyaml")


class Config:
    __instance = None

    __config = {}

    def __new__(self, *args):
        # Singleton - позволяет иметь только один экземпляр класса
        if self.__instance is None:
            self.__instance = object.__new__(self, *args)
        return self.__instance

    def __init__(self, config_file_name="config.yaml"):
        self.config_file_name = config_file_name

        if os.path.isfile(config_file_name) and yaml_installed:
            #  config file found and yaml-parser installed
            with open(self.config_file_name) as config_file:
                self.__config = yaml.safe_load(config_file)
        if self.__config == {}:
            #  Если файла нет - пробуем заполнить его из старой версии конфигурации
            logger.info('getting account data..')
            if not os.path.isfile("my_account.txt"):
                logger.critical("Default (my_account.txt) config file not found!")
                exit()
            with open(file='my_account.txt') as token_file:
                my_token = token_file.readline().rstrip('\n')
                my_timezone = token_file.readline().rstrip('\n')
                start_year = token_file.readline().rstrip('\n')
                start_month = token_file.readline().rstrip('\n')
                start_day = token_file.readline().rstrip('\n')

            self.__config.update({
                'token': my_token,
                'timezone': my_timezone,
                'start_year': int(start_year),
                'start_month': int(start_month),
                'start_day': int(start_day),
            })
            self._write_config_to_file()

    def _write_config_to_file(self):
        if not yaml_installed:
            # Если yaml не установлен - ничего не делаем
            return
        with open(self.config_file_name, 'w') as config_file:
            yaml.dump(self.__config,
                      config_file,
                      encoding="utf-8",
                      allow_unicode=True,
                      sort_keys=True)

    def check_accounts_config(self, accounts):
        # проверяет наличие конфигурации для аккаунтов, если надо - дописывает ее в файл
        for account in accounts:
            id = account.id
            name = account.name
            opened_date = account.opened_date.strftime("%Y-%m-%d")
            closed_date = account.closed_date
            if not closed_date.year > 1970:
                closed_date = None
            else:
                closed_date = closed_date.strftime("%Y-%m-%d")

            if id not in self.__config:
                logger.info(f"New account found - {id} - {name} - adding config")
                self.__config[id] = {
                    'id': id,
                }
                self._write_config_to_file()
            defaults = {
                'parse': True,
                'show empty operations': False,
                'type': account.type,
                'name': f'account-{name}',
                'filename': f'tinkoffReport_%Y.%m.%d_{id}_{name}',
                'opened date': opened_date,
                'closed date': closed_date,
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
        return self.__config['token']

    @property
    def now_date(self):
        """Возвращает текущую дату.
           Оставлено для обратной совместимости.

        Returns:
            [datetime]: текущие время и дата
        """
        return datetime.now()

    @staticmethod
    def parse_boolean(in_value):
        # Проверяет на входе данные (строка/число/булево)
        # возвращает соответствующее значение:
        # yes, true, 1, on, positive int -> True
        # no, false, 0, off, 0 or negative int -> False
        if isinstance(in_value, bool):
            return in_value
        elif isinstance(in_value, (int, float)):
            if in_value <= 0:
                # 0 и отрицательные числа - False
                return False
            # Все, что больше ноля - True
            return True
        elif isinstance(in_value, str):
            value = in_value.lower()
            if value in ["true", "yes", "on", "1"]:
                return True
            elif value in ["false", "no", "off", "0"]:
                return False
        logger.critical("Value cannot be parsed to boolean! Set to True")
        logger.critical(in_value)
        return True

    def get_account_parse_status(self, account_id):
        """Возвращает надо ли обрабатывать запрашиваемый счет

        Args:
            account_id (int): номер брокерского счета для API

        Returns:
            [boolean]: True - если обрабатывать.
        """
        logger.debug(f"Get parse status for account {account_id}")
        if account_id not in self.__config.keys():
            logger.error(f"Нет настроек для аккаунта {account_id}.")
            logger.error("Используем значение по умолчанию.")
            return True
        if 'parse' not in self.__config[account_id].keys():
            logger.error(f"Нет настроек необходимости обработки для аккаунта {account_id}.")
            logger.error("Используем значение по умолчанию.")
            return True
        status = self.__config[str(account_id)]['parse']
        status = self.parse_boolean(status)
        logger.debug(str(status) + " " + str(type(status)))
        return status

    def get_account_name(self, account_id):
        """Возвращает пользовательское название запрашиваемого счета

        Args:
            account_id (int): номер брокерского счета для API

        Returns:
            [str]: пользовательское имя счета
        """
        logger.debug(f"Get name for account {account_id}")
        if account_id not in self.__config.keys():
            logger.error(f"Нет настроек для аккаунта {account_id}.")
            logger.error("Используем значение по умолчанию.")
            return f"account-{account_id}"
        if 'name' not in self.__config[account_id].keys():
            logger.error(f"Нет настроек имени для аккаунта {account_id}.")
            logger.error("Используем значение по умолчанию.")
            return f"account-{account_id}"
        name = self.__config[str(account_id)]['name']
        logger.debug(name)
        return str(name)

    def get_account_filename(self, account_id):
        """Возвращает имя файла запрашиваемого счета
        Прогоняет шаблон через datetime.strftime
        При ошибке в шаблоне - выдает дефолтный шаблон

        Args:
            account_id (int): номер брокерского счета для API

        Returns:
            [str]: имя файла для счета
        """
        logger.debug(f"Get filename for account {account_id}")
        acc_name = self.get_account_name(account_id)
        def_name = datetime.now().strftime(f"tinkoffReport_%Y.%m.%d_{account_id}")
        logger.debug(def_name)
        if account_id not in self.__config.keys():
            logger.error(f"Нет настроек для аккаунта {acc_name} - {account_id}.")
            logger.error("Используем значение по умолчанию.")
            return def_name
        if 'name' not in self.__config[account_id].keys():
            logger.error(f"Нет настроек имени файла для аккаунта {acc_name} - {account_id}.")
            logger.error("Используем значение по умолчанию.")
            return def_name
        name_template = self.__config[str(account_id)]['filename']
        try:
            filename = datetime.now().strftime(name_template)
        except Exception as e:
            logger.error("Ошибка обработка шаблона имени файла {acc_name} - {account_id}.")
            logger.error(e)
            filename = def_name
        logger.debug(name_template)
        logger.debug(filename)
        if filename == "":
            return def_name
        return filename

    def get_account_show_empty_operations(self, account_id):
        """Возвращает надо ли показывать невыполненнные операции

        Args:
            account_id (int): номер брокерского счета для API

        Returns:
            [boolean]: True - если показывать.
        """
        logger.debug(f"Get empty operations status for account {account_id}")
        if account_id not in self.__config.keys():
            logger.error(f"Нет настроек для аккаунта {account_id}.")
            logger.error("Используем значение по умолчанию.")
            return False
        if 'show empty operations' not in self.__config[account_id].keys():
            logger.error(f"Нет настроек видимости пустых операций для аккаунта {account_id}.")
            logger.error("Используем значение по умолчанию.")
            return False
        status = self.__config[str(account_id)]['show empty operations']
        status = self.parse_boolean(status)
        logger.debug(str(status) + " " + str(type(status)))
        return status

    def get_account_opened_date(self, account_id):
        """Возвращает надо ли показывать невыполненнные операции

        Args:
            account_id (int): номер брокерского счета для API

        Returns:
            [boolean]: True - если показывать.
        """
        logger.debug(f"Get opened_date for account {account_id}")
        if account_id not in self.__config.keys():
            logger.error(f"Нет настроек для аккаунта {account_id}.")
            logger.error("Используем значение по умолчанию.")
            return datetime(2010, 1, 1)
        if 'opened date' not in self.__config[account_id].keys():
            logger.error(f"Нет настроек видимости пустых операций для аккаунта {account_id}.")
            logger.error("Используем значение по умолчанию.")
            return datetime(2010, 1, 1)

        opened_date_str = self.__config[str(account_id)]['opened date']
        try:
            opened_date = datetime.strptime(opened_date_str, "%Y-%m-%d")
        except Exception as e:
            name = self.get_account_name(account_id)
            logger.error(e)
            logger.warning(f"Неверный формат даты в настойках счета {name}.")
            logger.warning(f"Требуется %Y-%m-%d (ГГГГ-ММ-ДД), есть: {opened_date_str}.")
            logger.warning("Используем значение по умолчанию")
            opened_date = datetime(2010, 1, 1)
        logger.debug(f"Got opened date: {opened_date}")
        return opened_date

    def get_debug_figis(self):
        if "debug_figis" in self.__config:
            return self.__config["debug_figis"]
        return []
