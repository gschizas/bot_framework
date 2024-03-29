import datetime
import os
import uuid
from urllib.parse import urlparse, parse_qs

import praw

DEFAULT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID')
DEFAULT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET')


def praw_wrapper(config=None,
                 user_agent=None,
                 client_id=None,
                 client_secret=None,
                 redirect_url=None,
                 scopes=None,
                 prompt=None,
                 requestor_class=None):

    if config:
        user_agent = config['main'].get('user_agent')
        client_id = config['main'].get('client_id')
        client_secret = config['main'].get('client_secret')
        redirect_url = config['main'].get('redirect_url')
        scopes = config['main'].get('scopes')

    iso_date = datetime.date.today().isoformat()
    user_agent = user_agent or f'python:gr.terrasoft.reddit.scratch:v{iso_date} (by /u/gschizas)'
    client_id = client_id or DEFAULT_CLIENT_ID
    client_secret = client_secret or DEFAULT_CLIENT_SECRET
    redirect_url = redirect_url or 'https://example.com/authorize_callback'
    scopes = scopes or ['*']

    user_agent_key = user_agent.split(':')[1]

    refresh_token_file = os.path.join('.refreshtoken', user_agent_key + '.refresh_token')

    if not config:
        if os.path.exists(refresh_token_file):
            with open(refresh_token_file, 'r') as f:
                refresh_token = f.read()
        else:
            refresh_token = None
    else:
        refresh_token = config['main'].get('refresh_token')

    if refresh_token:
        praw_instance = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            user_agent=user_agent,
            requestor_class=requestor_class)
    else:
        print("No refresh token found. Please visit the following URL to obtain one.")

        praw_instance = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_url,
            user_agent=user_agent,
            requestor_class=requestor_class)
        state = uuid.uuid4().hex
        print(prompt or "Visit the following URL:", praw_instance.auth.url(scopes, state))
        url = input("Result URL: ")
        query = parse_qs(urlparse(url).query)
        assert state == query['state'][0]
        code = query['code'][0]
        refresh_token = praw_instance.auth.authorize(code)
        if config:
            config['main']['refresh_token'] = refresh_token
        else:
            if not os.path.exists('.refreshtoken'):
                os.mkdir('.refreshtoken')
            with open(refresh_token_file, 'w') as f:
                f.write(refresh_token)
    return praw_instance
