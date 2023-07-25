# -*- coding: utf-8-*-
import os
import unittest
import configparser
import uuid
import md5sum
import _libssh  as dll
from nfs3client import nfs3client
import random
import json
import time
global globpath
import sys
globpath = ""

configpath="C:\\Users\\pandesong\\Desktop\\ameds_test\\ameds_testcase.conf"

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

def  execmd(cmd):
    print "执行指令:%s".decode("utf-8")  %  cmd
    rest = dll.ssh_exec(str(cmd))
    assert rest == 0
    return dll.p_get_exec_result(0).strip().strip('\r').strip('\n').decode("utf-8")


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
            rest = execmd(cmd)
            dst_md5 = rest.strip().strip()
            for unit in str(units).split("\n"):
                unit1 = ("%s/%s/%s/" + dir1 + remote) % (unit, globals()['groupname'], globals()['username'])
                rest = execmd(
                    "ls  \"%s\" 2>/dev/null|wc -l" % (
                        unit1
                    ))
                try:
                    num = num+int(rest.strip("\n").strip("\r"))
                except:
                    print "exec error %s" % rest.strip("\n").strip("\r")

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
            num = rest.decode("utf-8").encode("gbk")
            assert int(num) == 0
    return tmp


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
    global userpwd
    global ldap_user_ou
    ip = config["base"]["ip"]
    port = config["base"]["port"]
    user = config["base"]["user"]
    password = config["base"]["password"]
    userpwd = config["base"]["userpwd"]
    config_json = config["base"]["configjson"]
    ldap_server = config["base"]["ldap_server"]
    ldap_pwd = config["base"]["ldap_pwd"]
    ldap_user_dn = config["base"]["ldap_user_dn"].replace("\"","")
    ldap_base_dn = config["base"]["ldap_base_dn"].replace("\"","")
    ldap_user_ou = config["base"]["ldap_user_ou"].replace("\"","")
def one_host(unit):
    l=[]
    unitnumber = unit
    for m in range(1,unitnumber+1):
        for n in range(1,unitnumber+1):
                if   m/2 > n and m>2:
                    l.append(("%d %d") %  (m,n))
    return l






class TestfileStorage(unittest.TestCase):
    def __init__(self,*args,**kwargs):
        super(TestfileStorage,self).__init__(*args,**kwargs)
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
        global ldap_user_dn
        global ldap_base_dn
        global userpwd
        global ldap_user_ou
        globals()['poolname'] = str(uuid.uuid4())
        session = dll.ssh_login_by_password(str(ip), int(port), str(user), str(password))
        assert session == 0,("%s  %s  %s  %s") % (str(ip),str(port),str(user), str(password))
        hostname=execmd("hostname")
        units = execmd( "lsblk  -l|grep  mnt|awk   '{ print $7}'")
        unit=units.split("\n")[0]
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg    create   %s   %s:%s/%s/" % (globals()['poolname'],hostname,unit, globals()['poolname']))
        print result
        assert ("lvgroup create: %s: success: please start the lvgroup to access data" % globals()['poolname']) == result
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg   info %s |grep  Status|awk  '{ print $2}'" % globals()['poolname'])
        assert result=="Created"
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg   start  %s " % globals()['poolname'])
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg   info %s |grep  Status|awk  '{ print $2}'" % globals()['poolname'])
        assert result == "Started"
        result = execmd("/usr/local/amefs/sbin/ame lvg   set  %s  performance.dcache  on " % (globals()['poolname']))

    @classmethod
    def tearDownClass(self):
        rest = execmd(
            " echo 'y'| /usr/local/amefs/sbin/ame lvg   stop  %s force" % globals()['poolname'])
        rest = execmd(
            "echo 'y'| /usr/local/amefs/sbin/ame lvg   delete  %s " % globals()['poolname'])

        result = rest
        assert  result.find("lvgroup delete: %s: success" % globals()['poolname'])>=0
        dll.ssh_close()



    def test_ames_get_node_model(self):
        result = execmd("/usr/local/ames/ames_cfg.sh GET dev-model")
        print result
        a = is_json_format(result)
        assert a["ret"] == "OK", result
        globals()['model']=a["data"][0]["type"]


    def test_ames_get_lvg_info(self):
        #session = dll.ssh_login_by_password(ip1, port, user, passwd)
        #assert session == 0
        result = execmd(
            "/usr/local/amefs/sbin/ame lvg   info")
        assert len(result)!=0




    @unittest.skip("2")
    def test_ames_get_network_status_detail_deban(self):
        import uuid
        blockname = str(uuid.uuid4())
        result = execmd("/usr/local/ames/ames_cfg.sh GET network-status-detail")
        print result
        a = is_json_format(result)
        assert a["ret"] == "OK", result
        result = execmd("cat   %S|grep  NETCARD |awk  -F '{'  '{ print $2}'|awk  -F '}'  '{ print $1}'" % config_json)

        P_IP_INTF_name=str(result).split(",")[0].split(":")[0]
        P_IP_INTF_card = str(result).split(",")[0].split(":")[1].strip("\"")
        I_IP_INTF_name = str(result).split(",")[1].split(":")[0].strip("\"")
        I_IP_INTF_card = str(result).split(",")[1].split(":")[1].strip("\"")
        P_IP_INTF_ip=a["data"][0][P_IP_INTF_card]["ip"]
        P_IP_INTF_type = a["data"][0][P_IP_INTF_card]["type"]
        P_IP_INTF_status = a["data"][0][P_IP_INTF_card]["status"]
        P_IP_INTF_purpose = a["data"][0][P_IP_INTF_card]["purpose"]
        P_IP_INTF_mask = a["data"][0][P_IP_INTF_card]["mask"].encode("utf-8")
        assert "outbound" == P_IP_INTF_purpose
        result = execmd("ifconfig %s|grep netmask|awk  -F 'netmask'  '{ print $2}'|awk  '{ print $1}'"  % P_IP_INTF_card)

        assert  P_IP_INTF_mask == result
        result = execmd("ifconfig %s|grep netmask|awk  -F 'netmask'  '{ print $2}'|awk  '{ print $1}'"  % I_IP_INTF_card)

        I_IP_INTF_ip=a["data"][1][I_IP_INTF_card]["ip"].encode("utf-8")
        I_IP_INTF_type = a["data"][1][I_IP_INTF_card]["type"].encode("utf-8")
        I_IP_INTF_status = a["data"][1][I_IP_INTF_card]["status"]
        I_IP_INTF_purpose = a["data"][1][I_IP_INTF_card]["purpose"]
        I_IP_INTF_mask = a["data"][1][I_IP_INTF_card]["mask"].encode("utf-8")
        assert "inbound" == I_IP_INTF_purpose
        result = execmd("ifconfig %s|grep netmask|awk  -F 'netmask'  '{ print $2}'|awk  '{ print $1}'"  % I_IP_INTF_card)

        assert  I_IP_INTF_mask == result
        result = execmd("ifconfig %s|grep  'inet '|awk  '{ print $2}'"  % I_IP_INTF_card)

        assert  I_IP_INTF_ip == result
        #print ("create block result is %s" % str(result))
        #assert "OK" in result==True



    def test_ames_get_network_status_detail(self):
        import uuid
        blockname = str(uuid.uuid4())
        result = execmd("/usr/local/ames/ames_cfg.sh GET network-status-detail")
        print result
        a = is_json_format(result)
        assert a["ret"] == "OK", result
        result = execmd("cat   %s|grep  NETCARD |awk  -F '{'  '{ print $2}'|awk  -F '}'  '{ print $1}'" % config_json)
        P_IP_INTF_name=str(result).split(",")[0].split(":")[0]
        P_IP_INTF_card = str(result).split(",")[0].split(":")[1].strip("\"")
        I_IP_INTF_name = str(result).split(",")[1].split(":")[0].strip("\"")
        I_IP_INTF_card = str(result).split(",")[1].split(":")[1].strip("\"")
        P_IP_INTF_ip=a["data"][0][P_IP_INTF_card]["ip"]
        P_IP_INTF_type = a["data"][0][P_IP_INTF_card]["type"]
        P_IP_INTF_status = a["data"][0][P_IP_INTF_card]["status"]
        result = execmd("ifconfig %s|grep netmask|awk  -F 'netmask'  '{ print $2}'|awk  '{ print $1}'"  % P_IP_INTF_card)

        result = execmd("ifconfig %s|grep netmask|awk  -F 'netmask'  '{ print $2}'|awk  '{ print $1}'"  % I_IP_INTF_card)

        I_IP_INTF_ip=a["data"][1][I_IP_INTF_card]["ip"].encode("utf-8")
        I_IP_INTF_type = a["data"][1][I_IP_INTF_card]["type"].encode("utf-8")
        I_IP_INTF_status = a["data"][1][I_IP_INTF_card]["status"]
        result = execmd("ifconfig %s|grep netmask|awk  -F 'netmask'  '{ print $2}'|awk  '{ print $1}'"  % I_IP_INTF_card)

        result = execmd("ifconfig %s|grep  'inet '|awk  '{ print $2}'"  % I_IP_INTF_card)

        assert  I_IP_INTF_ip == result

    def test_ames_get_hostname(self):

        result = execmd("/usr/local/ames/ames_cfg.sh GET hostname")
        hostname = execmd("hostname")
        globals()["hostname"]=hostname
        print result
        a = is_json_format(result)
        assert a["ret"] == "OK", result
        assert a["data"][0]["hostname"] ==hostname


    def test_ames_service_status2(self):

        result = execmd("/usr/local/ames/ames_cfg.sh GET service-status2")

        a = is_json_format(result)
        assert a["ret"] == "OK", result
        print "获取所有服务的状态 %s"  % result
        assert  str(result).find("fail")<0

    def test_ames_chek_status(self):

        result = execmd("/usr/local/ames/ames_cfg.sh SET service-check '' ''  %s" % globals()["hostname"])

        a = is_json_format(result)
        assert a["ret"] == "OK", result

        print "获取所有服务的状态 %s"  % result
        #assert  str(result).find("fail")<0





    def test_ames_get_pd_info(self):
        result = execmd("/usr/local/ames/ames_cfg.sh GET pd-info")

        a = is_json_format(result)
        assert a["ret"] == "OK", result



    def test_ames_get_raidcard_info(self):
        result = execmd("/usr/local/ames/ames_cfg.sh GET raidcard-info")

        print "获取radicard 结果 %s"  % result
        a = is_json_format(result)
        assert a["ret"] == "OK", result


    def test_ames_get_ld_info(self):
        result = execmd("/usr/local/ames/ames_cfg.sh GET ld-preview-info %s" % globals()['model'])
        print "获取LD信息 ld-preview-info结果 %s"  % result
        a = is_json_format(result)
        assert a["ret"] == "OK", result
        result = execmd(str("/usr/local/ames/ames_cfg.sh GET ld-info-detail %s" % globals()['model']))

        print "获取LD信息 ld-preview-info结果 %s"  % result
        a = is_json_format(result)
        assert a["ret"] == "OK", result


    def test_ames_disk_location(self):
        result = execmd("/usr/local/ames/ames_cfg.sh SET pd-led '0' '0' '8'")
        print "获取硬盘定位信息结果 %s"  % result
        a = is_json_format(result)
        assert a["ret"] == "OK", result


    def test_ames_disk_reset(self):
        result = execmd(str("/usr/local/ames/ames_cfg.sh SET reset-pd-led  %s" % globals()['model']))

        print "获取硬盘定位重置信息结果 %s"  % result
        a = is_json_format(result)
        assert a["ret"] == "OK", result


    def test_ames_disk_capacity(self):
        result = execmd("cat %s" % config_json)
        a = is_json_format(result)
        path=a["CONFIG"][0]["ROOTFS"]
        result = execmd(str("df %s|grep /|grep  -v  Used|awk  '{ print $2,$3,$4,$5}'" % path))
        total=int(str(result).split(" ")[0])/1024
        used=int(str(result).split(" ")[1])/1024
        availsize =int(str(result).split(" ")[2])/1024
        pre=str(result).split(" ")[3]
        result = execmd("/usr/local/ames/ames_cfg.sh GET rootfs-used")
        print "获取硬盘容量结果 %s"  % result
        a = is_json_format(result)
        assert a["ret"] == "OK", result
        assert abs(a["data"][0]["totalSize"]-total)<10,(a["data"][0]["totalSize"],used)
        assert abs(a["data"][0]["usedSize"]-used)<10,(a["data"][0]["usedSize"],used)
        assert abs(a["data"][0]["availSize"] -availsize)<10,(a["data"][0]["availSize"],used)
        assert a["data"][0]["pre"]==pre


    def test_ames_host_rename(self):
        result = execmd("hostname")
        hostname=result
        tmpname="test"+str(int(time.time()))
        result = execmd("/usr/local/ames/ames_cfg.sh SET node-rename %s " % tmpname)
        result = execmd("hostname")
        assert tmpname==result
        result =execmd("/usr/local/ames/ames_cfg.sh SET node-rename %s " % hostname)
        result = execmd("hostname")
        assert hostname==result


    def test_ames_get_network_status(self):
        result = execmd("/usr/local/ames/ames_cfg.sh GET network-status-detail %s" % ip)
        a = is_json_format(result)
        assert a["ret"] == "OK", result

    def test_ames_get_ntp_status(self):
        result = execmd("/usr/local/ames/ames_cfg.sh GET ntp-status")

        print result
        a = is_json_format(result)
        assert a["ret"] == "OK",result
        assert a["data"][0]["status"].find("running")>=0


    def test_ames_add_group(self):
        import random
        result = execmd("cat  /etc/group|awk -F ':' '{ print $3}'")
        t=str(result).split("\n")
        t=list(map(int,t))
        t1=list(range(1, 65535))
        t2=list(set(t1)-set(t))
        globals()['groupname']="pdstest"+str(int(time.time()))
        globals()['groupid']=t2[random.randint(1,len(t2))]
        result =execmd( "/usr/local/ames/ames_cfg.sh SET group add %s %d" % (globals()['groupname'],globals()['groupid']))
        a = is_json_format(result)
        assert a["ret"] == "OK",result
        result=execmd("cat /etc/group|grep  %s|wc -l" % globals()['groupname'])
        assert  result=="1",result

    def test_ames_set_group_quota(self):
        import random
        result = execmd("cat  /etc/group|awk -F ':' '{ print $3}'")
        t=str(result).split("\n")
        t=list(map(int,t))
        t1=list(range(1, 65535))
        t2=list(set(t1)-set(t))
        result =execmd( "/usr/local/amefs/sbin/set_user_path.sh  %s   /%s  %s limit-usage" % (globals()['poolname'] ,globals()['groupname'],"100GB"))
        assert str(result) .contain("lvgroup quota : success"), [result]
        result=execmd("fallocate  -l   /exports/%s/%s/test  104857600000" % (globals()['poolname'] ,globals()['groupname']))
        result = execmd("/usr/local/amefs/sbin/ame  lvg quota   %s  list   /%s |grep  ^/|awk  '{ print $2}'" % (globals()['poolname'] , globals()['groupname']))
        print "quota   result  %s"   %  result
        assert 100-float(str(result).replace("GB","").replace("Bytes","").replace("MB",""))<5,result


    def test_ames_add_user(self):
        import random
        result = execmd("cat  /etc/passwd|awk -F ':' '{ print $3}'")
        t=str(result).split("\n")
        t=list(map(int,t))
        t1=list(range(1, 65535))
        t2=list(set(t1)-set(t))
        globals()['username']="pdstest"+str(int(time.time()))
        globals()['userid']=t2[random.randint(1,len(t2))]
        result =execmd( "/usr/local/ames/ames_cfg.sh SET user add  %d %s %s %d" % (globals()['groupid'],globals()['username'],userpwd,globals()['userid']))
        a = is_json_format(result)
        assert a["ret"] == "OK",result
        result=execmd("cat /etc/passwd|grep  %s|wc -l" % globals()['username'])
        assert  result=="1"


    def test_ames_set_user_quota(self):
        result =execmd( "/usr/local/amefs/sbin/set_user_path.sh  %s   /%s/%s  %s limit-usage" % (globals()['poolname'] ,globals()['groupname'],globals()['username'],"100GB"))
        assert str(result).contain("lvgroup quota : success"),result
        result=execmd("/root/tt   /exports/%s/%s/%s/test  102400 1024000" % (globals()['poolname'] ,globals()['groupname'],globals()['username']))
        result = execmd("/usr/local/amefs/sbin/ame  lvg quota   %s  list   /%s/%s |grep  ^/|awk  '{ print $2}'" % (globals()['poolname'] , globals()['groupname'],globals()['username']))
        print "quota   result  %s"   % result
        assert 100-float(str(result).replace("GB","").replace("Bytes","").replace("MB",""))<5,result


    def test_ames_get_user_quota_list(self):
        result = execmd("cat  /etc/passwd|awk -F ':' '{ print $3}'")
        result = execmd("/usr/local/ames/ames_cfg.sh GET amefs-quota list '%s' '/%s/%s' 'N'" % (globals()['poolname'], globals()['groupname'], globals()['username']))
        a = is_json_format(result)
        assert a["ret"] == "OK",result
        print a

    def test_ames_get_all_ldap_user(self):
        result = execmd("/usr/local/ames/ames_cfg.sh GET ldapusers  ou=%s,%s " % (ldap_user_ou,ldap_base_dn))
        a = is_json_format(result)
        assert a["ret"] == "OK",result
        assert a.has_key("data"),result
        assert len(a["data"])!=0,result


    @unittest.skip("弃用")
    def test_ames_get_all_ldap_group(self):
        result = execmd("/usr/local/ames/ames_cfg.sh GET ldapgroups")
        a = is_json_format(result)
        assert a["ret"] == "OK",result
        assert len(a["data"]) != 0,result
        print result

    def test_ames_config_ldap_service(self):
        result = execmd("/usr/local/ames/ames_cfg.sh SET user ldap ldap://%s %s" %( ldap_server,ldap_base_dn))
        a = is_json_format(result)
        assert a["ret"] == "OK",result
        print result

    def test_ames_config_ldap_samba_user(self):
        result = execmd("/usr/local/ames/ames_cfg.sh SET share ldapsam ldap://%s %s %s" % (ldap_server,ldap_user_dn,ldap_pwd ))
        a = is_json_format(result)
        assert a["ret"] == "OK",result
        print result


    def test_ames_share_nfs(self):
        result = execmd("/usr/local/ames/ames_cfg.sh SET share NFS  %s  %s %s   \"/exports/%s_%s/%s *(rw,async,insecure,no_subtree_check,no_root_squash,all_squash,anonuid=%d,anongid=%s,fsid=%s)\"" % (globals()['poolname'],globals()['groupname'], globals()['username'],

        globals()['groupname'], globals()['username'],globals()['poolname'], globals()['userid'], globals()['groupid'],"".join(str(uuid.uuid4()).replace("-","").lower())))
        a = is_json_format(result)
        assert a["ret"] == "OK"
        assert result,result=="{\"ret\":\"OK\",\"msg\":null}"
        result=execmd("cat  /etc/exports|grep   %s_%s/%s|wc -l" % (globals()['groupname'], globals()['username'],globals()['poolname']))
        assert result=="1",result
        result=execmd("exportfs  -arv")
        path = "E:\\11111"
        nfs = nfs3client()
        nfs.init()
        nfs.initnfs(0, 3)
        nfs.chdirdir(".")
        units=execmd("/usr/local/amefs/sbin/ame lvg  info   %s| grep  unit|grep  node|awk '{ print $2}'|awk   -F ':' '{ print $2}'\n" % globals()['poolname'])
        remote_file_path = "/exports/%s_%s/%s" % (globals()['groupname'], globals()['username'],globals()['poolname'])
        mount_res=nfs.nfsmountex(ip, remote_file_path)
        assert mount_res==0,mount_res
        uploadfiles(path, nfs, remote_file_path, "./",units,ip)
        nfs.chdirdir(remote_file_path)
        rmfiles(path, nfs, remote_file_path,  "./")
        #nfs.nfscloseex()


    def test_ames_del_share_nfs(self):
        result = execmd("/usr/local/ames/ames_cfg.sh SET share-del  NFS  %d" % globals()['userid'])
        a=is_json_format(result)
        assert a["ret"] == "OK",result
        result=execmd("cat  /etc/exports|grep %s|wc -l" % globals()['username'])
        assert result=="0",result
        nfs = nfs3client()
        nfs.init()
        nfs.initnfs(0, 3)
        remote_file_path = "/exports/%s_%s/%s" % (globals()['groupname'], globals()['username'], globals()['poolname'])
        #assert nfs.nfsmountex(ip1, remote_file_path) != 0

    def test_ames_share_share_cifs(self):
        result = execmd(
            "/usr/local/ames/ames_cfg.sh SET share CIFS %s %s %s '' '%s' '' ''" % (
            globals()['poolname'], globals()['groupname'], globals()['username'],userpwd))
        assert result == "{\"ret\":\"OK\",\"msg\":null}",result
        result = execmd("cat /etc/samba/smb.conf|grep   %s_%s|wc -l" % ( globals()['username'],globals()['poolname']))
        assert result == "2", result

    def test_amefs_del_user(self):
        result = execmd( "cat /etc/passwd")
        assert result.find(globals()['username'])>0,result
        result = execmd( "/usr/local/amefs/sbin/del_user_path.sh    %s %s   %s" % (globals()['poolname'],globals()['groupname'],globals()['username']))
        #a=is_json_format(result)
        assert str(result).contain("删除目录成功"),result
        result = execmd( "cat /etc/passwd|grep %s" % globals()['username'])
        assert result.find(globals()['username'])<0

    def test_amefs_del_group(self):
        result = execmd( "cat /etc/group")
        assert result.find(globals()['groupname'])>0,result
        result = execmd( "/usr/local/amefs/sbin/del_user_path.sh  %s  %s" % (globals()['poolname'],globals()['groupname']))
        #a=is_json_format(result)
        #assert a["ret"] == "OK",result
        assert str(result).contain("删除目录成功"),result
        result = execmd( "cat /etc/group|grep %s" % globals()['groupname'])
        assert result.find(globals()['groupname'])<0





if __name__ == "__main__":
    os.path.join(os.getcwd(),"testcase_dir")
    runner=unittest.TextTestRunner()
    testunit = unittest.TestSuite()
    testunit.addTests(unittest.TestLoader().loadTestsFromTestCase(TestfileStorage))
    runner.run(testunit)
