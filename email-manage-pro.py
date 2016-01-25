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

# Classes definition {{{
class colors:
    NOC     = '\033[0m'
    GREEN   = '\033[92m'
    RED     = '\033[91m'
    BLUE    = '\033[94m'

#}}} Classes definition

# Functions definition {{{
def web_log(domain, event, msg, loglevel="info"):
    """Logging to web interface"""
    
    sql = "INSERT INTO log (admin, domain, event, loglevel, msg, ip) VALUES ('root-cli', '%s', '%s', '%s', '%s', '127.0.0.1')" % (domain, event, loglevel,msg)
   
    if not insert_sql_query(db_iredadmin, sql):
        print colors.RED + "Logging not work !" + colors.NOC

def exit_script(msg,returncode):
    """Exist script"""
    if returncode == 0:
        msg_output = colors.GREEN + msg + colors.NOC
    else:
        msg_output = colors.RED + "ERROR: " + msg + colors.NOC

    print msg_output
    sys.exit(returncode)

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
        print "Aliases"
        #sql = "SELECT address, goto, name, domain, case when active then 'yes' else 'no' end as 'Active' FROM alias WHERE address like '%" + search_string + "%'"
        sql = "SELECT address, REPLACE(goto, ',', ',\n') AS goto, name, domain, case when active then 'yes' else 'no' end as 'Active' FROM alias WHERE address like '%" + search_string + "%'"
        result = send_sql_query(db_vmail, sql)
        print_results(result)

def action_list_user_aliases(user,inpt):
    """ Func for list aliases which are pointing to user """
    sql = "SELECT address from alias where goto regexp '^" + user + "|," + user + "';"
    result = send_sql_query(db_vmail, sql)
    aliases = list(result)
    output = set()
    output.add(user)
    for alias in aliases:
        if alias[0] == user:
            continue
        if alias[0] in output:
            continue
        if inpt and alias[0] in inpt:
            continue
        output.update(action_list_user_aliases(alias[0],output))

    return output

def check_alias_exist(dbobject):
    """Check if alias exist in database"""
    if iredutils.is_email(dbobject):
    # Check if email exist
        sql = "SELECT address FROM alias WHERE address = '%s'" % (dbobject)
    else:
        return False

    result = send_sql_query(db_vmail, sql)
   
    if result.fetchone() != None:
        return True
    else:
        return False

def check_object_exist(dbobject):
    """Check if domain or mailbox exist in database"""
    if iredutils.is_email(dbobject):
    # Check if email exist
        sql = "SELECT username FROM mailbox WHERE username = '%s'" % (dbobject)
    else:
    # Check if domain exist
        sql = "SELECT domain FROM domain WHERE domain = '%s'" % (dbobject)

    result = send_sql_query(db_vmail, sql)
   
    if result.fetchone() != None:
        return True
    else:
        return False

def delete_object(domain, mailbox):
    """Delete domain or mailbox from iRedMail"""
    
    if domain:
        exit_script("Removing whole domains currently not supported", 1)

    elif mailbox:

        if not iredutils.is_email(mailbox):
            exit_script("Invalid email", 1)

        if check_object_exist(mailbox):
            # Do some search and ask user
            search_database(False,False,mailbox)
            
            print "Do you want to remove all of these ? (y/n)"
            choice = raw_input().lower()
            
            if choice == "y":
                sql = "DELETE FROM mailbox WHERE username = '%s'" % (mailbox)
                # Remove mailbox
                if insert_sql_query(db_vmail, sql):
                    print colors.GREEN + "Mailbox removed successfully" + colors.NOC
                    web_log(mailbox.split('@')[1], 'delete', 'Delete user: %s' % (mailbox))
                    # Now remove aliases
                    sql = "DELETE FROM alias WHERE address = '%s'" % (mailbox)
                    if insert_sql_query(db_vmail,sql):
                        print colors.GREEN + "Alias removed successfully" + colors.NOC
                    else:
                        print colors.RED + "Alias NOT removed" + colors.NOC
                        
                else:
                    exit_script("Mailbox not removed", 1)
            else:
                exit_script("Exiting", 0)
        else:
            exit_script("Mailbox: %s not exist" % mailbox, 1)

    exit_script("Object deleted", 0)

def add_object(domain, mailbox):
    """Add domain or mailbox to iRedMail"""
    if domain:
        # Remove whitespace chars
        domain = domain.strip()

        if not iredutils.is_domain(domain):
            exit_script("Invalid domain name", 1)
        
        if args.backupmx:
            backupmx = 1
        else:
            backupmx = 0


        #insert_policyd_status = 1

        sql = "INSERT INTO domain (domain, settings, backupmx) VALUES ('%s','default_user_quota:0;default_language:%s;max_user_quota:0;',%d)" % (domain, settings.default_language, backupmx)
        # Insert object to database
        if insert_sql_query(db_vmail, sql):
            web_log(domain, 'create', 'Create domain: %s' % (domain))
        else:
            exit_script("Error inserting into vmail database, domain not added", 1)
        
        #sql = "INSERT INTO policy_group_members (PolicyGroupID, Member, Disabled) VALUES (2,'@%s',0)" % (domain)
        ## Insert object to database policyd
        #if insert_sql_query(db_policy, sql):
        #    insert_policyd_status = 0
        #
        #if insert_policyd_status == 1:
        #    exit_script("Domain added but problem during inserting into policy database", 1)

        exit_script("Domain added", 0)



    elif mailbox:
        # Remove whitespace chars
        mailbox = mailbox.strip()

        if not iredutils.is_email(mailbox):
            exit_script("Invalid email", 1)

        # Get domain and user
        domain = mailbox.split('@')[1]
        user = mailbox.split('@')[0]
        username = mailbox

        if not check_object_exist(domain):
            exit_script("Not added, domain %s not exist" % (domain), 1)
        
        # Generate random string for password
        random_string = iredutils.generate_random_strings()

        # Prepare plain or encrypted password
        pwscheme = None

        try:
            settings.STORE_PASSWORD_IN_PLAIN_TEXT
        except:
            settings.STORE_PASSWORD_IN_PLAIN_TEXT = False

        if settings.STORE_PASSWORD_IN_PLAIN_TEXT:
            pwscheme = 'PLAIN'
        password = iredpwd.generate_password_hash(random_string, pwscheme=pwscheme)

        maildir = iredutils.generate_maildir_path(mailbox)

        local_part = user.strip().lower()

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
        # Insert object to database
        if insert_sql_query(db_vmail, sql):
            print colors.GREEN + "Generated new email account:" + colors.NOC
            print "Username: %s\nPassword: %s\nDomain: %s" % (username, random_string, domain)
            web_log(domain, 'create', 'Create user %s' % (mailbox))
            # Create initial alias
            sql = "INSERT INTO alias (address, goto, domain, islist) VALUES ('%s', '%s', '%s', 0)" % (username, username, domain)
            if insert_sql_query(db_vmail, sql):
                print "Initial alias added"
            else: 
                exit_script("Initial alias not added", 1)
        else:
            exit_script("Error, email not added", 1)

def action_add_alias(address, send_to):
    """Add alias"""

    # check if domain exist
    if not address:
        exit_script("Alias address not specified", 1)
    if not send_to:
        exit_script("Alias destination address not specified", 1)
    # Remove whitespaces
    address = address.strip()
    send_to = send_to.strip()

    domain = address.split('@')[1]

    if iredutils.is_domain(domain):
        if check_object_exist(domain):
            if check_alias_exist(address):
                search_database(False,False,address)
                ans = raw_input('Would you like to update alias ? (y/n) [n]: ')
                if ans.lower() == "y":
                    sql = "UPDATE alias SET goto = '%s' WHERE address = '%s' AND domain = '%s'" % (send_to, address, domain)
                else:
                    exit_script("Exiting", 0)
            else:
                sql = "INSERT INTO alias (address, goto, domain, islist) VALUES ('%s', '%s', '%s', 1)" % (address, send_to, domain)

            if insert_sql_query(db_vmail,sql):
                exit_script("Alias updated/added successfully", 0)
            else:
                exit_script("Alias not updated/added", 1)
        else:
            exit_script("Domain not exist", 1)
    else:
        exit_script("Invalid domain name", 1)


def action_changepass(mailbox, pass_from_prompt):
    """Changing password for mailbox account"""

    if not mailbox:
        exit_script("No mailbox entered", 1)

    if not iredutils.is_email(mailbox):
        exit_script("Invalid email", 1)

    if not check_object_exist(mailbox):
        exit_script("Mailbox %s not exist" % (mailbox), 1)

    if pass_from_prompt:
        random_string = pass_from_prompt
    else:
        # Generate random string for password
        random_string = iredutils.generate_random_strings()
    # Prepare plain or encrypted password
    pwscheme = None
    try:
        settings.STORE_PASSWORD_IN_PLAIN_TEXT
    except:
        settings.STORE_PASSWORD_IN_PLAIN_TEXT = False

    if settings.STORE_PASSWORD_IN_PLAIN_TEXT:
        pwscheme = 'PLAIN'
    password = iredpwd.generate_password_hash(random_string, pwscheme=pwscheme)

    # Now update password field in database
    sql = "UPDATE mailbox set password = '%s' WHERE username = '%s'" % (password, mailbox)
    if insert_sql_query(db_vmail, sql):
        print "Email: %s\nPassword: %s\n" % (mailbox, random_string)
        exit_script("Password successfuly updated", 0)
    else:
        exit_script("Passwor update not successful", 1)


#}}}

try:
    # Import some iRedMail libraries
    import settings
    from libs import iredutils,iredpwd
except:
    msg = "Could not import iRedAdmin settings, check iredadmin_install_path\nCurrent path is set to: %s" % (iredadmin_install_path)
    exit_script(msg, 1)

if settings.backend != 'mysql':
    exit_script("This script does not support any backends except mysql, sorry", 1)


parser = argparse.ArgumentParser(
    description= 'Manage iRedAdmin MySQL from console', 
    epilog='Created by Robert Vojcik <robert@vojcik.net>')

listgroup = parser.add_argument_group('List','List aliases and mailboxes')
listgroup.add_argument("-l", action="store_true", dest="action_search", default=False, help="Print domain, mailbox or find using SEARCH_STRING")
listgroup.add_argument("-s", dest="search_string", default=False, help="Search database for mail account")

addobject = parser.add_argument_group('Add/Delete','Add or delete aliases, mailboxes and domains')
addobject.add_argument("-a", action="store_true", dest="action_add", default=False, help="Add domain or mailbox")
addobject.add_argument("-x", action="store_true", dest="action_delete", default=False, help="Delete domain or mailbox")
addobject.add_argument("-A", action="store_true", dest="action_add_alias", default=False, help="Add alias")
addobject.add_argument("--backup-mx", action="store_true", dest="backupmx", default=False, help="If set, added domain is marked as backup-mx")
addobject.add_argument("--address", dest="alias_address", default=False, help="Alias address")
addobject.add_argument("--send-to", dest="alias_to", default=False, help="Alias destination addresses separated by comas")
addobject.add_argument("--list-user-aliases", dest="action_list_user_aliases", default=False, help="List aliases directing to username - example petr.burian@livesport.eu")

parserchpw = parser.add_argument_group('Change password','Change password for mailbox')
parserchpw.add_argument("-w", action="store_true", dest="action_changepass", default=False, help="Change password for mailbox")
parserchpw.add_argument("-p", dest="pass_from_prompt", default=False, help="Password used when changing password for mailbox")

commonargs = parser.add_argument_group('Common options', 'Some of the arguments are common for entire CLI')
commonargs.add_argument("-d", dest="domain", default=False, help="Search, Add or delete domain")
commonargs.add_argument("-m", dest="mailbox", default=False, help="Search mailbox, Add new mailbox, Change password for mailbox")


args = parser.parse_args()

# Connect to databases {{{
# Vmail database
try:
    db_vmail = MySQLdb.connect(
        host=settings.vmail_db_host,
        port=int(settings.vmail_db_port),
        passwd=settings.vmail_db_password,
        user=settings.vmail_db_user,
        db=settings.vmail_db_name)
    send_sql_query(db_vmail, "SET NAMES 'utf8'")
except MySQLdb.Error, e:
    print "Can't connect to iRedMail Vmail database"
    print "Error %d: %s" % (e.args[0],e.args[1])
    exit_script("Database error", 1)

# iredadmin database
try:
    db_iredadmin = MySQLdb.connect(
        host=settings.iredadmin_db_host,
        port=int(settings.iredadmin_db_port),
        passwd=settings.iredadmin_db_password,
        user=settings.iredadmin_db_user,
        db=settings.iredadmin_db_name)
    send_sql_query(db_iredadmin, "SET NAMES 'utf8'")
except MySQLdb.Error, e:
    print "Can't connect to iRedMail iRedAdmin database"
    print "Error %d: %s" % (e.args[0],e.args[1])
    exit_script("Database error", 1)

## policy database
#try:
#    db_policy = MySQLdb.connect(
#        host=settings.policyd_db_host,
#        port=int(settings.policyd_db_port),
#        passwd=settings.policyd_db_password,
#        user=settings.policyd_db_user,
#        db=settings.policyd_db_name)
#    send_sql_query(db_policy, "SET NAMES 'utf8'")
#except MySQLdb.Error, e:
#    print "Can't connect to iRedMail Policyd database"
#    print "Error %d: %s" % (e.args[0],e.args[1])
#    exit_script("Database error", 1)

#}}} Connect to databases

if args.action_search:
    search_database(args.domain, args.mailbox, args.search_string)
elif args.action_add:
    add_object(args.domain, args.mailbox)
elif args.action_delete:
    delete_object(args.domain, args.mailbox)
elif args.action_changepass:
    action_changepass(args.mailbox, args.pass_from_prompt)
elif args.action_add_alias:
    action_add_alias(args.alias_address, args.alias_to)
elif args.action_list_user_aliases:
    out=action_list_user_aliases(args.action_list_user_aliases,None)
    lst = list(out)
    lst.sort()
    print "\nAll aliases for user: "+args.action_list_user_aliases+"\n"
    for i in lst:
        print i
else:
    print "You have to specify some action\n"
    parser.print_help()

# Disconnect from databases {{{
db_vmail.close()
db_iredadmin.close()

#}}} Disconnect from databases
