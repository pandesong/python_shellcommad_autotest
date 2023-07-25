import _nfsclient as dll


class nfs3client(object):
    def __init__(self):
        self.ip = None
        self.path = None
        self.dll = dll
        self.index = 0

    def mount(self, ip, path):
        self.ip = ip
        self.path = path
        return self.dll.nfsmount(ip, path)

    def nfsmountex(self, ip, path):
        self.ip = ip
        self.path = path
        return self.dll.mountnfsex(self.index, str(ip), str(path))

    def listdir(self, path):
        return self.dll.nfs_listdir(path)
    def chdirdir(self, path):
        return self.dll.nfschdir(self.index,path)
    def mkdirex(self, path):
        return self.dll.mkdirex(self.index,path)
    def listdirex(self, path):
        return self.dll.nfs_listdirex(self.index, path)

    def rmfile(self, file):
        return self.dll.nfs_rmfile(file, "nfs://%s%s/%s" % (self.ip, self.path, file))

    def upload(self, local, remote):
        return self.dll.upload(local, ("nfs://%s%s/%s" % (self.ip, self.path, remote)))

    def nfsclose(self):
        return self.dll.nfsclose(self.ip, self.path)

    def download(self, remote, local):
        return self.dll.nfs_upload(("nfs://%s%s/%s" % (self.ip, self.path, remote)), local)

    def rmfileex(self, file):
        return self.dll.nfs_rmfileex(self.index, file)

    def uploadex(self, local, remote):
        #print (self.index, "nfs://%s%s/%s" % (self.ip, self.path, remote),local)
        return self.dll.nfs_uploadex(self.index,local, "%s" % ( remote))

    def nfscloseex(self):
        return self.dll.nfscloseex(self.index, self.ip, self.path)

    def initnfs(self, index, version):
        self.index = index
        return self.dll.nfsinit(index, version)
    def init(self):
        return self.dll.init()