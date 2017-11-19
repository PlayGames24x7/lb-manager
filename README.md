# LB-Manager

HAProxy is free, open source software that provides a high availability load balancer and proxy server for TCP and HTTP-based applications that spreads requests across multiple servers. The applications running behind HAProxy are typically updated in a round-robin fashion to ensure there is no downtime. A standard procedure of update involves disabling the node running that application from HAProxy, update the application and then enable it back. To enable and disable application nodes, HAProxy stats UI can be used but it's major drawback is it only works if HAProxy is running as a single process. HAProxy Manager was designed to counter that drawback and ease the process of deployment.

## Installation

### Environment
```
Centos 7, Python 2.7, x86-64 Architecture
```

### Install Yum Dependencies
```
yum install -y gcc python-devel openssl-devel openldap-devel epel-release python-pip libffi-devel httpd
```

### Install Pip Dependencies
```
pip install -r requirements.txt
```

## Configuration

Before running the tool you need to enter your environment config parameters in config.ini file. They are described below:

1. haproxy: This section only requires the path of haproxy socket dir. Please name the sockets in this dir as stats1, stats2 and so on.
2. ldap: Configure ldap related parameters in this section.
3. email: When applications are enabled or disabled from the tool, an email is sent. Please configure email related parameters in this section.

### Sample HAProxy global section

```
  global
    log 127.0.0.1 local0 debug
    maxconn 150000
    tune.ssl.default-dh-param 2048
    user haproxy
    group haproxy
    chroot      /var/lib/haproxy
    pidfile     /var/run/haproxy.pid
    maxcompcpuusage 1
    maxcomprate 1
    maxpipes    150000
    daemon

    nbproc 6
    cpu-map 1 0
    cpu-map 2 1
    cpu-map 3 2
    cpu-map 4 3
    cpu-map 5 4
    cpu-map 6 5

    stats socket /var/lib/haproxy/stats1 process 1 level admin
    stats socket /var/lib/haproxy/stats2 process 2 level admin
    stats socket /var/lib/haproxy/stats3 process 3 level admin
    stats socket /var/lib/haproxy/stats4 process 4 level admin
    stats socket /var/lib/haproxy/stats5 process 5 level admin
    stats socket /var/lib/haproxy/stats6 process 6 level admin
```

As Flask webserver is not suitable to run in production environment, we run this application with Apache mod_wsgi web server. WSGI daemon processes cannot be run as root. So you need to ensure the user, group specified in apache mod_wsgi configuration has access to haproxymanager dir and haproxy sockets dir.

### Sample Apache Configuration

```
WSGISocketPrefix <path_to_repository/logs>
<VirtualHost *:5000>
    ServerName <servername>

    WSGIDaemonProcess haproxymanager user=<user> group=<group> home=<path_to_repository>
    WSGIScriptAlias / <path_to_wsgi_file>

    <Directory <path_to_repository>>
        WSGIProcessGroup haproxymanager
        WSGIApplicationGroup %{GLOBAL}
        WSGIScriptReloading On
        Order deny,allow
        Allow from all
    </Directory>
</VirtualHost>
```

### Running the Application
```
service httpd start
```
