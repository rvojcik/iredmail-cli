#!/usr/bin/python

import sys
import re
import argparse
import MySQLdb
from prettytable import from_db_cursor

# iRedAdmin location
iredadmin_install_path = '/usr/share/apache2/iredadmin'
# Add to path list
sys.path.append(iredadmin_install_path)

# Functions definition {{{

def print_results(cursor_object):
    """Print results from database in nice table"""
    table = from_db_cursor(cursor_object)
    table.align = 'l'
    print table

def send_sql_query(dbobject, query):
    """Send query to database"""
    # Set database cursor
    dbresult = dbobject.cursor()
    dbresult.execute(query)
    return dbresult

def insert_sql_query(dbobject, query):
    """Insert statement to database object"""
    # Set database cursor
    dbresult = dbobject.cursor()
    try:
        dbresult.execute(query)
        dbobject.commit()
    except:
        return False

    return True

def search_database(domain,mailbox,search_string):
    """Func for list or search database for domains or mailboxes"""
    # Search for domains
    if domain:
        sql = "SELECT domain, description, transport, case when backupmx then 'yes' else 'no' end as 'Backup MX' FROM domain WHERE domain like '%" + domain + "%'"
        result = send_sql_query(db_vmail, sql)
        print_results(result)
    # Search for mailboxes
    elif mailbox:
        sql = "SELECT username, name, domain, case when active then 'yes' else 'no' end as 'Active', quota FROM mailbox WHERE username like '%" + mailbox + "%'"
        result = send_sql_query(db_vmail, sql)
        print_results(result)
    # Search both, mailboxes and domains
    else:
        print "Domains"
        sql = "SELECT domain, description, transport, case when backupmx then 'yes' else 'no' end as 'Backup MX' FROM domain WHERE domain like '%" + search_string + "%'"
        result = send_sql_query(db_vmail, sql)
        print_results(result)
        print "Mailboxes"
        sql = "SELECT username, name, domain, case when active then 'yes' else 'no' end as 'Active', quota FROM mailbox WHERE username like '%" + search_string + "%'"
        result = send_sql_query(db_vmail, sql)
        print_results(result)


def add_object(domain, mailbox):
    """Add domain to iRedMail"""
    if domain:
        sql = "INSERT INTO domain (domain, defaultlanguage, defaultuserquota) VALUES ('%s','%s',0)" % (domain, settings.default_language)
    elif mailbox:
        # Get domain and user
        domain = mailbox.split('@')[1]
        user = mailbox.split('@')[0]
        username = mailbox

        # Generate random string for password
        random_string = iredutils.generate_random_strings()

        # Prepare plain or encrypted password
        pwscheme = None
        if settings.STORE_PASSWORD_IN_PLAIN_TEXT:
            pwscheme = 'PLAIN'
        password = iredutils.generate_password_for_sql_mail_account(random_string, pwscheme=pwscheme)

        maildir = iredutils.generate_maildir_path(mailbox)

        local_part = username.strip().lower()

        # Get storage base directory.
        tmpStorageBaseDirectory = settings.storage_base_directory
        splitedSBD = tmpStorageBaseDirectory.rstrip('/').split('/')
        storageNode = splitedSBD.pop()
        storageBaseDirectory = '/'.join(splitedSBD)

        sql = '''INSERT INTO mailbox (
            username, 
            password, 
            language, 
            storagebasedirectory, 
            storagenode, 
            maildir, 
            quota, 
            domain, 
            local_part, 
            active) VALUES (
            '%s',
            '%s',
            '%s',
            '%s',
            '%s',
            '%s',
            '%d',
            '%s',
            '%s',
            '%d')''' % (username, password, settings.default_language, storageBaseDirectory, storageNode, maildir, 0, domain, local_part, 1)
        print "Generated new account:"
        print "Username: %s\nPassword: %s\nDomain: %s" % (username, random_string, domain)

        

    # Insert object to database
    if insert_sql_query(db_vmail, sql):
        print "Object added"
    else:
        print "Error, object not added"

#}}}

try:
    import settings
    from libs import iredutils
except:
    print "Could not import iRedAdmin settings, check iredadmin_install_path"
    print "Current path is set to:", iredadmin_install_path
    sys.exit(1)

if settings.backend != 'mysql':
    print "This script does not support any backends except mysql, sorry"
    sys.exit(1)


parser = argparse.ArgumentParser(
    description='Manage iRedAdmin MySQL from console',
    epilog='Created by Robert Vojcik <robert@vojcik.net>')
parser.add_argument("-s", dest="search_string", default=False, help="Search database for mail account")
parser.add_argument("-d", dest="domain", default=False, help="Search, add or delete domain")
parser.add_argument("-m", dest="mailbox", default=False, help="Search, add or delete mailbox")
parser.add_argument("-a", action="store_true", dest="action_add", default=False, help="Add domain or mailbox")
parser.add_argument("-x", action="store_true", dest="action_delete", default=False, help="Delete domain or mailbox")
parser.add_argument("-l", action="store_true", dest="action_search", default=False, help="Print domain, mailbox or find using SEARCH_STRING")

args = parser.parse_args()

# Connect to databases {{{
# Vmail Database
try:
    db_vmail = MySQLdb.connect(
        host=settings.vmail_db_host,
        port=int(settings.vmail_db_port),
        passwd=settings.vmail_db_password,
        user=settings.vmail_db_user,
        db=settings.vmail_db_name)
except MySQLdb.Error, e:
    print "Can't connect to iRedMail Vmail database"
    print "Error %d: %s" % (e.args[0],e.args[1])
    sys.exit(1)

try:
    db_iredadmin = MySQLdb.connect(
        host=settings.iredadmin_db_host,
        port=int(settings.iredadmin_db_port),
        passwd=settings.iredadmin_db_password,
        user=settings.iredadmin_db_user,
        db=settings.iredadmin_db_name)
except MySQLdb.Error, e:
    print "Can't connect to iRedMail iRedAdmin database"
    print "Error %d: %s" % (e.args[0],e.args[1])
    sys.exit(1)
#}}} Connect to databases

if args.action_search:
    search_database(args.domain, args.mailbox, args.search_string)
elif args.action_add:
    add_object(args.domain, args.mailbox)
else:
    print "You have to specify some action\n"
    parser.print_help()

# Disconnect from databases {{{
db_vmail.close()
db_iredadmin.close()

#}}} Disconnect from databases
