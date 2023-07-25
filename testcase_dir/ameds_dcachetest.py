# -*- coding: utf-8-*-
import os
import unittest
import json
import time
import tools
from  common import AmefsApiTest

configpath="C:\\Users\\pandesong\\Desktop\\ameds_test\\ameds_testcase.conf"
tApi=tools.toolsApi()
cur=tApi.getConCur()
AmefsApi=AmefsApiTest()
global globpath
globpath = ""

def execmd(cmd):
    return tApi.texecmd(cmd)

def execmdbk(cmd):
    return tApi.texecmdbk(cmd)

def bkexecmd(cmd):
    return tApi.ssh_execex(cmd)

def setDcacheOn(poolname):
    result = execmd("/usr/local/amefs/sbin/ame lvg   set  %s  performance.dcache  on " % (poolname))
    result = execmd(
        "/usr/local/amefs/sbin/ame lvg  get  %s  performance.dcache|grep dcache|awk  '{ print $2 }' " % (poolname))
    assert str(result).__contains__("on"), result

def setDcacheOff(poolname):
    result = execmd("/usr/local/amefs/sbin/ame lvg   set  %s  performance.dcache  off " % (poolname))
    result = execmd(
        "/usr/local/amefs/sbin/ame lvg  get  %s  performance.dcache|grep dcache|awk  '{ print $2 }' " % (poolname))
    assert str(result).__contains__("off"), result
def createFiles():
    pass

def setQuota(poolname,quota):
    result = execmd(
        "/usr/local/amefs/sbin/ame lvg  quota  %s  limit-usage   /group  %s " % (
            poolname,quota))
    assert result.__contains__("lvgroup quota : success"), result
    result = execmd(
        "/usr/local/amefs/sbin/ame lvg  quota  %s  limit-usage   /group/user  %s " % (
            poolname,quota))
    assert result.__contains__("lvgroup quota : success"), result


class TestfileStorageDcache(unittest.TestCase):
    def __init__(self,*args,**kwargs):
        super(TestfileStorageDcache,self).__init__(*args,**kwargs)

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
        ip, port, user, password, config_json, ldap_server, ldap_pwd, ldap_user_dn, ldap_base_dn, userpwd, ldap_user_ou = tApi.get_config(
            configpath)
        session = AmefsApi.init_amefs(str(ip), int(port), str(user), str(password))
        #assert session == 0,("%s  %s  %s  %s") % (str(ip),str(port),str(user), str(password))

    def readWriteLs(self,poolname):
        result = execmd(
            "cd /exports/%s/group/user;seq 500|xargs  -n 1 -i dd if=/dev/zero of=test{} bs=1M count=1  status=none " % (
            globals()['poolname']))
        result = execmd("cd /exports/%s/group/user;md5sum *  | awk    '{ print $1}'|sort|uniq" % poolname)
        assert result.split("\n").__len__() == 1, result
        result = execmd(
            "mkdir /exports/%s/group/user/test;cd /exports/%s/group/user/test;seq 500|xargs  -n 1 -i dd if=/dev/zero of=test{} bs=1M count=1  status=none " % (
            poolname, poolname))
        result = execmd(
            "cd /exports/%s/group/user/test;md5sum * |awk    '{ print $1}'|sort|uniq" % (poolname))
        assert result.split("\n").__len__() == 1, result
        result = execmd(
            "find  /exports/%s/group/user   -type f |wc -l" % (
                poolname))
        assert str(result).__eq__("1000")
        result = execmd(
            "ls  -l /exports/%s/group/user|grep -v total|awk   '{ print $1$2$3$4$5}'|uniq" % (
                poolname))
        result.__contains__("-rw-r--r--1rootroot1048576")
        assert result.split("\n").__len__() == 2, result
        result = execmd(
            "ls  -l /exports/%s/group/user/test|grep -v total|awk   '{ print $1$2$3$4$5}'|uniq" % (
                poolname))
        result.__contains__("-rw-r--r--1rootroot1048576")
        assert result.split("\n").__len__() == 1, result


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
        assert rest.__contains__("success"), rest
        rest = execmd(
            "echo  'y'| /usr/local/amefs/sbin/ame lvg   delete  %s " % globals()['poolname'])
        result = rest
        assert result.find("lvgroup delete: %s: success" % globals()['poolname']) >= 0,result
        cur.execute("select  poolunit from pooltest")
        data = cur.fetchall()
        for u in data[0]:
            AmefsApi.rm_unit(str(u).split(" "))
        cur.execute("drop  table  if exists   hostunit")
        cur.execute("drop  table  if exists   pooltest")


    def test_amefs_set_dcache_ReadAndWriteFileDir(self):
        result = execmd("/usr/local/amefs/sbin/ame lvg   set  %s  performance.dcache  on " % (globals()['poolname']))
        result = execmd("/usr/local/amefs/sbin/ame lvg  get  %s  performance.dcache|grep dcache|awk  '{ print $2 }' " % (globals()['poolname']))
        assert str(result).__contains__("on"), result
        result = execmd("/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (globals()['poolname']))
        result = execmd("cd  /exports/%s/;mkdir group;cd group;mkdir user" % (globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd("cd /exports/%s/group;ls " % (globals()['poolname']))
        assert result.__contains__("user"),result
        self.readWriteLs(globals()['poolname'])
        result = execmd("rm   -rf /exports/%s/group/user/*" % (globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user/  -type f |wc -l" % (globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_setdcache_AfterSetQuota_ReadFileCloseDcache(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        setDcacheOn(globals()['poolname'])
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;seq 5000|xargs  -n 1 -i dd if=/dev/zero of=test{} bs=1M count=1  status=none " % (
                globals()['poolname']))
        result = execmd("echo  'for i in {0..1000};do md5sum /exports/%s/group/user/test/* ;done  &'  > /tmp/xx.sh" % (
            globals()['poolname']))
        result = execmd("bash /tmp/xx.sh >/dev/null &")
        time.sleep(10)
        setDcacheOff(globals()['poolname'])
        for i in range(10):
            result = execmd(
            "cd /exports/%s/group/user;find  . -type f |wc -l" % (
                globals()['poolname']))
            assert result.__contains__("5000"),result
            time.sleep(2)
        result = execmd(
            "cd /exports/%s/group/user;rm -rf *" % (
                globals()['poolname']))
        result = execmd("cd /exports/%s/group/user;find  . -type f |wc -l" % (globals()['poolname']))
        assert result.__contains__("0"), result

    def test_amefs_setdcache_BeforeSetQuota_ReadFileCloseDcache(self):
        setDcacheOn(globals()['poolname'])
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
            "cd /exports/%s/group/user;seq 5000|xargs  -n 1 -i dd if=/dev/zero of=test{} bs=1M count=1  status=none " % (
                globals()['poolname']))
        result = execmdbk("for i in {0..1000};do md5sum /exports/%s/group/user/test/* ;done  " % (
            globals()['poolname']))
        #result = execmd("bash /tmp/xx.sh >/dev/null &")
        time.sleep(10)
        setDcacheOff(globals()['poolname'])
        for i in range(10):
            result = execmd(
                "cd /exports/%s/group/user;find  . -type f |wc -l" % (
                    globals()['poolname']))
            assert result.__contains__("5000"), result
            time.sleep(2)
        result = execmd(
            "cd /exports/%s/group/user;rm -rf *" % (
                globals()['poolname']))
        result = execmd("cd /exports/%s/group/user;find  . -type f |wc -l" % (globals()['poolname']))
        assert result.__contains__("0"), result

    def test_amefs_setdcache_BeforeSetQuota_Create70DirAnd10240Files_OpenDcache(self):
        result = execmd("/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (globals()['poolname']))
        result = execmd("cd  /exports/%s/;mkdir group;cd group;mkdir user" % (globals()['poolname']))
        # result = execmd("/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd  /exports/%s/group/user;for  i  in  {1..70};do   mkdir  test;cd test;done;seq 10240|xargs  -n 1  -i  dd if=/dev/zero of=test{} bs=1KB count=1  status=none" % (globals()['poolname']))
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "find /exports/%s/group/user  -type  f |wc  -l" % (
                globals()['poolname']))
        assert str(result).__eq__("10240"), result
        setDcacheOn(globals()['poolname'])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd("ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result


    def test_amefs_setdcache_AfterSetQuota_ReadFileCloseDcache(self):


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

        setDcacheOn(globals()['poolname'])


        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;seq 5000|xargs  -n 1 -i dd if=/dev/zero of=test{} bs=1M count=1  status=none " % (
                globals()['poolname']))

        result = execmdbk("for i in {0..1000};do md5sum /exports/%s/group/user/test/* ;done  " % (
            globals()['poolname']))
        #result = execmd("bash /tmp/xx.sh >/dev/null &")
        time.sleep(10)

        setDcacheOff(globals()['poolname'])


        for i in range(10):
            result = execmd(
                "cd /exports/%s/group/user;find  . -type f |wc -l" % (
                    globals()['poolname']))
            assert result.__contains__("5000"), result
            time.sleep(2)
        result = execmd(
            "cd /exports/%s/group/user;rm -rf *" % (
                globals()['poolname']))
        result = execmd("cd /exports/%s/group/user;find  . -type f |wc -l" % (globals()['poolname']))
        assert result.__contains__("0"), result


    def test_amefs_setdcache_AfterSetQuota_ReadFileOpenDcache(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;seq 5000|xargs  -n 1 -i dd if=/dev/zero of=test{} bs=1M count=1  status=none " % (
                globals()['poolname']))
        result = execmd(
            "cd /exports/%s/group/user;find  . -type f |wc -l" % (
                globals()['poolname']))
        assert str(result).__contains__("5000"), result
        result = execmdbk(
            "cd /exports/%s/group/user;for i in {0..1000};do md5sum  * ;done" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        l=[]
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;ls |wc -l" % (
                    globals()['poolname']))
            if not result.__eq__("5000"):
                len=l.__len__()
                l.append(result)
                l=list(set(l))
                if l.__len__()==len:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(1)
            else:break
        assert result.__eq__("5000"), result
        result = execmd(
            "cd /exports/%s/group/user;rm -rf *" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user|wc -l" % (
                globals()['poolname']))
        assert str(result).__contains__("0"), result

    def test_amefs_setdcache_AfterSetQuota_ReadFileDeleteFileCloseDcache(self):
        setDcacheOn(globals()['poolname'])
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "mkdir /exports/%s/group/user/test" % (
                globals()['poolname']))
        result = execmd(
            "cd /exports/%s/group/user/test;seq 5000|xargs  -n 1 -i dd if=/dev/zero of=test{} bs=1M count=1  status=none " % (
                globals()['poolname']))
        result = execmdbk("for i in {0..1000};do md5sum /exports/%s/group/user/test/* ;done" % (globals()['poolname']))
        #result = execmd("bash /tmp/xx.sh >/dev/null &")
        time.sleep(5)
        result = execmdbk(
            "rm -rf  /exports/%s/group/user/test" % (
                globals()['poolname']))
        #result = execmd("bash /tmp/xx1.sh  >/dev/null &")
        for i in range(1800):
            result = execmd(
            "cd /exports/%s/group/user/;find  . -type f |wc -l" % (
                globals()['poolname']))
            #print result
            if not result.__eq__("5000"):
                setDcacheOff(globals()['poolname'])
                break

            time.sleep(2)

        for i in range(1800):
            result = execmd(
            "cd /exports/%s/group/user/;find  . -type f |wc -l" % (
                globals()['poolname']))
            print result
            if  result.__eq__("0"):
                break
            time.sleep(2)

    def test_amefs_setdcache_AfterSetQuota_ReadFileDeleteFileOpenDcache(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "mkdir /exports/%s/group/user/test" % (
                globals()['poolname']))
        result = execmd(
            "cd /exports/%s/group/user/test;seq 5000|xargs  -n 1 -i dd if=/dev/zero of=test{} bs=1M count=1  status=none " % (
                globals()['poolname']))
        result = execmdbk("for i in {0..1000};do md5sum /exports/%s/group/user/test/* ;done" % (
        globals()['poolname']))
        #result = execmd("bash /tmp/xx.sh >/dev/null &")
        time.sleep(5)
        result = execmdbk(
            "rm -rf  /exports/%s/group/user/test" % (
                globals()['poolname']))
        #result = execmd("bash /tmp/xx.sh  >/dev/null &")
        for i in range(1800):
            result = execmd(
                "cd /exports/%s/group/user/;find  . -type f  2>/dev/null|wc -l" % (
                    globals()['poolname']))
            print result
            if not result.__eq__("5000"):
                setDcacheOn(globals()['poolname'])
                break
            time.sleep(2)

        for i in range(1800):
            result = execmd(
                "cd /exports/%s/group/user/;find  . -type f |wc -l" % (
                    globals()['poolname']))
            print result
            if result.__eq__("0"):
                break
            time.sleep(2)

    def test_amefs_SetDcache_Before_Enable(self):
        setDcacheOn(globals()['poolname'])
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
            globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"),result

    def test_amefs_SetDcache_BeforeStartStorage(self):
        result = execmd("echo  'y'|/usr/local/amefs/sbin/ame lvg stop  %s" % (globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        result = execmd("/usr/local/amefs/sbin/ame lvg   start  %s" % (globals()['poolname']))
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
            globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"),result

    def test_amefs_SetDcache_AfterSetQuota(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
            globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"),result
        self.readWriteLs(globals()['poolname'])

    def test_amefs_SetDcache_AfterEnableQuota(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
            globals()['poolname']))

        setQuota(globals()['poolname'], "1TB")


        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"),result
        result = execmd(
            "cd /exports/%s/group;dd if=/dev/zero of=test bs=1M count=10  status=none " % (
                globals()['poolname']))
        result = execmd(
            "cd /exports/%s/group;md5sum test " % (
                globals()['poolname']))
        assert result.__contains__("f1c9645dbc14efddc7d8a322685f26eb"),result


    def test_amefs_SetDcache_afterSetQuotaEnableBeforeExpansion(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
            globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group/user;seq 5000|xargs  -n 1 -i dd if=/dev/zero of=test{} bs=1M count=1  status=none " % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert  str(result).__contains__("5000"),result

        setDcacheOn(globals()['poolname'])

        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"),result
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  limit-usage   /group  2TB " % (
                globals()['poolname']))
        assert result.__contains__("lvgroup quota : success"), result
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  limit-usage   /group/user  2TB " % (
                globals()['poolname']))

        assert result.__contains__("lvgroup quota : success"), result

        result = execmd(
            "/usr/local/amefs/sbin/ame  lvg  quota  %s   list|grep  /|awk   '{print $1\",\"$2\",\"$3\",\"$4\",\"$5}'" % (
                globals()['poolname']))
        print(result)

        execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"),result

    def test_amefs_SetDcache_aftersetquotaEnableTwice(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
            globals()['poolname']))

        setDcacheOn(globals()['poolname'])

        setQuota(globals()['poolname'], "1TB")
        setDcacheOff(globals()['poolname'])

        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"),result
        result = execmd(
            "cd /exports/%s/group/user;dd if=/dev/zero of=test bs=1M count=1  status=none " % (
                globals()['poolname']))

        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert  str(result).__eq__("1")
        result = execmd(
            "md5sum /exports/%s/group/user/test" % (
                globals()['poolname']))
        assert  result.__contains__("b6d81b360a5672d80c27430f39153e2c"),result
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  limit-usage   /group/user  2TB " % (
                globals()['poolname']))
        assert result.__contains__("lvgroup quota : success"), result
        result = execmd(
            "/usr/local/amefs/sbin/ame  lvg  quota  %s   list|grep  /|awk   '{print $1\",\"$2\",\"$3\",\"$4\",\"$5}'" % (
                globals()['poolname']))
        print(result)
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"),result

    def test_amefs_SetDcache_stopAndStartStorage(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        setQuota(globals()['poolname'], "1TB")

        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result

        self.readWriteLs(globals()['poolname'])
        result = execmd("echo 'y'|/usr/local/amefs/sbin/ame  lvg  stop %s" % (globals()['poolname']))
        assert  result.__contains__(": success"),result
        time.sleep(10)
        result = execmd("/usr/local/amefs/sbin/ame  lvg  start %s  force" % (globals()['poolname']))
        assert result.__contains__(": success"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1])  == 1000, int(tt[0][1])
        assert int(tt[1][1]) == 1000, int(tt[1][1])
        assert int(tt[2][1])  == 1000, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_setdcache_BeforeSetQuota_CreateSeventyDirAnd10240Files_CloseDcache(self):
        result = execmd("/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (globals()['poolname']))
        result = execmd("cd  /exports/%s/;mkdir group;cd group;mkdir user" % (globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        #result = execmd("/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd("cd  /exports/%s/group/user;for  i  in  {1..70};do   mkdir  test;cd test;done;seq 10240|xargs  -n 1  -i  dd if=/dev/zero of=test{} bs=1KB count=1  status=none" % (globals()['poolname']))
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "find /exports/%s/group/user  -type  f |wc  -l" % (
                globals()['poolname']))
        assert str(result).__eq__("10240"),result
        setDcacheOff(globals()['poolname'])
        result = execmd(
            "cd   /exports/%s/group/user/;for  i  in  {1..70};do cd test;done;rm -rf *" % (
                globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user/  -type f |wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_setdcache_BeforeSetQuota_CreateSeventyDirAnd1024FilesThenCloseDcache(self):
        result = execmd("/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (globals()['poolname']))
        result = execmd("cd  /exports/%s/;mkdir group;cd group;mkdir user" % (globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        # result = execmd("/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmdbk(
            "cd  /exports/%s/group/user;for  i  in  {1..70};do   mkdir  test;cd test;done;" % (
            globals()['poolname']))
        setDcacheOff(globals()['poolname'])
        l=[]
        for i in range(1200):
            result = execmd(
                "find /exports/%s/group/user  -type  d |wc  -l" % (
                    globals()['poolname']))
            if not result.__eq__("71"):
                len=l.__len__()
                l.append(result)
                l=list(set(l))
                if l.__len__()==len:
                    assert False
                else:
                    break
                time.sleep(1)
            else:
                break
        assert result.__eq__("71")
        setDcacheOn(globals()['poolname'])
        result = execmdbk(
            "cd  /exports/%s/group/user;for  i  in  {1..70};do cd test;done;seq 1024|xargs  -n 1  -i  dd if=/dev/zero of=test{} bs=1KB count=1  status=none" % (
                globals()['poolname']))
        time.sleep(5)
        setDcacheOff(globals()['poolname'])
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;for  i  in  {1..70};do cd test;done;ls|wc -l" % (
                    globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__eq__("1024"):
                len=l.__len__()
                l.append(result)
                l=list(set(l))
                if l.__len__()==len:
                    assert False
                time.sleep(1)
            else:
                break
        assert result.__eq__("1024")

        result = execmd(
            "cd   /exports/%s/group/user/;for  i  in  {1..70};do cd test;done;seq 1024|xargs  -n 1  -i  rm -rf test{} " % (
                globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user/  -type f |wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_setdcache_BeforeSetQuota_CreateSeventyDirAnd1024FilesThenOpenDcache(self):
        result = execmd("/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (globals()['poolname']))
        result = execmd("cd  /exports/%s/;mkdir group;cd group;mkdir user" % (globals()['poolname']))
        #result = execmd("/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmdbk(
            "cd  /exports/%s/group/user;for  i  in  {1..70};do   mkdir  test;cd test;done;" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        l = []
        for i in range(1200):
            result = execmd(
                "find /exports/%s/group/user  -type  d |wc  -l" % (
                    globals()['poolname']))
            if not result.__eq__("71"):
                len = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == len:
                    assert False
                else:
                    break
                time.sleep(1)
            else:
                break
        assert result.__eq__("71"),result
        setDcacheOff(globals()['poolname'])
        result = execmdbk(
            "cd  /exports/%s/group/user;for  i  in  {1..70};do cd test;done;seq 1024|xargs  -n 1  -i  dd if=/dev/zero of=test{} bs=1KB count=1  status=none" % (
                globals()['poolname']))
        time.sleep(5)
        setDcacheOn(globals()['poolname'])
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;for  i  in  {1..70};do cd test;done;ls|wc -l" % (
                    globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__eq__("1024"):
                len = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == len:
                    assert False
                time.sleep(1)
            else:
                break
        assert result.__eq__("1024"),result
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_setdcache_BeforeSetQuota_SetExtProperty_And_CloseDcache(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result

        result = execmd(
            "cd /exports/%s/group/user;dd if=/dev/zero of=test bs=1M count=1  status=none;setfattr   -n trusted.test-attr -v test123  test" % (
                globals()['poolname']))

        result = execmd(
            "cd /exports/%s/group/user;getfattr   -n trusted.test-attr  test" % (
                globals()['poolname']))

        assert result.__contains__("test123"), result
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert str(result).__eq__("1")
        setDcacheOff(globals()['poolname'])
        result = execmd(
            "cd /exports/%s/group/user;getfattr   -n trusted.test-attr  test" % (
                globals()['poolname']))
        assert result.__contains__("test123"), result
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("1"),result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 1, int(tt[0][1])
        assert int(tt[1][1])  == 1, int(tt[1][1])
        assert int(tt[2][1])== 1, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_setdcache_BeforeSetQuota_AfterSetExtProperty(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;dd if=/dev/zero of=test bs=1M count=1  status=none;setfattr   -n trusted.test-attr -v test123  test" % (
                globals()['poolname']))
        result = execmd(
            "cd /exports/%s/group/user;getfattr   -n trusted.test-attr  test" % (
                globals()['poolname']))
        assert result.__contains__("test123"), result
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("1"),result
        setDcacheOn(globals()['poolname'])
        result = execmd(
            "cd /exports/%s/group/user;getfattr   -n trusted.test-attr  test" % (
                globals()['poolname']))
        assert result.__contains__("test123"), result
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("1"),result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 1, int(tt[0][1])
        assert int(tt[1][1]) == 1, int(tt[1][1])
        assert int(tt[2][1]) == 1, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_DoNotsetdcache_BeforeSetQuota_AfterSetExtProperty(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))

        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result

        result = execmd(
            "cd /exports/%s/group/user;dd if=/dev/zero of=test bs=1M count=1  status=none;setfattr   -n trusted.test-attr -v test123  test" % (
                globals()['poolname']))

        result = execmd(
            "cd /exports/%s/group/user;getfattr   -n trusted.test-attr  test" % (
                globals()['poolname']))

        assert result.__contains__("test123"), result
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("1"),result

        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 1, int(tt[0][1])
        assert int(tt[1][1]) == 1, int(tt[1][1])
        assert int(tt[2][1]) == 1, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_setdcache_BeforeSetQuota_AfterSetExtPropertyThenCloseDcache(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd("cd /exports/%s/group/user;for i in {1..10240};do dd if=/dev/zero of=test$i bs=1M count=1  status=none;done" % (globals()['poolname']))
        result = execmdbk("cd /exports/%s/group/user;for i in {1..10240};do setfattr   -n trusted.test-attr -v test123  test$i;done" % globals()['poolname'])
        setDcacheOff(globals()['poolname'])
        flag=True
        while 1:
            result = execmd(
                "cd /exports/%s/group/user;for i in   {1..10240};do getfattr   -n trusted.test-attr  test$i|grep  trust|grep test123|awk  -F  '=' '{ print $2}';done|wc -l" % (globals()['poolname']))
            if not result.__contains__("10240"):
                print "属性未设置完等待中。。。"
                time.sleep(3)
            else:
                flag=False
                break
        assert flag == False
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert str(result).__eq__("10240")
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 10240, int(tt[0][1])
        assert int(tt[1][1]) == 10240, int(tt[1][1])
        assert int(tt[2][1]) == 10240, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_setdcache_BeforeSetQuota_AfterSetExtPropertyThenOpenDcache(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..10240};do dd if=/dev/zero of=test$i bs=1M count=1  status=none;done" % (
            globals()['poolname']))
        result = execmdbk("cd /exports/%s/group/user;for i in {1..10240};do setfattr   -n trusted.test-attr -v test123  test$i;done" % (
            globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        flag = True
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;for i in   {1..10240};do getfattr   -n trusted.test-attr  test$i|grep  trust|grep test123|awk  -F  '=' '{ print $2}';done|wc -l" % (
                globals()['poolname']))
            print "属性未设置完等待中。。。:%s"  % result
            if not result.__contains__("10240"):
                time.sleep(3)
            else:
                flag=False
                break
        assert flag==False
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert str(result).__eq__("10240")
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 10240, int(tt[0][1])
        assert int(tt[1][1]) == 10240, int(tt[1][1])
        assert int(tt[2][1]) == 10240, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_set_dcache_aftersetquota_Expansion_samenode(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
            globals()['poolname']))
        setDcacheOn(globals()['poolname'])

        setQuota(globals()['poolname'], "1TB")

        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))

        assert result.__contains__("user"),result
        result = execmd(
            "cd /exports/%s/group/user;seq 5000|xargs  -n1 -i dd if=/dev/zero of=test{} bs=1M count=1  status=none " % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert  str(result).__eq__("5000")
        AmefsApi.lvg_AddSameUnit(globals()["poolname"])
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
            print result
            if result.__contains__("in progress"):
                time.sleep(5)
            else:
                break
        tt=AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) + int(tt[3][1]) == 5000, int(tt[0][1]) + int(tt[3][1])
        assert int(tt[1][1]) + int(tt[4][1]) == 5000, int(tt[1][1]) + int(tt[4][1])
        assert int(tt[2][1]) + int(tt[5][1]) == 5000, int(tt[2][1]) + int(tt[5][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"),result

    def test_amefs_set_dcache_aftersetquota_Expansion_othernode(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
            globals()['poolname']))

        setDcacheOn(globals()['poolname'])

        setQuota(globals()['poolname'], "1TB")

        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"),result

        result = execmd(
            "cd /exports/%s/group/user;seq 5000|xargs  -n1 -i dd if=/dev/zero of=test{} bs=1M count=1  status=none " % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert  str(result).__contains__("5000")
        AmefsApi.lvg_AddDiffUnit(globals()['poolname'])
        result = execmd(
            "/usr/local/amefs/sbin/ame  lvg  quota  %s   list|grep  /|awk   '{print $1\",\"$2\",\"$3\",\"$4\",\"$5}'" % (
                globals()['poolname']))
        print(result)
        result = execmd(
            "/usr/local/amefs/sbin/ame  lvg  rebalance  %s start" % (
                globals()['poolname']))
        time.sleep(5)
        for i in range(1800):
            print result
            result = execmd(
                "/usr/local/amefs/sbin/ame  lvg  rebalance  %s status " % (
                    globals()['poolname']))
            print result
            if result.__contains__("in progress"):
                time.sleep(5)
            else:
                break

        tt=AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) + int(tt[3][1]) == 5000, int(tt[0][1]) + int(tt[3][1])
        assert int(tt[1][1]) + int(tt[4][1]) == 5000, int(tt[1][1]) + int(tt[4][1])
        assert int(tt[2][1]) + int(tt[5][1]) == 5000, int(tt[2][1]) + int(tt[5][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"),result

    def test_amefs_setdcache_BeforeSetQuota_AfterMvFileThenOpenDcache(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..10240};do dd if=/dev/zero of=test$i bs=1M count=1  status=none;done" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("10240")
        result = execmdbk("cd /exports/%s/group/user;for i in {1..10240};do mv  test$i   1234test$i;done" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        l=[]
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;ls|grep 1234test|wc -l" % (
                    globals()['poolname']))
            print "mv等待中。。。:%s" % result
            if not result.__contains__("10240"):
                ll=l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__()==ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("10240"),result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 10240, int(tt[0][1])
        assert int(tt[1][1]) == 10240, int(tt[1][1])
        assert int(tt[2][1]) == 10240, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_setDcache_BeforeSetQuota_AfterMvFile(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..10240};do dd if=/dev/zero of=test$i bs=1M count=1  status=none;done" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("10240")
        result = execmdbk("cd /exports/%s/group/user;for i in {1..10240};do mv  test$i   1234test$i;done" % (
            globals()['poolname']))
        l = []
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;ls|grep 1234test|wc -l" % (
                    globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__contains__("10240"):
                ll = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("10240"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 10240, int(tt[0][1])
        assert int(tt[1][1]) == 10240, int(tt[1][1])
        assert int(tt[2][1]) == 10240, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_DoNotsetDcache_BeforeSetQuota_AfterMvFile(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..10240};do dd if=/dev/zero of=test$i bs=1M count=1  status=none;done" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("10240")
        result = execmdbk("cd /exports/%s/group/user;for i in {1..10240};do mv  test$i   1234test$i;done" % (
            globals()['poolname']))
        l = []
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;ls|grep 1234test|wc -l" % (
                    globals()['poolname']))
            print "mv等待中。。。:%s" % result
            if not result.__contains__("10240"):
                ll = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd(
            "ls /exports/%s/group/user|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("10240"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 10240, int(tt[0][1])
        assert int(tt[1][1]) == 10240, int(tt[1][1])
        assert int(tt[2][1]) == 10240, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_setdcache_BeforeSetQuota_AfterMvDirThenOpenDcache(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..1024};do mkdir test$i;done" % (
                globals()['poolname']))
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..1024};do for x in {1..20};do dd if=/dev/zero of=test$i/test$x bs=1M count=1  status=none;done;done" % (globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert result.__eq__("20480"),result
        execmdbk("cd /exports/%s/group/user;for i in {1..1024};do mv  test$i   1234test$i;done" % (
            globals()['poolname']))
        time.sleep(5)
        setDcacheOn(globals()['poolname'])
        l = []
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;for i in {1..1024};do find 1234test$i/  -type f |wc -l;done|uniq|wc -l" % (
                globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__contains__("1024"):
                ll = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd("" % ( globals()['poolname']))
        assert str(result).__eq__("20480"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 20480, int(tt[0][1])
        assert int(tt[1][1]) == 20480, int(tt[1][1])
        assert int(tt[2][1]) == 20480, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_setdcache_BeforeSetQuota_AfterMvDirThenCloseDcache(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..1024};do mkdir test$i;done" % (
                globals()['poolname']))
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..1024};do for x in {1..20};do dd if=/dev/zero of=test$i/test$x bs=1M count=1  status=none;done;done" % (globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert result.__eq__("20480"),result
        execmdbk("cd /exports/%s/group/user;for i in {1..1024};do mv  test$i   1234test$i;done" % (
            globals()['poolname']))
        time.sleep(5)
        setDcacheOff(globals()['poolname'])
        l = []
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;for i in {1..1024};do find 1234test$i/  -type f |wc -l;done|uniq|wc -l" % (
                globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__eq__("1024"):
                ll = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd("" % ( globals()['poolname']))
        assert str(result).__eq__("20480"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 20480, int(tt[0][1])
        assert int(tt[1][1]) == 20480, int(tt[1][1])
        assert int(tt[2][1]) == 20480, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_setdcache_BeforeSetQuota_AfterRenameDirThenOpenDcache(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..1024};do mkdir test$i;done" % (
                globals()['poolname']))
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..1024};do for x in {1..20};do dd if=/dev/zero of=test$i/test$x bs=1M count=1  status=none;done;done" % (
            globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert result.__eq__("20480"), result
        execmdbk("cd /exports/%s/group/user;for i in {1..1024};do rename test$i   1234test$i   test$i   ;done" % (
            globals()['poolname']))
        time.sleep(5)
        setDcacheOn(globals()['poolname'])
        l = []
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;for i in {1..1024};do find 1234test$i/  -type f |wc -l;done|uniq|wc -l" % (
                    globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__eq__("1024"):
                ll = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd("" % (globals()['poolname']))
        assert str(result).__eq__("20480"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 20480, int(tt[0][1])
        assert int(tt[1][1]) == 20480, int(tt[1][1])
        assert int(tt[2][1]) == 20480, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_setdcache_BeforeSetQuota_AfterRenameDirThenCloseDcache(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..1024};do mkdir test$i;done" % (
                globals()['poolname']))
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..1024};do for x in {1..20};do dd if=/dev/zero of=test$i/test$x bs=1M count=1  status=none;done;done" % (
            globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert result.__eq__("20480"), result
        execmdbk("cd /exports/%s/group/user;for i in {1..1024};do rename test$i   1234test$i   test$i   ;done" % (
            globals()['poolname']))
        time.sleep(5)
        setDcacheOff(globals()['poolname'])
        l = []
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;for i in {1..1024};do find 1234test$i/  -type f |wc -l;done|uniq|wc -l" % (
                    globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__eq__("1024"):
                ll = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd("" % (globals()['poolname']))
        assert str(result).__eq__("20480"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 20480, int(tt[0][1])
        assert int(tt[1][1]) == 20480, int(tt[1][1])
        assert int(tt[2][1]) == 20480, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_setdcache_BeforeSetQuota_AfterRenameDir(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..1024};do mkdir test$i;done" % (
                globals()['poolname']))
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..1024};do for x in {1..20};do dd if=/dev/zero of=test$i/test$x bs=1M count=1  status=none;done;done" % (
                globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert result.__eq__("20480"), result
        execmdbk("cd /exports/%s/group/user;for i in {1..1024};do rename test$i   1234test$i   test$i   ;done" % (
            globals()['poolname']))
        time.sleep(5)
        setDcacheOff(globals()['poolname'])
        l = []
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;for i in {1..1024};do find 1234test$i/  -type f |wc -l;done|uniq|wc -l" % (
                    globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__eq__("1024"):
                ll = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd("" % (globals()['poolname']))
        assert str(result).__eq__("20480"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 20480, int(tt[0][1])
        assert int(tt[1][1]) == 20480, int(tt[1][1])
        assert int(tt[2][1]) == 20480, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_DoNotsetdcache_BeforeSetQuota_AfterRenameDir(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..1024};do mkdir test$i;done" % (
                globals()['poolname']))
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..1024};do for x in {1..20};do dd if=/dev/zero of=test$i/test$x bs=1M count=1  status=none;done;done" % (
                globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert result.__eq__("20480"), result
        execmdbk("cd /exports/%s/group/user;for i in {1..1024};do rename test$i   1234test$i   test$i   ;done" % (
            globals()['poolname']))
        time.sleep(5)
        l = []
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;for i in {1..1024};do find 1234test$i/  -type f |wc -l;done|uniq|wc -l" % (
                    globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__eq__("1024"):
                ll = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert str(result).__eq__("20480"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 20480, int(tt[0][1])
        assert int(tt[1][1]) == 20480, int(tt[1][1])
        assert int(tt[2][1]) == 20480, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result




    def test_amefs_setdcache_BeforeSetQuota_AfterRenameFileThenOpenDcache(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user; for x in {1..10240};do dd if=/dev/zero of=test$x bs=1M count=1  status=none;done" % (
            globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert result.__eq__("10240"), result
        execmdbk("cd /exports/%s/group/user;for i in {1..10240};do rename test$i   1234test$i   test$i   ;done" % (
            globals()['poolname']))
        time.sleep(5)
        setDcacheOn(globals()['poolname'])
        l = []
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;ls -al |grep  1234test|uniq|wc -l" % (globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__contains__("10240"):
                ll = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert str(result).__eq__("10240"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 10240, int(tt[0][1])
        assert int(tt[1][1]) == 10240, int(tt[1][1])
        assert int(tt[2][1]) == 10240, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result


    def test_amefs_setdcache_BeforeSetQuota_AfterRenameFileThenCloseDcache(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user; for x in {1..10240};do dd if=/dev/zero of=test$x bs=1M count=1  status=none;done" % (
                globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert result.__eq__("10240"), result
        execmdbk("cd /exports/%s/group/user;for i in {1..10240};do rename test$i   1234test$i   test$i   ;done" % (
            globals()['poolname']))
        time.sleep(5)
        setDcacheOff(globals()['poolname'])
        l = []
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;ls  -al |grep  1234test|uniq|wc -l" % (
                    globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__eq__("10240"):
                ll = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert str(result).__eq__("10240"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 10240, int(tt[0][1])
        assert int(tt[1][1]) == 10240, int(tt[1][1])
        assert int(tt[2][1]) == 10240, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_setdcache_BeforeSetQuota_AfterRenameFile(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user; for x in {1..10240};do dd if=/dev/zero of=test$x bs=1M count=1  status=none;done" % (
                globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert result.__eq__("10240"), result
        execmdbk("cd /exports/%s/group/user;for i in {1..10240};do rename test$i   1234test$i   test$i   ;done" % (
            globals()['poolname']))
        time.sleep(5)
        l = []
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;ls  -al |grep  1234test|uniq|wc -l" % (
                    globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__contains__("10240"):
                ll = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert str(result).__eq__("10240"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 10240, int(tt[0][1])
        assert int(tt[1][1]) == 10240, int(tt[1][1])
        assert int(tt[2][1]) == 10240, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result





    def test_amefs_DoNotsetdcache_BeforeSetQuota_AfterRenameFile(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user; for x in {1..10240};do dd if=/dev/zero of=test$x bs=1M count=1  status=none;done" % (
                globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert result.__eq__("10240"), result
        execmdbk("cd /exports/%s/group/user;for i in {1..10240};do rename test$i   1234test$i   test$i   ;done" % (
            globals()['poolname']))
        time.sleep(5)
        l = []
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;ls  -al |grep  1234test|uniq|wc -l" % (
                    globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__contains__("10240"):
                ll = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert str(result).__eq__("10240"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 10240, int(tt[0][1])
        assert int(tt[1][1]) == 10240, int(tt[1][1])
        assert int(tt[2][1]) == 10240, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result




    def test_amefs_set_dcache_Expansion_rebalancing_deletefile(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))

        setDcacheOn(globals()['poolname'])

        setQuota(globals()['poolname'], "1TB")

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
        assert result.__eq__("6"), result
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
        assert result.__eq__("0"), result
        result = execmd("/usr/local/amefs/sbin/ame  lvg   status  %s|grep  mnt|awk  '{ print $5}'|wc -l" % (globals()['poolname']))
        assert result.__eq__("6"), result
        tt=AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) + int(tt[3][1]) == 0, int(tt[0][1]) + int(tt[3][1])
        assert int(tt[1][1]) + int(tt[4][1]) == 0, int(tt[1][1]) + int(tt[4][1])
        assert int(tt[2][1]) + int(tt[5][1]) == 0, int(tt[2][1]) + int(tt[5][1])



    def test_amefs_set_dcache_Expansion_AfterRebalance_EnablDcache_DeleteFile_ContinueRe(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
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
            "/usr/local/amefs/sbin/ame  lvg  quota  %s   list|grep  /|awk   '{print $1\",\"$2\",\"$3\",\"$4\",\"$5}'" % (
                globals()['poolname']))
        print(result)
        result = execmd(
            "/usr/local/amefs/sbin/ame  lvg  rebalance  %s start" % (
                globals()['poolname']))

        #time.sleep(5)
        setDcacheOn(globals()['poolname'])

        time.sleep(60)
        result = execmd(
            "/usr/local/amefs/sbin/ame  lvg  rebalance  %s stop " % (
                globals()['poolname']))

        result = execmd("rm  -rf  /exports/%s/group/user/*" % (globals()['poolname']))

        result = execmd(
            "/usr/local/amefs/sbin/ame  lvg  rebalance  %s start" % (
                globals()['poolname']))

        time.sleep(5)

        for i in range(1800):
            print result
            result = execmd(
                "/usr/local/amefs/sbin/ame  lvg  rebalance  %s status " % (
                    globals()['poolname']))
            if result.__contains__("in progress"):
                time.sleep(5)
            else:
                break


        result = execmd("ls /exports/%s/group/user/|wc  -l" % (globals()['poolname']))
        assert result.__eq__("0"), result
        result = execmd("/usr/local/amefs/sbin/ame  lvg   status  %s|grep  mnt|awk  '{ print $5}'|wc -l" % (globals()['poolname']))
        assert result.__eq__("6"), result

        tt=AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) + int(tt[3][1]) == 0, int(tt[0][1]) + int(tt[3][1])
        assert int(tt[1][1]) + int(tt[4][1]) == 0, int(tt[1][1]) + int(tt[4][1])
        assert int(tt[2][1]) + int(tt[5][1]) == 0, int(tt[2][1]) + int(tt[5][1])

    def test_amefs_DoNotsetdcache_BeforeSetQuota_AfterMvDir(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))

        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..1024};do mkdir test$i;done" % (
                globals()['poolname']))
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..1024};do for x in {1..20};do dd if=/dev/zero of=test$i/test$x bs=1M count=1  status=none;done;done" % (
            globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert result.__eq__("20480"), result
        execmdbk("cd /exports/%s/group/user;for i in {1..1024};do mv  test$i   1234test$i;done" % (
            globals()['poolname']))
        time.sleep(5)
        l = []
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;for i in {1..1024};do find 1234test$i/  -type f |wc -l;done|uniq|wc -l" % (
                    globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__eq__("1024"):
                ll = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd("" % (globals()['poolname']))
        assert str(result).__eq__("20480"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 102400, int(tt[0][1])
        assert int(tt[1][1]) == 102400, int(tt[1][1])
        assert int(tt[2][1]) == 102400, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result

    def test_amefs_setdcache_BeforeSetQuota_AfterMvDir(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..1024};do mkdir test$i;done" % (
                globals()['poolname']))
        result = execmd(
            "cd /exports/%s/group/user;for i in {1..1024};do for x in {1..20};do dd if=/dev/zero of=test$i/test$x bs=1M count=1  status=none;done;done" % (
            globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert result.__eq__("20480"), result
        execmdbk("cd /exports/%s/group/user;for i in {1..1024};do mv  test$i   1234test$i;done" % (
            globals()['poolname']))
        time.sleep(5)
        l = []
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;for i in {1..1024};do find 1234test$i/  -type f |wc -l;done|uniq|wc -l" % (
                    globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__eq__("1024"):
                ll = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd("" % (globals()['poolname']))
        assert str(result).__eq__("20480"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 102400, int(tt[0][1])
        assert int(tt[1][1]) == 102400, int(tt[1][1])
        assert int(tt[2][1]) == 102400, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result



    def test_amefs_setdcache_aftersetquotaEnable_DelFileThenOpenDcache(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))

        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;for x in {1..10240};do dd if=/dev/zero of=test$x bs=1M count=1  status=none;done" % (globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert result.__eq__("10240"), result
        execmdbk("cd /exports/%s/group/user;rm  -rf  *" % (
            globals()['poolname']))
        time.sleep(5)
        setDcacheOn(globals()['poolname'])
        l = []
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;find .  -type f |wc -l" % (
                    globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__eq__("10240"):
                ll = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd(
            "cd /exports/%s/group/user;find .  -type f |wc -l" % (
                globals()['poolname']))
        assert str(result).__eq__("0"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 0, int(tt[0][1])
        assert int(tt[1][1]) == 0, int(tt[1][1])
        assert int(tt[2][1]) == 0, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result


    def test_amefs_setdcache_aftersetquotaEnable_DelFileInDirThenOpenDcache(self):
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (
                globals()['poolname']))
        result = execmd(
            "cd  /exports/%s/;mkdir group;cd group;mkdir user" % (
                globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd(
            "cd /exports/%s/group;ls " % (
                globals()['poolname']))
        assert result.__contains__("user"), result
        result = execmd(
            "cd /exports/%s/group/user;mkdir test;for x in {1..10240};do dd if=/dev/zero of=test/test$x bs=1M count=1  status=none;done" % (globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user  -type f |wc -l" % (
                globals()['poolname']))
        assert result.__eq__("10240"), result
        execmdbk("cd /exports/%s/group/user;rm  -rf  *" % (
            globals()['poolname']))
        time.sleep(5)
        setDcacheOn(globals()['poolname'])
        l = []
        for i in range(1200):
            result = execmd(
                "cd /exports/%s/group/user;find .  -type f |wc -l" % (
                    globals()['poolname']))
            print "等待中。。。:%s" % result
            if not result.__eq__("0"):
                ll = l.__len__()
                l.append(result)
                l = list(set(l))
                if l.__len__() == ll:
                    result1 = execmd("ps -ef|grep  'mv  test'|grep 1234|grep -v 'ps -ef'|wc -l")
                    if result1.__eq__("0"):
                        assert False
                time.sleep(3)
            else:
                break
        result = execmd(
            "cd /exports/%s/group/user;find .  -type f |wc -l" % (
                globals()['poolname']))
        assert str(result).__eq__("0"), result
        tt = AmefsApi.checktest(globals()['poolname'])
        assert int(tt[0][1]) == 0, int(tt[0][1])
        assert int(tt[1][1]) == 0, int(tt[1][1])
        assert int(tt[2][1]) == 0, int(tt[2][1])
        result = execmd(
            "rm -rf  /exports/%s/group/user/*" % (
                globals()['poolname']))
        result = execmd(
            "ls /exports/%s/group/user/|wc  -l" % (
                globals()['poolname']))
        assert result.__eq__("0"), result


    def test_amefs_setdcache_AfterMkgroup(self):
        result = execmd("cd  /exports/%s/;mkdir group;cd group;mkdir user" % (globals()['poolname']))
        setDcacheOn(globals()['poolname'])
        result = execmd("/usr/local/amefs/sbin/ame lvg  quota  %s  enable" % (globals()['poolname']))
        setQuota(globals()['poolname'], "1TB")
        result = execmd("cd /exports/%s/group;ls " % (globals()['poolname']))
        assert result.__eq__("user"), result
        result = execmd("rm   -rf /exports/%s/group/user/*" % (globals()['poolname']))
        result = execmd(
            "find /exports/%s/group/user/  -type f |wc -l" % (globals()['poolname']))
        assert result.__eq__("0"), result



if __name__ == "__main__":
    os.path.join(os.getcwd(),"testcase_dir")
    runner=unittest.TextTestRunner()
    testunit = unittest.TestSuite()
    testunit.addTests(unittest.TestLoader().loadTestsFromTestCase(TestfileStorageDcache))
    runner.run(testunit)
