# -*- coding: utf-8-*-
import os
import unittest
import configparser
import uuid
import md5sum
import _libssh  as dll
import random
import json
import time
global globpath

globpath = ""
configpath="C:\\Users\\pandesong\\Desktop\\ameds_test\\ameds_testcase.conf"





def  execmd(cmd):
    print "执行指令:%s".decode("utf-8")  %  cmd
    rest = dll.ssh_exec(str(cmd))
    assert rest == 0
    result = dll.p_get_exec_result(0).strip().strip('\r').strip('\n')
    return result


def uploadfiles(path, nfs, remote_file_path,  dir1,units,ip):
    tmp = []
    upload_bytes=0
    global globpath
    try:
        fils = os.listdir(path)
    except Exception as e:
        print str(e)
        return []
    for file in fils:
        num = 0
        path1 = os.path.join(path, file)
        if os.path.isdir(path1):
            pos = path1.rfind("\\")
            dir = path1[pos + 1:len(path1)]
            c=nfs.mkdirex(dir)
            nfs.chdirdir(dir)
            dir2 = dir1 + dir + "/"
            upload_bytes=upload_bytes+uploadfiles(path1, nfs, remote_file_path + "//" + dir,  dir2,units,ip)
            nfs.chdirdir("..")
            globpath = globpath + dir + "/"
        else:
            pos = path1.rfind("\\")
            remote = path1[pos + 1:len(path1)].decode("gbk",'ignore').encode("UTF-8")
            remote=str(remote)
            a = nfs.uploadex(path1,remote)
            if a < 0:
                print "upload False faild %s %d  %s %s" % (file.decode("gbk",'ignore').encode("UTF-8"), a,remote_file_path,ip)
                continue
            else:
                upload_bytes=upload_bytes+a
            cmd = "md5sum  \"%s/%s\"" % (remote_file_path, remote)
            dst_md5 = ""
            dst_md5 = execmd(cmd)
            for unit in str(units).split("\n"):
                unit1 = ("%s/%s/%s/" + dir1 + remote) % (unit, globals()['groupname'], globals()['username'])
                rest = execmd(
                    "ls  \"%s\" 2>/dev/null|wc -l" % (
                        unit1
                    ))
                try:
                    num = num+int(rest)
                except:
                    print "exec error %s" % rest

            src_md5 = ""
            try:
                src_md5 = md5sum.get_file_md5(path1).decode("gbk",'igore').encode("UTF-8")
            except Exception as e:
                print str(e)
            assert "md5 值不相等：%s %s" %(file,dst_md5),dst_md5.find(src_md5) >= 0
            #assert int(num) ==1
    return upload_bytes

def nfs_downloadex(path, nfs, remote_file_path):
    nfs.nfs_download(remote_file_path,"F:\\AutoTestData\\download")


def rmfiles(path, nfs, remote_file_path, dir1):
    tmp = []
    try:
        fils = os.listdir(path)
    except:
        return []
    for file in fils:
        nfs.chdirdir(path)
        path1 = os.path.join(path, file)
        if os.path.isdir(path1):
            pos = path1.rfind("\\")
            dir = path1[pos + 1:len(path1)]
            nfs.chdirdir(dir)
            dir2 = dir1 + dir + "//"
            rmfiles(path1, nfs, remote_file_path,dir2)
            nfs.chdirdir("..")
            nfs.rmdirex(dir)
        else:
            pos = path1.rfind("\\")
            remote = path1[pos + 1:len(path1)]
            if nfs.rmfileex(remote) < 0:
                print "rm file faild %s" % path1
                #fa.write("rm file faild %s\n" % path1);
                #fa.flush()
                continue
            unit1 = ("/mnt/zp-sdj/%s/%s/%s/" + dir1 + remote) % (globals()['poolname'],globals()['groupname'], globals()['username'])
            unit2 = ("/mnt/zp-sdb/%s/%s/%s/" + dir1 + remote) % (globals()['poolname'],globals()['groupname'], globals()['username'])
            rest = execmd(
                "b=`ls  %s 2>/dev/null |wc -l&&ls  %s 2>/dev/null|wc -l`&&echo $b|tr ' '  '+'|xargs echo |bc" % (
                unit1, unit2))
            num = rest.strip("\n").strip("\r").decode("utf-8").encode("gbk")
            assert int(num) == 0
    return tmp

def  is_json_format(json1):
    import re
    json1=json1.decode("utf-8")
    if json1=="" or json1==None:
        json_tt = "{\"ret\":\"NOOK\",\"error\":\"respose is null\"}"
        return json.loads(json_tt,strict=False)
    if json1.find("Warning: The unit file")>=0:
        json1=re.sub("Warning:(.*)reload units(.*)",'',json1)
    json_object=""
    try:
        json_object = json.loads(json1,strict=False)
    except Exception as e:
        json_tt="{\"ret\":\"NOOK\",\"error\":\" Exception:\"}"
        print str(e)
        print json1
        json_object = json.loads(json_tt)
    return json_object

def getallfiles(path):
    tmp = []
    try:
        fils = os.listdir(path)
    except:
        return []
    for file in fils:
        path1 = os.path.join(path, file)
        if os.path.isdir(path1):
            tmp.extend(getallfiles(path1))
        else:
            tmp.append(path1)
    return tmp

def get_config():
    config = configparser.ConfigParser()
    config.read(configpath, encoding="utf-8")
    global ip
    global port
    global user
    global password
    global config_json
    global ldap_server
    global ldap_pwd
    global  ldap_user_dn
    global ldap_base_dn
    ip = config["base"]["ip"]
    port = config["base"]["port"]
    user = config["base"]["user"]
    password = config["base"]["password"]
    config_json = config["base"]["configjson"]
    ldap_server = config["base"]["ldap_server"]
    ldap_pwd = config["base"]["ldap_pwd"]
    ldap_user_dn = config["base"]["ldap_user_dn"].replace("\"","")
    ldap_base_dn = config["base"]["ldap_base_dn"].replace("\"","")

def one_host(unit):
    l=[]
    unitnumber = unit
    for m in range(1,unitnumber+1):
        for n in range(1,unitnumber+1):
                if   m/2 > n and m>2:
                    l.append(("%d %d") %  (m,n))
    return l

def create_pool_disperse(ip1, port, user, password):
    l=[]
    session = dll.ssh_login_by_password(str(ip1), int(port), str(user), str(password))
    assert session == 0
    hostname = execmd("hostname")
    result=execmd("df  2>/dev/null|grep mnt|awk  '{ print $6}'")
    units=str(result).strip('\r').split('\n')
    uu=one_host(len(units))
    for i in uu:
        checkblock=i.split(' ')[1]
        disperse=i.split(' ')[0]
        unit=random.sample(units,int(disperse))
        create="disperse %s redundancy %s"  %  (disperse,checkblock)
        name="jsm"+checkblock+disperse
        storage = ("/jsmname%s:" % hostname).join(unit)
        storage = (" %s:%s" % (hostname,storage)+"/jsmname")
        storage=storage.replace("jsmname",name+" ")
        result=execmd("echo  'y'|/usr/local/amefs/sbin/ame lvg  create %s %s %s force" % (name,create,storage))
        assert result.contain("lvgroup create: %s: success: please start the lvgroup to access data" % name) or result.contain(" already exists"),result
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg   start  %s " % name)
        assert str(result).contain("success") or result.contain("already started") ,result
        l.append(name)
        break
    dll.ssh_close()
    return l


class TestblockStorage(unittest.TestCase):
    def __init__(self,*args,**kwargs):
        super(TestblockStorage,self).__init__(*args,**kwargs)

    @classmethod
    def setUpClass(self):
        get_config()
        global ip
        global port
        global user
        global password
        global config_json
        global ldap_server
        global ldap_pwd
        globals()['pools']=create_pool_disperse(ip, port, user, password)
        session = dll.ssh_login_by_password(str(ip), int(port), str(user), str(password))

        result = execmd("/usr/local/amefs/sbin/ame lvg   set  %s  performance.dcache  on " % (globals()['pools'][0]))
        assert session == 0


    @classmethod
    def tearDownClass(self):
        result=execmd("iscsiadm --mode node  -u")
        for pool in globals()['pools']:
            globals()['poolname']=pool
            result = execmd(
                "echo  'y'|/usr/local/amefs/sbin/ame lvg   stop  %s" % globals()['poolname'])
            result = execmd(
                "echo 'y'|/usr/local/amefs/sbin/ame lvg   delete  %s" % globals()['poolname'])
        execmd("ls /mnt/|xargs -n1 -i  rm -rf   /mnt/{}/jsm14")
        execmd("rm -rf /exports/jsm14")
        dll.ssh_close()


    def test_ames_add_iqn(self):
        globals()['iqnname']="iqn"+str(int(time.time()))
        result=execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt add-iqn  %s" % globals()['iqnname'])
        a =is_json_format(result)
        self.assertTrue(a["ret"] == "OK",a)


    def test_ames_add_same_iqn(self):
        globals()['iqnname_1']="iqn"+str(int(time.time()))
        result = execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt add-iqn  %s" % globals()['iqnname_1'])
        a = is_json_format(result)
        assert a["ret"] == "OK",result
        result = execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt add-iqn  %s" % globals()['iqnname_1'])
        a = is_json_format(result)
        assert a["ret"] == "NOK",result
        assert result.contain("this target already exists")
        result=execmd("grep  -ari   %s /etc/tgt/conf.d/*|awk   -F  ':'  '{ print $1}'|wc -l" % globals()['iqnname_1'])
        self.assertTrue(result=="1", result)
        result = execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt del-iqn   iqn.2021-10.com.%s:amefs" % globals()['iqnname_1'])
        a = is_json_format(result)
        assert a["ret"] == "OK",result
        result=execmd("grep  -ari   %s /etc/tgt/conf.d/*|awk   -F  ':'  '{ print $1}'|wc -l" % globals()['iqnname_1'])
        assert result=="0"


    def test_ames_get_iqnlist(self):
        result = execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt list-iqn")
        a =is_json_format(result)
        globals()['iqnid']=""
        assert a["ret"]=="OK",result
        assert result.contain(globals()['iqnname'])
        flag=False
        for i in a["data"]:
            if str(i.values()[0]).contain(globals()['iqnname']):
                globals()['iqnname']=i.values()[0]
                globals()['iqnid']=i.keys()[0]
                print globals()['iqnid']
                flag=True
        assert  flag


    def test_ames_unbind_all(self):
        result = execmd("tgt-admin   -s")
        flag=False
        for i in str(result).split("Target "):
            if i.contain(globals()['iqnname']):
                flag=True
                assert  len(i.split("ACL information:"))>0
                self.assertTrue(not i.split("ACL information:")[1].contain("ALL"),msg=i)
        assert  flag==True
        result = execmd("systemctl  restart tgtd")
        result = execmd("tgt-admin   -s")
        flag=False
        for i in str(result).split("Target "):
            if i.contain(globals()['iqnname']):
                flag=True
                assert  len(i.split("ACL information:"))>1
                assert  i.split("ACL information:")[1].contain("ALL")
        assert  flag
        result = execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt unbind-all   %s" % globals()['iqnname'])
        a = is_json_format(result)
        assert a["ret"] == "OK",result
        flag = False
        result = execmd("tgt-admin   -s")
        for i in str(result).split("Target "):
            if i.contain(globals()['iqnname']):
                flag = True
                print i
                assert  len(i.split("ACL information:")) > 1
                self.assertTrue(not i.split("ACL information:")[1].contain("ALL"),msg=i)
        self.assertTrue(flag,msg=result)

    def test_ames_bind_ip_single(self):
        ip_test=execmd("cardname=`cat %s|grep  'P_IP_INTF'|awk -F  ','  '{ print $1}'|awk   -F  ':'   '{ print $3 }'`;card=`echo  $cardname|sed  's/\"//g'`;ifconfig  $card |grep  'mask'|awk  '{ print $2}'" % config_json)
        globals()["ip"]=ip_test
        result=execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt list-iqn")
        a= is_json_format(result)
        assert a["ret"] == "OK",result
        assert result.find(globals()['iqnname'])>=0,("%s , %s ") % (result,globals()['iqnname'])

        globals()["iqn"]=result.strip(":").strip("\"")
        result = execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt bind-ip '%s' '%s'" % (globals()["iqnname"],ip_test))
        a= is_json_format(result)
        assert a["ret"] == "OK",result
        result=execmd("tgt-admin  -s")
        targetlist=str(result).split("Target ")
        targetlist.remove('')
        find=False
        for i in  targetlist:
            if i.contain(globals()['iqnname']):
                find=True
                assert i,i.contain(ip_test)
        assert find





    def test_ames_bind_ip_Multiple(self):
        iplist=["127.0.0.1","127.0.0.2","127.0.0.3","127.0.0.4","127.0.0.5"]
        result = execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt bind-ip '%s' '%s'" % (globals()["iqnname"], ",".join(iplist)))
        a = is_json_format(result)
        assert a["ret"] == "OK"
        result = execmd("tgt-admin  -s")
        targetlist = str(result).split("Target ")
        targetlist.remove('')
        find = False
        for i in targetlist:
            if i.contain(globals()['iqnname']):
                find = True
                for iptmp in iplist:
                    self.assertTrue(i.contain(iptmp),msg=i)
        assert find


    def test_ames_unbind_ip_Multiple(self):
        iplist = ["127.0.0.1", "127.0.0.2", "127.0.0.3", "127.0.0.4", "127.0.0.5"]
        result = execmd(
            "/usr/local/ames/ames_cfg.sh SET ame-tgt unbind-ip '%s' '%s'" % (globals()["iqnname"], ",".join(iplist)))
        a = is_json_format(result)
        assert a["ret"] == "OK"
        result = execmd("tgt-admin  -s")
        targetlist = str(result).split("Target ")
        targetlist.remove('')
        find = False
        for i in targetlist:
            if i.contain(globals()['iqnname']):
                find = True
                for iptmp in iplist:
                    assert  not i.contain(iptmp),i
        assert find,i



    def test_ames_bind_user(self):
        globals()["username"]="username"+str((int)(time.time()))
        globals()["passwd"]="Zjcc@123"
        result=execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt bind-user %s %s %s" % (globals()["iqnname"],globals()["username"],globals()["passwd"]))
        a =is_json_format(result)
        assert isinstance(a,dict),a
        assert a["ret"] == "OK",result
        result=execmd("grep  -l   %s /etc/tgt/conf.d/*|xargs  -n1  -i  cat {}" % globals()["iqnname"])
        print result
        assert result.contain(globals()["username"])>=0 and result.find(globals()["passwd"])
        result=execmd("iscsiadm --mode discoverydb --type sendtargets --portal %s  --discover 2>&1|grep %s" % (globals()["ip"],globals()['iqnname']))
        assert len(result)>0,result
        try:
            targetname=result.split(" ")[1].strip()
            print [targetname]
            result=execmd("iscsiadm --mode node --targetname %s -o update -n node.session.auth.password -v %s -n node.session.auth.username -v  %s -n node.session.auth.authmethod -v CHAP" % (targetname,globals()["passwd"],globals()["username"]))
            result=execmd("iscsiadm --mode node --targetname  %s --portal  %s  -l"   %  (targetname,globals()["ip"]))
            print("iscsiadm --mode node --targetname  %s --portal  %s  -l"   %  (targetname,globals()["ip"]))
            assert result,result.contain("successful")
            result=execmd("iscsiadm -m session -P 0|grep  %s" % targetname)
            print result
            assert  result.contain(targetname)
            result = execmd(" iscsiadm --mode node  -u" )
            assert  result.contain("successful")
            result = execmd(
                "iscsiadm --mode node --targetname %s -o update -n node.session.auth.password -v %s -n node.session.auth.username -v  %s -n node.session.auth.authmethod -v CHAP" % (
                targetname, "dddd", globals()["username"]))
            result = execmd("iscsiadm --mode node --targetname  %s --portal  %s  -l" % (targetname, globals()["ip"]))
            assert result.contain("fail")
        except Exception as e:
            print e
            assert 1==2


    def test_ames_create_lun_streamline(self):
        globals()['poolname'] = str(uuid.uuid4())
        hostname = execmd("hostname")
        units = execmd("lsblk  -l|grep  mnt|awk   '{ print $7}'")
        unit = units.split("\n")[0]
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg    create   %s   %s:%s/%s/" % (
            globals()['poolname'], hostname, unit, globals()['poolname']))
        assert ("lvgroup create: %s: success: please start the lvgroup to access data" % globals()[
            'poolname']) == result
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg   start  %s " % globals()['poolname'])
        assert str(result).contain("success")
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg   info %s |grep  Status|awk  '{ print $2}'" % globals()['poolname'])
        assert result == "Started"
        luns=[]
        for pool in globals()['pools']:
            globals()['poolname'] = pool
            globals()['lunname']="lun"+str(int(time.time()))
            luns.append(globals()['lunname'])
            result=execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt add-lun %s %s %s %s" % (globals()['iqnname'],globals()['poolname'],globals()['lunname'],1024))
            a =is_json_format(result)
            assert  a["ret"] == "OK",result
            result = execmd("cat  /etc/tgt/conf.d/tgt%s.conf" % globals()['iqnid'])
            #parser = xml.sax.make_parser()
            #parser.setFeature(xml.sax.handler.feature_namespaces, 0)
            #Handler = tgtconfig()
            #parser.setContentHandler(Handler)
            #xml.sax.parse(result)
            if result.contain("backing-store"):
                assert True
            else:assert result,False
            if result.contain(globals()['lunname']):
                assert True
            else:assert result,False
            result=execmd("iscsiadm --mode discoverydb --type sendtargets --portal  %s  --discover 2>&1 |grep %s" % (globals()["ip"],globals()['iqnname']))
            try:
                targetname=result.split(" ")[1].strip()
                print [targetname]
                result = execmd(
                    "iscsiadm --mode node --targetname %s -o update -n node.session.auth.password -v %s -n node.session.auth.username -v  %s -n node.session.auth.authmethod -v CHAP" % (
                    targetname, globals()["passwd"], globals()["username"]))
                result=execmd("iscsiadm --mode node --targetname  %s --portal  %s  -l"   %  (targetname,globals()["ip"]))
                assert  result.contain("success")
                result=execmd("iscsiadm -m session -P  3" )
                flag=False
                for i in result.split("Target:"):
                    i=i.replace("\t"," ")
                    if i.find(globals()['iqnname'])>=0:
                        flag=True
                        t=i.split("Attached scsi disk ")
                        assert  len(t)>1
                        assert  len(t[1].split(" "))>1
                        disk=t[1].split(" ")[0]
                        result=execmd("mkfs.xfs  -f /dev/%s" % disk)
                        print "mkfs.xfs  result:%s" % result
                        dir="pdstest"+str(int(time.time()))
                        result=execmd("mkdir -p /opt/%s;mount  /dev/%s /opt/%s" % (dir,disk,dir))
                        print result
                        result=execmd("df /opt/%s|grep /dev/%s|wc -l" % (dir,disk))
                        assert  result=="1"
                        result=execmd("dd if=/dev/zero bs=1024 count=1000576 of=/opt/%s/test" % dir)
                        result = execmd("ls -s /opt/%s/test|awk  '{print $1}'" % dir)
                        assert  result.contain("1000576"),result
                        result = execmd("umount /opt/%s" % (dir))
                        result = execmd("iscsiadm --mode node --targetname  %s  --portal %s  -u" % (globals()['iqnname'], globals()['ip']))
                assert flag,result

            except Exception as e:
                print e
                assert 1==2
        globals()['luns']=luns





    def test_ames_create_snapshot_streamline(self):
        luns=[]
        for pool in globals()['pools']:
            snapname="snap"+pool
            result=execmd("/usr/local/amefs/sbin/ame   snapshot   create     %s   %s no-timestamp" % (snapname,pool))
            result=execmd("/usr/local/amefs/sbin/ame   snapshot  activate  %s " % (snapname))
            print result
            clonename="clone"+pool
            result =execmd("/usr/local/amefs/sbin/ame   snapshot  clone %s   %s " % (clonename,snapname))
            print result
            result = execmd("echo y|/usr/local/amefs/sbin/ame   lvg delete %s " % (clonename))
            print result
            result = execmd("echo y|/usr/local/amefs/sbin/ame   snapshot delete  snapjsm14")
            print result

    def test_ames_get_tgt_detail(self):
        result = execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt tgt-status %s" % globals()['iqnname'])
        a = is_json_format(result)
        assert  a["ret"] == "OK",result
        flag=False
        lun_flag=False
        for  i in a["data"]:
            targetname=i["target"]
            if i.has_key("luns"):
                for lun in i["luns"]:
                    if str(lun["backing-store"]).contain(globals()['lunname']):
                        lun_flag=True
                        self.assertTrue(str(lun["size"]).contain("1000576") or str(lun["size"]).contain("1074MB"),msg=result)
            if globals()['iqnname']==targetname:
                flag=True
        assert  flag and lun_flag,result


    def test_ames_create_resizelun_streamline(self):
        lun=0;
        print globals()['luns']
        for pool in globals()['pools']:
            globals()['poolname']=pool
            globals()['lunname']=globals()['luns'][lun]
            result=execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt resize-lun %s %s %s" % (globals()['poolname'],globals()['lunname'],2048))
            a = is_json_format(result)
            assert a["ret"] == "OK",result
            print globals()['iqnid']
            result = execmd("cat  /etc/tgt/conf.d/tgt%s.conf" % globals()['iqnid'])
            if result.contain("backing-store"):
                assert True
            else:
                print result
                assert  False
            if result.contain(globals()['lunname']):
                assert True
            else:
                print result
                assert  False
            result=execmd("iscsiadm --mode discoverydb --type sendtargets --portal  %s  --discover 2>&1 |grep %s" % (globals()["ip"],globals()['iqnname']))
            targetname=result.split(" ")[1].strip()
            print [targetname]
            result = execmd(
                "iscsiadm --mode node --targetname %s -o update -n node.session.auth.password -v %s -n node.session.auth.username -v  %s -n node.session.auth.authmethod -v CHAP" % (
                targetname, globals()["passwd"], globals()["username"]))
            result=execmd("iscsiadm --mode node --targetname  %s --portal  %s  -l"   %  (targetname,globals()["ip"]))
            assert result.__contains__("success"),result
            result=execmd("iscsiadm -m session -P  3" )
            print result
            flag=False
            for i in result.split("Target:"):
                i=i.replace("\t"," ")
                if i.contain(globals()['iqnname']):
                    flag=True
                    t=i.split("Attached scsi disk ")
                    assert  len(t)>1
                    assert  len(t[1].split(" "))>1
                    print t[1].split(" ")
                    disk=t[1].split(" ")[0]
                    result=execmd("mkfs.xfs  -f /dev/%s" % disk)
                    print "mkfs.xfs  result:%s" % result
                    dir="pdstest"+str(int(time.time()))
                    execmd("mkdir /opt/%s;mount  /dev/%s /opt/%s" % (dir,disk,dir))
                    result=execmd("df /opt/%s|grep /dev/%s|awk '{ print $2}'" % (dir,disk))
                    self.assertTrue(result=="2086912",msg=result)
                    result=execmd("dd if=/dev/zero bs=1024 count=1000576 of=/opt/%s/test" % dir)
                    result = execmd("ls -s /opt/%s/test|awk  '{print $1}'" % dir)
                    assert  result.contain("1000576")
            assert  flag
            result = execmd(
                "umount /opt/%s" % (dir))
            result=execmd(
                "iscsiadm --mode node --targetname  %s  --portal %s  -u" % (targetname,globals()['ip']))
            assert  result.contain("success")
            lun=lun+1

    def test_ames_disable_lun_streamline(self):
        lun=0
        for pool in globals()['pools']:
            globals()['poolname']=pool
            globals()['lunname'] = globals()['luns'][lun]
            result = execmd("/usr/local/ames/ames_cfg.sh  SET ame-tgt disable-lun %s %s %s" % (globals()["iqnname"],globals()['poolname'], globals()['lunname']))
            a = is_json_format(result)
            assert a["ret"] == "OK",result
            print globals()['iqnid']
            result = execmd("cat  /etc/tgt/conf.d/tgt%s.conf" % globals()['iqnid'])
            assert not result.contain(pool),result
            #assert not result.contain(globals()['lunname']),result
            lun=lun+1

    def test_ames_login_fail_streamline(self):
        result=execmd("iscsiadm --mode discoverydb --type sendtargets --portal  %s  --discover 2>&1 |grep %s" % (globals()["ip"],globals()['iqnname']))
        targetname=result.split(" ")[1].strip()
        print [targetname]
        result = execmd(
            "iscsiadm --mode node --targetname %s -o update -n node.session.auth.password -v %s -n node.session.auth.username -v  %s -n node.session.auth.authmethod -v CHAP" % (
            targetname, globals()["passwd"], globals()["username"]))
        result=execmd("iscsiadm --mode node --targetname  %s --portal  %s  -l"   %  (targetname,globals()["ip"]))
        assert result.contain("success")
        result=execmd("iscsiadm -m session -P  3" )
        flag=False
        for i in result.split("Target:"):
            i=i.replace("\t"," ")
            if i.contain(globals()['iqnname']):
                flag = True
                t = i.split("Attached scsi disk ")
                assert  len(t)<=1,i
        assert flag,False
        result=execmd(
            "iscsiadm --mode node --targetname  %s  --portal %s  -u" % (targetname,globals()['ip']))
        assert  result.contain("success")


    def test_ames_enable_lun_streamline(self):
        lun=0
        for pool in globals()['pools']:
            globals()['poolname']=pool
            globals()['lunname'] = globals()['luns'][lun]
            result = execmd("/usr/local/ames/ames_cfg.sh  SET ame-tgt enable-lun %s %s %s" % (globals()["iqnname"],globals()['poolname'], globals()['lunname']))
            a = is_json_format(result)
            assert a["ret"] == "OK",result
            print globals()['iqnid']
            result = execmd("cat  /etc/tgt/conf.d/tgt%s.conf" % globals()['iqnid'])
            assert  result.contain("backing-store"),result
            assert  result.contain(globals()['lunname']),result
            lun=lun+1

    def test_ames_login_success_streamline(self):
        result = execmd("iscsiadm --mode discoverydb --type sendtargets --portal  %s  --discover 2>&1 |grep %s" % (
        globals()["ip"], globals()['iqnname']))
        targetname = result.split(" ")[1].strip()
        print [targetname]
        result = execmd(
            "iscsiadm --mode node --targetname %s -o update -n node.session.auth.password -v %s -n node.session.auth.username -v  %s -n node.session.auth.authmethod -v CHAP" % (
                targetname, globals()["passwd"], globals()["username"]))
        result = execmd("iscsiadm --mode node --targetname  %s --portal  %s  -l" % (targetname, globals()["ip"]))
        assert result.contain("success"),result
        result = execmd("iscsiadm -m session -P  3")
        flag = False
        for i in result.split("Target:"):
            i = i.replace("\t", " ")
            if i.contain(globals()['iqnname']):
                flag = True
                t = i.split("Attached scsi disk ")
                assert len(t) > 1
                assert len(t[1].split(" ")) > 1
        assert flag,result
        result = execmd(
            "iscsiadm --mode node --targetname  %s  --portal %s  -u" % (targetname, globals()['ip']))
        assert result.contain("success")





    def test_ames_del_lun_streamline(self):
        lun=0
        for pool in globals()['pools']:
            globals()['poolname']=pool
            globals()['lunname'] = globals()['luns'][lun]
            result = execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt del-lun %s  %s" % (
                globals()["poolname"], globals()['lunname']))
            a = is_json_format(result)
            assert a["ret"] == "OK",result
            result=execmd("ls  /exports/%s/%s 2>/dev/null|wc -l" % (globals()['poolname'],globals()['lunname']))
            assert result=="0",result
            result = execmd("iscsiadm --mode node --targetname  %s --portal  %s  -l" % (globals()["iqnname"], globals()["ip"]))
            assert result.contain("success"),result
            result = execmd("iscsiadm -m session -P  3")
            flag = False
            for i in result.split("Target:"):
                i = i.replace("\t", " ")
                if i.contain(globals()['iqnname']):
                    flag = True
            assert flag, result
            result = execmd(
                "iscsiadm --mode node --targetname  %s  --portal %s  -u" % (globals()["iqnname"], globals()['ip']))
            assert result.contain("success"),result
            assert not result.contain("backing-store"), result
            assert not result.contain(globals()['lunname']), result
            lun=lun+1



    def test_ames_create_lun_fallocate(self):
        l=[]
        for pool in globals()['pools']:
            globals()['poolname']=pool
            globals()['lunname']="lun"+str(int(time.time()))
            l.append(globals()['lunname'])
            result=execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt add-lun %s %s %s %s fallocate" % (globals()['iqnname'],globals()['poolname'],globals()['lunname'],1024))
            a = is_json_format(result)
            assert a["ret"] == "OK",result
            result = execmd("cat  /etc/tgt/conf.d/tgt%s.conf" % globals()['iqnid'])
            if result.contain("backing-store"):
                assert True
            else:assert result,False
            if result.contain(globals()['lunname']):
                assert True
            else:assert result,False
            result=execmd("iscsiadm --mode discoverydb --type sendtargets --portal  %s  --discover 2>&1 |grep %s" % (globals()["ip"],globals()['iqnname']))
            targetname=result.split(" ")[1].strip()
            print [targetname]
            result = execmd(
                "iscsiadm --mode node --targetname %s -o update -n node.session.auth.password -v %s -n node.session.auth.username -v  %s -n node.session.auth.authmethod -v CHAP" % (
                targetname, globals()["passwd"], globals()["username"]))
            result=execmd("iscsiadm --mode node --targetname  %s --portal  %s  -l"   %  (targetname,globals()["ip"]))
            assert  result.contain("success"),result
            result=execmd("iscsiadm -m session -P  3" )
            flag=False
            for i in result.split("Target:"):
                i=i.replace("\t"," ")
                if i.find(globals()['iqnname'])>=0:
                    flag=True
                    t=i.split("Attached scsi disk ")
                    assert  len(t)>1
                    assert  len(t[1].split(" "))>1
                    disk=t[1].split(" ")[0]
                    result=execmd("mkfs.xfs  -f /dev/%s" % disk)
                    print "mkfs.xfs  result:%s" % result
                    dir="pdstest"+str(int(time.time()))
                    result=execmd("mkdir -p /opt/%s;mount  /dev/%s /opt/%s" % (dir,disk,dir))
                    print result
                    result=execmd("df /opt/%s|grep /dev/%s|wc -l" % (dir,disk))
                    assert  result=="1"
                    result=execmd("dd if=/dev/zero bs=1024 count=1000576 of=/opt/%s/test" % dir)
                    result = execmd("ls -s /opt/%s/test|awk  '{print $1}'" % dir)
                    assert  result.contain("1000576"),result
                    result = execmd("du -s /opt/%s/test|awk  '{print $1}'" % dir)
                    assert  result.contain("1000576"),result
            assert flag,result
            result = execmd(
                "umount /opt/%s" % (dir))
            result = execmd( "iscsiadm --mode node --targetname  %s  --portal %s  -u" % (globals()['iqnname'], globals()['ip']))
        globals()['luns']=l


    def test_ames_create_resizelun_fallocate(self):
        lun=0;
        for pool in globals()['pools']:
            globals()['poolname']=pool
            globals()['lunname']=globals()['luns'][lun]
            result=execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt resize-lun %s %s %s fallocate" % (globals()['poolname'],globals()['lunname'],2048))
            a = is_json_format(result)
            assert a["ret"] == "OK",result
            print globals()['iqnid']
            result = execmd("cat  /etc/tgt/conf.d/tgt%s.conf" % globals()['iqnid'])
            if result.contain("backing-store"):
                assert True
            else:
                print result
                assert  False
            if result.contain(globals()['lunname']):
                assert True
            else:
                print result
                assert  False
            result=execmd("iscsiadm --mode discoverydb --type sendtargets --portal  %s  --discover 2>&1 |grep %s" % (globals()["ip"],globals()['iqnname']))
            targetname=result.split(" ")[1].strip()
            print [targetname]
            result = execmd(
                "iscsiadm --mode node --targetname %s -o update -n node.session.auth.password -v %s -n node.session.auth.username -v  %s -n node.session.auth.authmethod -v CHAP" % (
                targetname, globals()["passwd"], globals()["username"]))
            result=execmd("iscsiadm --mode node --targetname  %s --portal  %s  -l"   %  (targetname,globals()["ip"]))
            assert result.contain("success")
            result=execmd("iscsiadm -m session -P  3" )
            flag=False
            for i in result.split("Target:"):
                i=i.replace("\t"," ")
                if i.contain(globals()['iqnname']):
                    flag=True
                    t=i.split("Attached scsi disk ")
                    assert  len(t)>1
                    assert  len(t[1].split(" "))>1
                    print t[1].split(" ")
                    disk=t[1].split(" ")[0]
                    result=execmd("mkfs.xfs  -f /dev/%s" % disk)
                    print "mkfs.xfs  result:%s" % result
                    dir="pdstest"+str(int(time.time()))
                    execmd("mkdir /opt/%s;mount  /dev/%s /opt/%s" % (dir,disk,dir))
                    result=execmd("df /opt/%s|grep /dev/%s|awk '{ print $2}'" % (dir,disk))
                    self.assertTrue(result=="2086912",msg=result)
                    result=execmd("dd if=/dev/zero bs=1024 count=1000576 of=/opt/%s/test" % dir)
                    result = execmd("ls -s /opt/%s/test|awk  '{print $1}'" % dir)
                    assert  result.contain("1000576")
                    result = execmd("du -s /opt/%s/test|awk  '{print $1}'" % dir)
                    assert result.contain("1000576")
            assert  flag
            result = execmd(
                "umount /opt/%s" % (dir))
            result=execmd(
                "iscsiadm --mode node --targetname  %s  --portal %s  -u" % (targetname,globals()['ip']))
            assert  result.contain("success")
            lun=lun+1
        self.test_ames_del_lun_streamline()

    def test_ames_create_lun_fallocate_kill_reduence(self):
        l=[]
        for pool in globals()['pools']:
            globals()['poolname']=pool
            result=execmd("/usr/local/amefs/sbin/ame lvg info   %s|grep  Units|grep =|awk   '{ print $8 }' | awk  -F   ')'  '{ print $1 } '" % pool)
            num=int(result.replace(" ",""))
            globals()['lunname']="lun"+str(int(time.time()))
            result=execmd("ps -ef|grep  %s.pid|grep  -v grep |awk  '{ print $2}'" % pool).strip('\r').split('\n')
            assert  len(result)!=0,result
            print num
            print result
            print pool
            pids = random.sample(result, num)
            execmd("kill -9 "+ " ".join(pids))
            l.append(globals()['lunname'])
            result=execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt add-lun %s %s %s %s fallocate" % (globals()['iqnname'],globals()['poolname'],globals()['lunname'],1024))
            a = is_json_format(result)
            assert a["ret"] == "OK",result
            result = execmd("cat  /etc/tgt/conf.d/tgt%s.conf" % globals()['iqnid'])
            if result.contain("backing-store"):
                assert True
            else:assert result,False
            if result.contain(globals()['lunname']):
                assert True
            else:assert result,False
            result=execmd("iscsiadm --mode discoverydb --type sendtargets --portal  %s  --discover 2>&1 |grep %s" % (globals()["ip"],globals()['iqnname']))
            targetname=result.split(" ")[1].strip()
            print [targetname]
            result = execmd(
                "iscsiadm --mode node --targetname %s -o update -n node.session.auth.password -v %s -n node.session.auth.username -v  %s -n node.session.auth.authmethod -v CHAP" % (
                targetname, globals()["passwd"], globals()["username"]))
            result=execmd("iscsiadm --mode node --targetname  %s --portal  %s  -l"   %  (targetname,globals()["ip"]))
            assert  result.contain("success"),result
            result=execmd("iscsiadm -m session -P  3" )
            flag=False
            for i in result.split("Target:"):
                i=i.replace("\t"," ")
                if i.find(globals()['iqnname'])>=0:
                    flag=True
                    t=i.split("Attached scsi disk ")
                    assert  len(t)>1
                    assert  len(t[1].split(" "))>1
                    disk=t[1].split(" ")[0]
                    result=execmd("mkfs.xfs  -f /dev/%s" % disk)
                    print "mkfs.xfs  result:%s" % result
                    dir="pdstest"+str(int(time.time()))
                    result=execmd("mkdir -p /opt/%s;mount  /dev/%s /opt/%s" % (dir,disk,dir))
                    print result
                    result=execmd("df /opt/%s|grep /dev/%s|wc -l" % (dir,disk))
                    assert  result=="1"
                    result=execmd("dd if=/dev/zero bs=1024 count=1000576 of=/opt/%s/test" % dir)
                    result = execmd("ls -s /opt/%s/test|awk  '{print $1}'" % dir)
                    assert  result.contain("1000576"),result
                    result = execmd("du -s /opt/%s/test|awk  '{print $1}'" % dir)
                    assert  result.contain("1000576"),result
            assert flag,result
            result = execmd(
                "umount /opt/%s" % (dir))
            result = execmd("iscsiadm --mode node --targetname  %s  --portal %s  -u" % (globals()['iqnname'], globals()['ip']))
        globals()['luns']=l

    def test_ames_create_resizelun_fallocate_kill(self):
        lun=0;
        for pool in globals()['pools']:
            globals()['poolname']=pool
            globals()['lunname']=globals()['luns'][lun]
            result=execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt resize-lun %s %s %s fallocate" % (globals()['poolname'],globals()['lunname'],2048))
            a = is_json_format(result)
            assert a["ret"] == "OK",result
            print globals()['iqnid']
            result = execmd("cat  /etc/tgt/conf.d/tgt%s.conf" % globals()['iqnid'])
            if result.contain("backing-store"):
                assert True
            else:
                print result
                assert  False
            if result.contain(globals()['lunname']):
                assert True
            else:
                print result
                assert  False
            result=execmd("iscsiadm --mode discoverydb --type sendtargets --portal  %s  --discover 2>&1 |grep %s" % (globals()["ip"],globals()['iqnname']))
            targetname=result.split(" ")[1].strip()
            print [targetname]
            result = execmd(
                "iscsiadm --mode node --targetname %s -o update -n node.session.auth.password -v %s -n node.session.auth.username -v  %s -n node.session.auth.authmethod -v CHAP" % (
                targetname, globals()["passwd"], globals()["username"]))
            result=execmd("iscsiadm --mode node --targetname  %s --portal  %s  -l"   %  (targetname,globals()["ip"]))
            assert result.contain("success")
            result=execmd("iscsiadm -m session -P  3" )
            flag=False
            for i in result.split("Target:"):
                i=i.replace("\t"," ")
                if i.contain(globals()['iqnname']):
                    flag=True
                    t=i.split("Attached scsi disk ")
                    assert  len(t)>1
                    assert  len(t[1].split(" "))>1
                    print t[1].split(" ")
                    disk=t[1].split(" ")[0]
                    result=execmd("mkfs.xfs  -f /dev/%s" % disk)
                    print "mkfs.xfs  result:%s" % result
                    dir="pdstest"+str(int(time.time()))
                    execmd("mkdir /opt/%s;mount  /dev/%s /opt/%s" % (dir,disk,dir))
                    result=execmd("df /opt/%s|grep /dev/%s|awk '{ print $2}'" % (dir,disk))
                    self.assertTrue(result=="2086912",msg=result)
                    result=execmd("dd if=/dev/zero bs=1024 count=1000576 of=/opt/%s/test" % dir)
                    result = execmd("ls -s /opt/%s/test|awk  '{print $1}'" % dir)
                    assert  result.contain("1000576")
                    result = execmd("du -s /opt/%s/test|awk  '{print $1}'" % dir)
                    assert result.contain("1000576")
            assert  flag
            result = execmd(
                "umount /opt/%s" % (dir))
            result=execmd(
                "iscsiadm --mode node   -u")
            assert  result.contain("success")
            lun=lun+1
        self.test_ames_del_lun_streamline()

    def test_ames_unbind_user_noexist(self):
        result = execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt unbind-user %s noexist%s" % (globals()["iqnname"], globals()["username"]))
        a =is_json_format(result)
        assert  a["ret"] == "NOK" and a["msg"] == "tgtadm: can't find the account"


    def test_ames_unbind_user_noiqn(self):
        result = execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt unbind-user noexist%s %s" % (globals()["iqnname"], globals()["username"]))
        a =is_json_format(result)
        self.assertTrue(a["ret"] == "NOK",msg=result)



    def test_ames_unbind_user(self):
        result=execmd("grep  -l   %s /etc/tgt/conf.d/*|xargs  -n1  -i  cat {}" % globals()["iqnname"])
        assert result.contain(globals()["username"]),result
        result = execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt unbind-user %s %s" % (
        globals()["iqnname"], globals()["username"]))
        a =is_json_format(result)
        print a
        assert a["ret"] == "OK",result
        result=execmd("grep  -l   %s /etc/tgt/conf.d/*|xargs  -n1  -i  cat {}" % globals()["iqnname"])
        assert not result.contain(globals()["username"])
        print result



    def test_ames_unbind_ip_single(self):
        result=execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt list-iqn|grep 'com.%s:amefs'|awk  '{ print $1 }'" % globals()['iqnname'])
        globals()["iqn"]=result.strip(":").strip("\"")
        result = execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt unbind-ip '%s' '%s'" % (globals()["iqnname"],globals()["ip"]))
        a =is_json_format(result)
        assert a["ret"]=="OK", result
        result=execmd("tgt-admin  -s")
        targetlist=str(result).split("Target ")
        targetlist.remove('')
        find=False
        for i in  targetlist:
            if i.contain(globals()['iqnname']):
                find=True
                t=i.split("ACL information:")
                if len(t)>1:
                    assert not str(t[1]).contain(globals()['ip']),i
        assert find



    def test_ames_del_iqn(self):
        result = execmd(
            "iscsiadm --mode node  -u" )
        print result
        result=execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt del-iqn   %s" % globals()['iqnname'])
        a =is_json_format(result)
        assert  a["ret"] == "OK",result
        result = execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt list-iqn")
        assert not result.contain(globals()['iqnname'])
        result = execmd("ls  /etc/tgt/conf.d/tgt%s.conf 2>/dev/null|wc -l" % globals()['iqnid'])
        print result
        assert  result=="0"
        result = execmd(
            "echo  'y'|/usr/local/amefs/sbin/ame lvg   stop  %s" % globals()['poolname'])
        result = execmd(
            "echo 'y'|/usr/local/amefs/sbin/ame lvg   delete  %s" % globals()['poolname'])


    def test_ames_del_iqn_no_exist(self):
        result=execmd("/usr/local/ames/ames_cfg.sh SET ame-tgt del-iqn   exist%s" % globals()['iqnname'])
        a =is_json_format(result)
        assert  a["ret"] == "NOK"




if __name__ == "__main__":
    runner=unittest.TextTestRunner()
    testunit = unittest.TestSuite()
    testunit.addTests(unittest.TestLoader().loadTestsFromTestCase(TestblockStorage))
    runner.run(testunit)
