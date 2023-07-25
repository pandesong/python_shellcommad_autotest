# -*- coding: utf-8-*-
import os
import unittest
from  common import AmefsApiTest
import time
import tools
global globpath
globpath = ""
tApi=tools.toolsApi()
AmefsApi=AmefsApiTest()
cur=tApi.getConCur()
configpath="C:\\Users\\pandesong\\Desktop\\ameds_test\\ameds_testcase.conf"
def execmd(cmd):
    return tApi.execmd(cmd)



class TestfileStorageRebalance(unittest.TestCase):
    def __init__(self,*args,**kwargs):
        super(TestfileStorageRebalance,self).__init__(*args,**kwargs)

    @classmethod
    def setUpClass(self):
        global ip
        global port
        global user
        global password
        global config_json
        global ldap_server
        global ldap_pwd
        global ldap_user_dn
        global ldap_base_dn
        global userpwd
        global ldap_user_ou
        ip, port, user, password, config_json, ldap_server, ldap_pwd, ldap_user_dn, ldap_base_dn, userpwd, ldap_user_ou = tApi.get_config(configpath)
        session = tApi.ssh_login(str(ip), int(port), str(user), str(password))
        assert session == 0,("%s  %s  %s  %s") % (str(ip),str(port),str(user), str(password))




    @classmethod
    def tearDownClass(self):
        cur.execute("drop  table  if exists   hostunit")
        cur.execute("drop  table  if exists   pooltest")
        pass

    def setUp(self):
        global ip
        global port
        global user
        global password
        sql_text_1 = '''CREATE TABLE if not EXISTS pooltest
                           (poolname TEXT,
                            poolunit TEXT);'''
        cur.execute(sql_text_1)
        sql_text_1 = '''CREATE TABLE if not EXISTS hostunit
                                   (hostname TEXT,
                                    units TEXT,isuse BOOL);'''
        cur.execute(sql_text_1)
        globals()['poolname'] = AmefsApi.create_disperse_pool(str(ip), int(port), str(user), str(password))


    def tearDown(self):
        rest = execmd(
            " echo 'y'| /usr/local/amefs/sbin/ame lvg   stop  %s force" % globals()['poolname'])
        rest = execmd(
            "echo  'y'| /usr/local/amefs/sbin/ame lvg delete %s" % globals()['poolname'])
        result = rest
        assert result.find("lvgroup delete: %s: success" % globals()['poolname']) >= 0,result
        cur.execute("select  poolunit from pooltest")
        data = cur.fetchall()

        for u in data[0]:
            AmefsApi.rm_unit(str(u).split(" "))
        cur.execute("drop  table  if exists   hostunit")
        cur.execute("drop  table  if exists   pooltest")

    def test_amefs_expansion_samenode(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  limit-usage   /group  1TB " % (
                globals()['poolname']))
        assert result.__contains__("lvgroup quota : success"), result
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  limit-usage   /group/user  1TB " % (
                globals()['poolname']))
        assert result.__contains__("lvgroup quota : success"), result
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;seq 5000|xargs  -n1 -i dd if=/dev/zero of=test{} bs=1M count=1  status=none " % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert str(result).__contains__("5000")
        AmefsApi.lvg_AddSameUnit(globals()['poolname'])
        result = execmd(
            "/usr/local/amefs/sbin/ame  lvg  info  %s |grep Unit|grep mnt|wc -l" % (
                globals()['poolname']))
        assert result.__contains__("6"), result
        result = execmd(
            "/usr/local/amefs/sbin/ame  lvg  quota  %s   list|grep  /|awk   '{print $1\",\"$2\",\"$3\",\"$4\",\"$5}'" % (
                globals()['poolname']))
        print(result)
        result = execmd(
            "/usr/local/amefs/sbin/ame  lvg  rebalance  %s start" % (
                globals()['poolname']))
        time.sleep(5)
        for i in range(1800):
            result = execmd(
                "/usr/local/amefs/sbin/ame  lvg  rebalance  %s status " % (
                    globals()['poolname']))
            if result.__contains__("in progress"):
                time.sleep(2)
            else:
                break
            print result
        tt=AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) + int(tt[3][1]) == 5000, int(tt[0][1]) + int(tt[3][1])
        assert int(tt[1][1]) + int(tt[4][1]) == 5000, int(tt[1][1]) + int(tt[4][1])
        assert int(tt[2][1]) + int(tt[5][1]) == 5000, int(tt[2][1]) + int(tt[5][1])
        result = execmd("rm  -rf  /exports/%s/group/user/*" % (globals()['poolname']))
        result = execmd("ls /exports/%s/group/user/|wc  -l" % (globals()['poolname']))
        assert result.__contains__("0"), result


    def test_amefs_expansion_othernode(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  limit-usage   /group  1TB " % (
                globals()['poolname']))
        assert result.__contains__("lvgroup quota : success"), result
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  limit-usage   /group/user  1TB " % (
                globals()['poolname']))
        assert result.__contains__("lvgroup quota : success"), result
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;seq 5000|xargs  -n1 -i dd if=/dev/zero of=test{} bs=1M count=1  status=none " % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert str(result).__contains__("5000")
        AmefsApi.lvg_AddDiffUnit(globals()['poolname'])
        result = execmd(
            "/usr/local/amefs/sbin/ame  lvg  info  %s |grep Unit|grep mnt|wc -l" % (
                globals()['poolname']))
        assert result.__contains__("6"), result
        result = execmd(
            "/usr/local/amefs/sbin/ame  lvg  quota  %s   list|grep  /|awk   '{print $1\",\"$2\",\"$3\",\"$4\",\"$5}'" % (
                globals()['poolname']))
        print(result)
        result = execmd(
            "/usr/local/amefs/sbin/ame  lvg  rebalance  %s start" % (
                globals()['poolname']))
        time.sleep(5)
        for i in range(1800):
            result = execmd(
                "/usr/local/amefs/sbin/ame  lvg  rebalance  %s status " % (
                    globals()['poolname']))
            if result.__contains__("in progress"):
                print result
                time.sleep(2)
            else:
                break
        print result
        tt=AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) + int(tt[3][1]) == 5000, int(tt[0][1]) + int(tt[3][1])
        assert int(tt[1][1]) + int(tt[4][1]) == 5000, int(tt[1][1]) + int(tt[4][1])
        assert int(tt[2][1]) + int(tt[5][1]) == 5000, int(tt[2][1]) + int(tt[5][1])
        result = execmd("rm  -rf  /exports/%s/group/user/*" % (globals()['poolname']))
        result = execmd("ls /exports/%s/group/user/|wc  -l" % (globals()['poolname']))
        assert result.__contains__("0"), result

    def test_amefs_expansion_rebalancing_deletefileAandDir(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  limit-usage   /group  1TB " % (
                globals()['poolname']))
        assert result.__contains__("lvgroup quota : success"), result
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  limit-usage   /group/user  1TB " % (
                globals()['poolname']))
        assert result.__contains__("lvgroup quota : success"), result

        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result

        result = execmd(
            "cd /exports/%s/group/user;for i in {0..9};do mkdir  tt$i;cd tt$i;seq 500|xargs  -n1 -i dd if=/dev/zero of=test{} bs=1M count=1  status=none;cd ..;done " % (
                globals()['poolname']))
        result = execmd(
            "cd /exports/%s/group/user;seq 500|xargs  -n1 -i dd if=/dev/zero of=test{} bs=1M count=1  status=none " % (
                globals()['poolname']))

        result = execmd(
            "find /exports/%s/group/user  -type f |wc  -l" % (
                globals()['poolname']))
        assert str(result).__contains__("5500")
        AmefsApi.lvg_AddSameUnit(globals()['poolname'])
        result = execmd(
            "/usr/local/amefs/sbin/ame  lvg  info  %s |grep Unit|grep mnt|wc -l" % (
                globals()['poolname']))
        assert result.__contains__("6"), result
        result = execmd(
            "/usr/local/amefs/sbin/ame  lvg  quota  %s   list|grep  /|awk   '{print $1\",\"$2\",\"$3\",\"$4\",\"$5}'" % (
                globals()['poolname']))
        print(result)
        result = execmd(
            "/usr/local/amefs/sbin/ame  lvg  rebalance  %s start" % (
                globals()['poolname']))
        time.sleep(5)
        for i in range(1800):
            result = execmd(
                "/usr/local/amefs/sbin/ame  lvg  rebalance  %s status " % (
                    globals()['poolname']))
            if result.__contains__("in progress"):
                break
        print result
        result = execmd("rm  -rf  /exports/%s/group/user/*" % (globals()['poolname']))
        result = execmd("ls /exports/%s/group/user/|wc  -l" % (globals()['poolname']))
        assert result.__contains__("0"), result
        result = execmd("/usr/local/amefs/sbin/ame  lvg   status  %s|grep  mnt|awk  '{ print $5}'|wc -l" % (globals()['poolname']))
        assert result.__contains__("6"), result
        tt=AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) + int(tt[3][1]) == 0, int(tt[0][1]) + int(tt[3][1])
        assert int(tt[1][1]) + int(tt[4][1]) == 0, int(tt[0][1]) + int(tt[4][1])
        assert int(tt[2][1]) + int(tt[5][1]) == 0, int(tt[0][1]) + int(tt[5][1])





if __name__ == "__main__":
    os.path.join(os.getcwd(),"testcase_dir")
    runner=unittest.TextTestRunner()
    testunit = unittest.TestSuite()
    testunit.addTests(unittest.TestLoader().loadTestsFromTestCase(TestfileStorageRebalance))
    runner.run(testunit)
