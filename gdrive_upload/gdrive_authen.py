#!/usr/bin/python
from __future__ import absolute_import
import os
import sys
import httplib2
import logging

from apiclient import discovery
from oauth2client import client as oauth_client, tools as oauth_tools, file as oauth_file
from oauth2client.service_account import ServiceAccountCredentials

logger = logging.getLogger(__name__)
# Set scope to allow all action
SCOPES = 'https://www.googleapis.com/auth/drive'
# Google client secret : https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRET_FILE = 'client_secret.json'
SERVICE_SECRET_FILE = 'service_secret.json'
APPLICATION_NAME = 'GDrive Uploader'


def get_credentials(flags=None, service_account=False, delegated_user=None):
    """
    Read token file from ./.credentials/drive-access.json or create one if not exist.
    Creation process will ask user to copy url that display on screen to get allow token.
    :param flags : oauth2client flags. read more [https://goo.gl/dL03yF]
    :param service_account : set to enable service account. Default is client account that need to authen on web browser
    :param delegated_user : if service account is True, you have choice to act as specific user. e.g. admin@example.com
    :return:
        Oauth2 credential ready for use in client
    """

    if service_account:
        logger.debug('User service account')
        credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_SECRET_FILE, scopes=SCOPES)
        if delegated_user:
            logger.debug('Delegate service account to [%s]', delegated_user)
            credentials = credentials.create_delegated(delegated_user)
    else:
        logger.debug('Use client account')
        home_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'drive-access.json')
        logger.debug('Get credentials : %s', credential_path)

        store = oauth_file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            logger.info('Not found credentials. Try to get new key.')
            logger.debug('Storing credentials to %s', credential_path)
            flow = oauth_client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.params['access_type'] = 'offline'  # offline access
            flow.user_agent = APPLICATION_NAME
            if not flags:
                # if function call with non-implement flags, force to use default flags for oauth2client api
                import argparse
                parser = argparse.ArgumentParser(parents=[oauth_tools.argparser])
                flags = parser.parse_args()
            credentials = oauth_tools.run_flow(flow, store, flags)
        logger.debug('Storing credentials to %s', credential_path)

    logger.debug('Init credential success : %s', credentials)
    return credentials


def create_gdrive_service(flags=None, service_account=False, delegated_user=None):
    """
    Create Google API Service for Google Drive
    :param flags : oauth2client flags. read more [https://goo.gl/dL03yF]
    :param service_account : set to enable service account. Default is client account that need to authen on web browser
    :param delegated_user : if service account is True, you have choice to act as specific user. e.g. admin@example.com
    :return:
        A service for api call
    """
    credentials = get_credentials(flags=flags, service_account=service_account, delegated_user=delegated_user)
    try:
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('drive', 'v3', http=http, cache_discovery=False)
    except Exception as e:
        logger.error('cannot initial gdrive service : %s', e)
        return
    return service
