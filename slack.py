import requests


class SlackWrapper:
    def __init__(self, url, channel, color, username, emoji, logger):
        self.url = url
        self.channel = channel
        self.color = color
        self.username = username
        self.emoji = emoji
        self.logger = logger

    def send_text(self, title, main_text, blocks=None, color=None, emoji=None, channel=None):
        payload = {
            'channel': channel or self.channel,
            'username': self.username,
            'color': color or self.color,
            'unfurl_links': True,
            'pretext': title,
            'icon_emoji': emoji or self.emoji,
            'text': main_text
        }
        if blocks:
            payload.pop('text')
            payload['blocks'] = blocks
        doit = requests.post(self.url, json=payload)
        self.logger.debug(doit)
        self.logger.debug(doit.text)
        assert doit.ok
