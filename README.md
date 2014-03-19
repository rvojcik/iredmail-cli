iredmail-cli
============

iRedMail CLI (MySQL Only)
Command Line interface to iRedMail Open Source Email server solution


This is simple CLI interface to some functions of iRedMail. Many admins like CLI tools more like web management. 

It's good to have ability to do some basic thinks via command line. This tool in fact use configuration and many other functions from original Web interface. So original iredadmin is one of requirements

#Currently supported features
* Add domain
* Add domain as backup MX
* Add new mailbox
* Add/Update aliases
* Search in domains and mailbox
* Delete single account

#TODO
* Delete domain with all accounts

#Requirements
* python 2.7
* python-mysqldb
* python-pip
* python-prettytable
* iRedMail Web admin (iredadmin)

#Installation

Copy script to your sbin directory (for example /usr/local/sbin)

     sudo cp email-manage.py /usr/local/sbin/

Install python-mysqldb and python-pip to your system. 

In debian/ubuntu run

     sudo apt-get install python-mysqldb python-pip 

You will need new python-prettytable, so use pip radher then system packages

     sudo pip install prettytable


#Configuration

There is only one thing you need set up. Open email-manage.py and find rows:

    # iRedAdmin location
    iredadmin_install_path = '/usr/share/apache2/iredadmin'

This variables must point to directory where your iRedAdmin web interface is installed. This is default for Debian/Ubuntu.


#Contact

Robert Vojcik <robert@vojcik.net>
