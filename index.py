from datetime import datetime
import math
import random

TOTAL_BLOCKS = 128
BLOCK_SIZE   = 512
MAX_INODES   = 64
DIRECT_PTRS  = 8

class Inode:
    def __init__(self, inode_id, file_type, name, permissions):
        self.inode_id        = inode_id
        self.file_type       = file_type
        self.name            = name
        self.permissions     = permissions
        self.size            = 0
        self.link_count      = 1
        self.uid             = 1000
        self.gid             = 1000
        self.created         = datetime.now()
        self.modified        = datetime.now()
        self.direct_blocks   = []
        self.indirect_block  = None
        self.content         = ""

    def perm_string(self):
        prefix = "d" if self.file_type == "directory" else "-"
        return prefix + self.permissions


class DirectoryEntry:
    def __init__(self, name, inode_id, parent_inode_id=None):
        self.name            = name
        self.inode_id        = inode_id
        self.parent_inode_id = parent_inode_id
        self.children        = []


class Filesystem:
    def __init__(self):
        self.inodes       = {}
        self.block_bitmap = [False] * TOTAL_BLOCKS
        self.next_inode   = 1
        self.root         = None

    def _alloc_inode(self, file_type, name, permissions):
        if self.next_inode > MAX_INODES:
            raise RuntimeError("Inode table is full!")
        inode = Inode(self.next_inode, file_type, name, permissions)
        self.inodes[self.next_inode] = inode
        self.next_inode += 1
        return inode

    def _alloc_blocks(self, content):
        needed = max(1, math.ceil(len(content.encode()) / BLOCK_SIZE))
        free   = [i for i, used in enumerate(self.block_bitmap) if not used]
        if len(free) < needed:
            raise RuntimeError("Disk is full!")
        chosen = random.sample(free, needed)
        for b in chosen:
            self.block_bitmap[b] = True
        direct   = chosen[:DIRECT_PTRS]
        indirect = chosen[DIRECT_PTRS:] if len(chosen) > DIRECT_PTRS else None
        return direct, indirect

    def _free_blocks(self, inode):
        for b in inode.direct_blocks:
            self.block_bitmap[b] = False
        if inode.indirect_block:
            for b in inode.indirect_block:
                self.block_bitmap[b] = False

    def _mkdir(self, parent_entry, name, permissions):
        inode = self._alloc_inode("directory", name, permissions)
        entry = DirectoryEntry(name, inode.inode_id, parent_entry.inode_id)
        parent_entry.children.append(entry)
        return entry

    def _mkfile(self, parent_entry, name, permissions, content=""):
        inode                = self._alloc_inode("file", name, permissions)
        inode.content        = content
        inode.size           = len(content.encode())
        direct, indirect     = self._alloc_blocks(content)
        inode.direct_blocks  = direct
        inode.indirect_block = indirect
        entry = DirectoryEntry(name, inode.inode_id, parent_entry.inode_id)
        parent_entry.children.append(entry)
        return entry

    def create_file(self, parent_entry, name, content="New file.\n"):
        if any(c.name == name for c in parent_entry.children):
            raise ValueError(f"'{name}' already exists.")
        return self._mkfile(parent_entry, name, "rw-r--r--", content)

    def create_directory(self, parent_entry, name):
        if any(c.name == name for c in parent_entry.children):
            raise ValueError(f"'{name}' already exists.")
        return self._mkdir(parent_entry, name, "rwxr-xr-x")

    def delete_entry(self, parent_entry, entry):
        inode = self.inodes[entry.inode_id]
        if inode.file_type == "directory" and entry.children:
            raise ValueError("Cannot delete a non-empty directory.")
        self._free_blocks(inode)
        inode.link_count -= 1
        if inode.link_count <= 0:
            del self.inodes[entry.inode_id]
        parent_entry.children.remove(entry)

    def create_hard_link(self, target_entry, parent_entry, link_name):
        inode = self.inodes[target_entry.inode_id]
        if inode.file_type == "directory":
            raise ValueError("Hard links to directories are not allowed.")
        link_entry = DirectoryEntry(link_name, target_entry.inode_id, parent_entry.inode_id)
        parent_entry.children.append(link_entry)
        inode.link_count += 1
        return link_entry

    def init_root(self):
        root_inode = self._alloc_inode("directory", "/", "rwxr-xr-x")
        self.root  = DirectoryEntry("/", root_inode.inode_id)

        home = self._mkdir(self.root, "home", "rwxr-xr-x")
        etc  = self._mkdir(self.root, "etc",  "rwxr-xr-x")
        var  = self._mkdir(self.root, "var",  "rwxr-xr-x")
        user = self._mkdir(home,      "user", "rwxr-xr-x")
        log  = self._mkdir(var,       "log",  "rwxr-xr-x")

        self._mkfile(user, "readme.txt",  "rw-r--r--",
                     "Welcome to the Inode Filesystem Emulator!\n\n"
                     "Click any file to inspect its inode.\n"
                     "Edit content and press Save to watch blocks update.\n")

        self._mkfile(user, "notes.txt",   "rw-r--r--",
                     "OS Course Notes\n\n"
                     "An inode stores:\n"
                     "  - file type and permissions\n"
                     "  - owner UID/GID\n"
                     "  - size in bytes\n"
                     "  - timestamps\n"
                     "  - block pointers\n")

        self._mkfile(user, "script.sh",   "rwxr-xr-x",
                     "#!/bin/bash\necho 'Hello Filesystem!'\n")

        self._mkfile(etc,  "hostname",    "rw-r--r--", "mycomputer\n")
        self._mkfile(etc,  "passwd",      "rw-r--r--",
                     "root:x:0:0:/root:/bin/bash\n"
                     "user:x:1000:1000:/home/user:/bin/bash\n")

        self._mkfile(log,  "syslog",      "rw-r-----",
                     "[2025-01-10 08:00:01] System boot\n"
                     "[2025-01-10 08:00:05] Filesystem mounted\n")

        return self.root