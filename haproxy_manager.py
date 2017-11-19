#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Flask Module to display haproxy stats
and perform enable/disable operations
"""

import os
import smtplib
import subprocess
import ConfigParser
import logging
from logging.handlers import RotatingFileHandler
from email.mime.text import MIMEText
from flask import Flask, g, session, redirect, url_for, render_template, request
from flask_simpleldap import LDAP
from haproxyadmin import haproxy

pwd = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = "\xd7\x1e\xd0\xc6O\xdf\x8b\xfb9\xe12\xfb(\x8d\xcb\xfbC\xb8\xe8t\r\x0c\x94\t"

config = ConfigParser.ConfigParser()
config.read(pwd + '/config.ini')

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = RotatingFileHandler(pwd + '/logs/ha_manager.log',
                              maxBytes=1000000, backupCount=15)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)

wz_logger = logging.getLogger('werkzeug')
wz_handler = RotatingFileHandler(pwd + '/logs/access.log',
                                 maxBytes=1000000, backupCount=15)
wz_logger.addHandler(wz_handler)

app.logger.addHandler(wz_handler)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

app.config['LDAP_HOST'] = config.get('ldap', 'host')
app.config['LDAP_BASE_DN'] = config.get('ldap', 'base_dn')
app.config['LDAP_OPENLDAP'] = True
app.config['LDAP_USER_OBJECT_FILTER'] = config.get('ldap',
                                                   'ldap_user_object_filter')

# Group configuration
app.config['LDAP_GROUP_MEMBERS_FIELD'] = config.get('ldap',
                                                    'ldap_group_members_field')
app.config['LDAP_GROUP_OBJECT_FILTER'] = config.get('ldap',
                                                    'ldap_group_object_filter')


def fetch_haproxy_data():
    """
    Function to fetch server state and
    current connections from haproxy
    """
    data = {}
    hap = haproxy.HAProxy(socket_dir=config.get('haproxy', 'socket_dir'))
    backends = hap.backends()
    for backend in backends:
        data[backend.name] = {}
        data[backend.name]['bind-process'] = backend.process_nb
        data[backend.name]['servers'] = {}
        data[backend.name]['requests'] = {}
        servers = backend.servers()
        for server in servers:
            try:
                data[backend.name]['servers'][server.name] = server.status
            except:
                data[backend.name]['servers'][server.name] = "INCONSISTENT"
            data[backend.name]['requests'][server.name] = server.metric('scur')
    return data


@app.before_request
def before_request():
    """
    Function called before starting a new session
    """
    g.user = None
    if 'username' in session:
        g.user = {}


@app.route('/state-change/', methods=['POST'])
def change_state():
    """
    Function called when servers are enabled/disabled
    """
    backend = request.form['backend']
    svr = request.form['server']
    action = request.form['action']

    app.logger.info('User %s %s %s', session['username'], action, svr)

    ansible_cmd = "ansible-playbook " + pwd + \
        "/haproxy.yml -e haproxy_backend=" + backend + \
        " -e haproxy_host=" + svr + " -e action=" + action
    proc = ansible_cmd.split(' ')
    subout = subprocess.Popen(proc, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)

    output = subout.communicate()[0]
    exitcode = subout.returncode

    if exitcode != 0:
        app.logger.warning('Ansible playbook failed to %s %s', action, backend)

    return ('', 204)


@app.route('/')
def index():
    """
    Index page of the tool
    """
    if g.user is None:
        return redirect(url_for('login'))

    doc = fetch_haproxy_data()
    return render_template('view.html', doc=doc)


@app.route('/getData')
def get_data():
    """
    Function to get haproxy data and render on UI
    """
    doc = fetch_haproxy_data()
    return render_template('table.html', doc=doc)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Function called when user logs in
    """
    if g.user:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        ldap_username = 'uid='+username+',ou=' + config.get('ldap', 'ou') + \
            ',' + config.get('ldap', 'base_dn')
        app.config['LDAP_USERNAME'] = ldap_username
        app.config['LDAP_PASSWORD'] = password
        ldap = LDAP(app)
        try:
            grp_members = ldap.get_group_members(group=config.get('ldap',
                                                 'group'))
            if ldap_username in grp_members:
                ldap.bind_user(username, password)
        except Exception:
            app.logger.warning('Login attempt failed for %s', username)
            return render_template('login.html')
        else:
            session['username'] = request.form['username']
            app.logger.info('User %s logged in', username)
            return redirect('/')

    return render_template('login.html')


@app.route('/sendEmail', methods=['POST'])
def sendemail():
    """
    Function to send email after enabling/disabling servers
    """
    server = request.form['server']
    state = request.form['state']
    user = session['username']
    sender = config.get('email', 'sender')
    receiver = config.get('email', 'receiver')

    msg = MIMEText("User %s has %s %s from haproxy" % (user, state, server))
    msg['Subject'] = config.get('email', 'subject')
    msg['From'] = sender
    msg['To'] = receiver

    smtp = smtplib.SMTP(config.get('email', 'smtp_server'))
    smtp.sendmail(sender, [receiver], msg.as_string())
    smtp.quit()

    return ('', 204)


@app.route('/logout')
def logout():
    """
    Function called when user logs out
    """
    app.logger.info('User %s logged out', session['username'])
    session.pop('username', None)
    return redirect(url_for('login'))
