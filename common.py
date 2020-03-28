import logging
import logging.handlers
import os
import os.path
import sys

import colorlog

from bot_framework.slack import SlackWrapper


def setup_logging(extra_name=None, disable_tty=False):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    if extra_name:
        extra_name = '-' + extra_name
    else:
        extra_name = ''

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    if not os.path.exists('logs'):
        os.mkdir('logs')

    filename = os.path.basename(sys.argv[0])
    basename = os.path.splitext(filename)[0]

    if sys.stdout.isatty() and not disable_tty:
        ch = colorlog.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(colorlog.ColoredFormatter('%(log_color)s%(levelname)s\t%(name)s\t%(message)s'))
        logger.addHandler(ch)

    fh = logging.handlers.TimedRotatingFileHandler(f'logs/{basename}{extra_name}.log', when='W0')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    fh2 = logging.handlers.TimedRotatingFileHandler(f'logs/{basename}{extra_name}.debug.log', when='W0')
    fh2.setLevel(logging.DEBUG)
    fh2.setFormatter(formatter)
    logger.addHandler(fh2)

    return logger


def change_to_local_dir():
    abspath = os.path.abspath(sys.argv[0])
    dname = os.path.dirname(abspath)
    os.chdir(dname)


def send_to_slack(url, channel, title, main_text, color, username, emoji, logger):
    _slack = SlackWrapper(url, channel, color, username, emoji, logger)
    _slack.send_text(title, main_text)


def normalize_text(input_text):
    import pathlib
    import unicodedata
    import re
    from ftplib import FTP

    if not pathlib.Path('confusables.txt').exists():
        ftp = FTP('ftp.unicode.org')
        ftp.login()
        ftp.cwd('Public/security/latest')
        with open('confusables.txt', 'wb') as fp:
            ftp.retrbinary('RETR confusables.txt', fp.write)
        ftp.quit()

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

    result = unicodedata.normalize('NFKD', input_text)
    result = re.sub(r'[\u0300-\u0380]', '', result)
    result = result.translate(tr)
    return result
