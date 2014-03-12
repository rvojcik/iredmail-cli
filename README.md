iredmail-cli
============

iRedMail CLI (MySQL Only)
Command Line interface to iRedMail Open Source Email server solution


This is simple CLI interface to some functions of iRedMail. Many admins like CLI tools more like web management. 

It's good to have ability to do some basic thinks via command line. This tool in fact use configuration and many other functions from original Web interface. So original iredadmin is one of requirements

#Currently supported features
* Add domain
* Add new mailbox
* Searech in domains and mailbox

#TODO
* Delete domain with all accounts
* Delete single account

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







