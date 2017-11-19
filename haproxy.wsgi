import sys
import os

pwd = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, pwd)
from haproxy_manager import app as application

