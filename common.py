import logging
import logging.handlers
import os
import os.path
import sys

import colorlog

from bot_framework.slack import SlackWrapper


def setup_logging(extra_name: str = None, disable_tty: bool = False, when: str = None):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    for key, value in os.environ.items():
        if key.upper().startswith('LOGGING.'):
            logger_name = key[8:].lower()
            logger_value = logging.getLevelName(value)
            logging.getLogger(logger_name).setLevel(logger_value)

    extra_name = '-' + extra_name if extra_name else ''

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s:%(lineno)s %(message)s')

    if not os.path.exists('logs'):
        os.mkdir('logs')

    filename = os.path.basename(sys.argv[0])
    basename = os.path.splitext(filename)[0]

    if sys.stdout.isatty() and not disable_tty:
        ch = colorlog.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(colorlog.ColoredFormatter('%(log_color)s%(levelname)s\t%(name)s\t%(message)s'))
        logger.addHandler(ch)

    fh = logging.handlers.TimedRotatingFileHandler(f'logs/{basename}{extra_name}.log',
                                                   when=when or 'W0', encoding='utf-8')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    fh2 = logging.handlers.TimedRotatingFileHandler(f'logs/{basename}{extra_name}.debug.log',
                                                    when=when or 'W0', encoding='utf-8')
    fh2.setLevel(logging.DEBUG)
    fh2.setFormatter(formatter)
    logger.addHandler(fh2)

    return logger


def change_to_local_dir():
    abspath = os.path.abspath(sys.argv[0])
    dname = os.path.dirname(abspath)
    os.chdir(dname)


def send_to_slack(url: str, channel: str, title: str = None, main_text: str = None, color: str = None,
                  username: str = None, emoji: str = None, logger=None, blocks: list = None):
    _slack = SlackWrapper(url, channel, color, username, emoji, logger)
    _slack.send_text(title, main_text, blocks=blocks)


def _confusables():
    import pathlib

    if not pathlib.Path('confusables.txt').exists():
        _download_confusables()
    trans_table = {}
    with open('confusables.txt', encoding='utf8') as fp:
        c = 0
        for line in fp.readlines():
            line = line.strip()
            if ';' not in line:
                continue
            from_char, to_chars_raw, convertion_type = line.split('#')[0].split(';')
            assert convertion_type.strip() == 'MA', repr(convertion_type.strip())
            to_chars = to_chars_raw.strip().split()
            trans_table[int(from_char, 16)] = ''.join([chr(int(c, 16)) for c in to_chars])
    tr = str.maketrans(trans_table)
    return tr


def _download_confusables():
    from ftplib import FTP
    ftp = FTP('ftp.unicode.org')
    ftp.login()
    ftp.cwd('Public/security/latest')
    with open('confusables.txt', 'wb') as fp:
        ftp.retrbinary('RETR confusables.txt', fp.write)
    ftp.quit()


def normalize_text(input_text):
    import unicodedata
    import re
    if len(input_text) == 1: return input_text

    tr = _confusables()
    tr = dict(filter(lambda x: x[0] > 128, tr.items()))  # remove all ASCII from confusables. sheesh!

    result = unicodedata.normalize('NFKD', input_text)
    result = re.sub(r'[\u0300-\u0380]', '', result)
    result = result.translate(tr)
    return result
