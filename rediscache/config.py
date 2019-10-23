import os
import time
import sys
from enum import Enum

# suppress boto logs
import logging
logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('s3transfer').setLevel(logging.CRITICAL)


def setup_custom_logger(name):
    formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler(os.environ['LOGFILE_PATH'], mode='w')
    handler.setFormatter(formatter)
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(screen_handler)
    return logger


logger = setup_custom_logger(__name__)

mongo_dsn = os.environ['MONGO_DSN']
mongo_database = os.environ['MONGO_DATABASE']
redis_dsn = os.environ['REDIS_DSN']
default_expire_after = os.environ.get('EXPIRE_AFTER_SEC', 0)


class SourceType(Enum):
    MONGODB = 'mongodb'
    S3 = 's3'


class DocType(Enum):
    ACCOUNTS = 'accounts'
    CALENDARS = 'calendars'
    CATEGORIES = 'categories'
    CONTACTS = 'contacts'
    DRAFTS = 'drafts'
    EVENTS = 'events'
    FAVORITES = 'favorites'
    FILES = 'files'
    FOLDERS = 'folders'
    LABELS = 'labels'
    MESSAGES = 'messages'
    PROFILES = 'profiles'
    ROLODEXS = 'rolodexs'
    SPOOLS = 'spools'
    SUGGESTIONS = 'suggestions'
    TEMPLATES = 'templates'
    THREADS = 'threads'
    TOKENS = 'tokens'
    TRACKERS = 'trackers'
    USERS = 'users'
    WAITLISTS = 'waitlists'
    WHITELISTS = 'whitelists'
