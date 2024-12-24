import argparse
import re
import difflib
import subprocess
import os
import sqlite3
import sys
import configparser
import concurrent.futures

current_path = os.path.dirname(os.path.abspath(__file__))

li = lambda x : print('\x1b[01;38;5;214m' + str(x) + '\x1b[0m')
ll = lambda x : print('\x1b[01;38;5;1m' + str(x) + '\x1b[0m')

# Binary2Sqlite
class B2S():
    def __init__(self, oldfpath, newfpath) -> None:
        # must be abspath
        self.old = {"fpath": oldfpath, 
                    "fname": os.path.basename(oldfpath), 
                    "dname": os.path.dirname(oldfpath) }
        self.new = {"fpath": newfpath, 
                    "fname": os.path.basename(newfpath), 
                    "dname": os.path.dirname(newfpath) }
            
    def GetConfig(self):
        self.config = configparser.ConfigParser()
        self.config.read(current_path + "/setting.cfg")
        return self.config
    
    def ExecuteCommand(self, ida_path, i, if_new):
        command = [
            ida_path,
            "-A",
            "-B",
            "-S" + current_path + "/diaphora/diaphora.py",
            i
        ]
        sqlite_name = i + (".new" if if_new else ".old") + ".sqlite"
        os.environ['DIAPHORA_AUTO'] = "1"
        os.environ['DIAPHORA_EXPORT_FILE'] = sqlite_name
        li(f"{i}(binary) to {sqlite_name}")
        li("[*] watting")
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stdout)


    def SaveSqlite(self):
        self.GetConfig()
        ida_path = self.config['ida_path']['path']
        FileName = [self.old["fpath"], self.new["fpath"]]
        li('[*] Multi-process startup')
        # with concurrent.futures.ProcessPoolExecutor(max_workers = 2) as executor:
        #     futures = [executor.submit(self.ExecuteCommand, ida_path, i) for i in FileName]

        #     for future in concurrent.futures.as_completed(futures):
        #         future.result()  

        self.ExecuteCommand(ida_path, self.old["fpath"], False)
        self.ExecuteCommand(ida_path, self.new["fpath"], True)

        command = [
            sys.executable,
            current_path + "/diaphora/diaphora.py",
            self.old["fpath"] + ".old.sqlite",
            self.new["fpath"] + ".new.sqlite",
            "-o",
            self.new["fpath"] + ".new.sqlite.output.sqlite"
        ]
        print(command)
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stdout)
        
# BinaryDiff
class BD():
    def __init__(self, old, new, local) -> None:
        
        self._old = {"fpath": old, 
                    "fname": os.path.basename(old), 
                    "dname": os.path.dirname(old) }
        self._new = {"fpath": new, 
                    "fname": os.path.basename(new), 
                    "dname": os.path.dirname(new) }
        # self.old = old
        # self.new = new
        # self.local = local
        # self.file_name = os.path.dirname(os.path.abspath(self.old)) + '/' + os.path.basename(old) + '-' + os.path.basename(new) + ".diff"
        # self.out_path = os.path.dirname(os.path.abspath(self.old))
        # self.output = self.out_path + "/output.sqlite"
        # if local:
        #     self.old_diff_filename = os.path.dirname(os.path.abspath(self.old)) + '/' + os.path.basename(old) + ".cc"
        #     self.new_diff_filename = os.path.dirname(os.path.abspath(self.old)) + '/' + os.path.basename(new) + ".cc"

        self.old = old
        self.new = new
        self.local = local
        self.file_name = self._new["fname"] + ".diff"
        self.out_path = self._new["dname"]
        self.output = self._new["fpath"]+ ".output.sqlite"
        if local:
            self.old_diff_filename = self._old["fpath"] + ".cc"
            self.new_diff_filename = self._new["fpath"] + ".cc"

    
    def SqliteOutput(self, file_name, sql):
        #li("connecting %s"%(file_name))
        conn = sqlite3.connect(file_name)
        cursor = conn.cursor()

        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()
        return rows
    
    def UpdateDict(self, name, name2=None, old_context=None, new_context=None):
        if not old_context:
            old_context = ""
        if not new_context:
            new_context = ""
        diff_dict = {
            "name": name,
            "name2": name2,
            "old": old_context,
            "new": new_context
        }
        return diff_dict

    def Write_File(self, file_name, content):
        with open(f'{file_name}', 'a+') as file:
            file.write(f'{content}\n\n')
            #file.write('\n' * 2 + '-' * 0x60 + '\n')
    
    def NewFuncDiff(self):
        primary_unmatch = self.SqliteOutput(self.output, "select address, name from unmatched where type = 'primary'")
        li("[+] Newly added functions")
        for row in primary_unmatch:
            li("NewFuncDiff: Write_File(self.new_diff_filename, pp)")
            address, name = row
            print(address + ' | ' + name)

            functions = self.SqliteOutput(self.new, f"select prototype, pseudocode from functions where address = 0x{address}")
            prototype, pseudocode = functions[0]
            if not prototype:
                break
            pp = prototype + pseudocode
            if not self.local:
                Func_diff = self.UpdateDict(name, None, None, pp)

                diff = difflib.unified_diff(Func_diff['old'].splitlines(), Func_diff['new'].splitlines(), fromfile=name, tofile=name, lineterm='')
                # for line in diff:
                #     print(line, end='\n')
                with open(f'{self.file_name}', 'a+') as file:
                    for line in diff:
                        file.write(f'{line}\n')  
            if self.local:
                
                self.Write_File(self.new_diff_filename, pp)
                self.Write_File(self.old_diff_filename, prototype + '{\n}')
        
        secondary_unmatch = self.SqliteOutput(self.output, "select address, name from unmatched where type = 'secondary'")
        li("[+] Subtracting function")
        for row in secondary_unmatch:
            address, name = row
            print(address + ' | ' + name)

            functions = self.SqliteOutput(self.old, f"select prototype, pseudocode from functions where address = 0x{address}")
            prototype, pseudocode = functions[0]
            if not prototype:
                break
            pp = prototype + pseudocode
            if not self.local:
                Func_diff = self.UpdateDict(name, None, None, pp)

                diff = difflib.unified_diff(Func_diff['new'].splitlines(), Func_diff['old'].splitlines(), fromfile=name, tofile=name, lineterm='')
                # for line in diff:
                #     print(line, end='\n')
                with open(f'{self.file_name}', 'a+') as file:
                    for line in diff:
                        file.write(f'{line}\n')
            
            if self.local:
                self.Write_File(self.old_diff_filename, pp)
                #print(pp)
    
    def PDiff(self, type):
        unmatch = self.SqliteOutput(self.output, f"select address, address2, name, name2 from results where type = '{type}'")
        li(f"[+] {type}Diff")
        for row in unmatch:
            address, address2, name, name2 = row
            print(address + ' | ' + address2 + ' | '+ name + ' | ' + name2)

            functions = self.SqliteOutput(self.old, f"select prototype, pseudocode from functions where address = 0x{address}")
            prototype, pseudocode = functions[0]
            pp1 = prototype + pseudocode

            functions = self.SqliteOutput(self.new, f"select prototype, pseudocode from functions where address = 0x{address2}")
            prototype, pseudocode = functions[0]
            pp2 = prototype + pseudocode
            if not self.local:
                Func_diff = self.UpdateDict(name, name2, pp1, pp2)
                
                diff = difflib.unified_diff(Func_diff['old'].splitlines(), Func_diff['new'].splitlines(), fromfile=name, tofile=name2, lineterm='')
                with open(f'{self.file_name}', 'a+') as file:
                    for line in diff:
                        file.write(f'{line}\n')
            if self.local:
                self.Write_File(self.old_diff_filename, pp1)
                self.Write_File(self.new_diff_filename, pp2)
    
    def PartialDiff(self):
        self.PDiff("partial")
    
    def MultimatchDiff(self):
        self.PDiff("multimatch")
    
    def GistCommand(self, *args):
        full_command = ["gh", "gist"] + list(args)
        result = subprocess.run(full_command, capture_output=True, text=True)
        return result.stdout.strip()
    
    def GistCreat(self):
        li('[*] Gist Creat')
        result = self.GistCommand("create", "-d", f"{self.gist_desc}", current_path + "/README.md")
        match = re.search(r'https://gist\.github\.com/([^/]+)/([^/]+)', result)
        self.id = match.group(2)
        li('[+] Gist id = ' + self.id)

    def GistUpload(self):
        li('[*] Upload Gist')
        result = self.GistCommand("list", "--secret")
        print(result)
        if f"{self.gist_desc}" not in result:
            ll('[-] not in gist')
            self.GistCreat()
        else:
            li('[+] in gist')
            match = re.search(r'^(\S+)', result)
            self.id = match.group(1)
            li('[+] Gist id = ' + self.id)
        
        result = self.GistCommand("edit", self.id, "-a", os.path.abspath(os.path.join("./", f"{self.file_name}")))
        print(result)
        li('[+] open: https://www.z1r0.top/binarydiff/?' + self.id + '/' + f"{os.path.basename(self.old) + '-' + os.path.basename(self.new) + '.diff'}")
        

    def main(self):
        #self.NewFuncDiff()
        if not self.local:
            desc = B2S.GetConfig(self)
            self.gist_desc = desc['gist']['desc']
            self.PartialDiff()
            self.MultimatchDiff()
            self.NewFuncDiff()
            self.GistUpload()
        else:
            self.PartialDiff()
            self.MultimatchDiff()
            self.NewFuncDiff()

def is_elf_or_exe(file_path):
    with open(file_path, 'rb') as file:
        magic = file.read(4)
        
    # ELF 文件的魔术数字
    if magic.startswith(b'\x7fELF'):
        return "ELF"
    # PE (EXE) 文件的魔术数字
    elif magic.startswith(b'MZ'):
        return "EXE"
    else:
        return "Unknown"
    
def get_match_files(dir1, dir2):
    def get_files(directory):
        # 只获取elf和exe文件
        files = []
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                # 构建相对路径，使得文件路径是相对于目录的
                rel_path = os.path.relpath(os.path.join(root, filename), directory)
                if is_elf_or_exe(os.path.join(directory, rel_path)) is ("ELF" or "EXE"):
                    #print(rel_path)
                    files.append(rel_path)
        return set(files)

    files_in_dir1 = get_files(dir1)
    files_in_dir2 = get_files(dir2)
    
    # 找出在两个目录中都存在的文件
    common_files = files_in_dir1 & files_in_dir2
    
    # 找出只在第一个目录中存在的文件
    only_in_dir1 = files_in_dir1 - files_in_dir2
    
    # 找出只在第二个目录中存在的文件
    only_in_dir2 = files_in_dir2 - files_in_dir1

    return [common_files, only_in_dir1|only_in_dir2]
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Diff old_file and new_file.')
    
    parser.add_argument('--old_file', type=str, help='The old file')
    parser.add_argument('--new_file', type=str, help='The new file')
    parser.add_argument('--old_dir', type=str, help='The old directory')
    parser.add_argument('--new_dir', type=str, help='The new directory')
    parser.add_argument('--local', help='Local Diff', action="store_const", const=1, default=0)

    args = parser.parse_args()

    # if args.old is None and args.new is None:
    #     parser.print_help()
    #     sys.exit(1)
    # elif args.old is None or args.new is None:
    #     print("Error: Both --old and --new parameters are required.")
    #     parser.print_help()
    #     sys.exit(1)
    
    if args.old_file and args.new_file:
        file_path = os.path.dirname(os.path.abspath(args.old_file))
        binary = B2S(args.old_file, args.new_file)
        binary.SaveSqlite()
        li('[+] Sqlite Saved')
        bd = BD(args.old_file + ".sqlite", args.new_file + ".sqlite", args.local)
        bd.main()
    elif args.old_dir and args.new_dir:
        old_absdir = (os.path.abspath(args.old_dir))
        new_absdir = (os.path.abspath(args.new_dir))
        li("newdir:%s ; olddir:%s"%(old_absdir, new_absdir))
        matched_files, dismatched_files  = get_match_files(old_absdir, new_absdir)
        for file in matched_files:
            # step1 get ida pro pseudo code
            binary = B2S(os.path.join(old_absdir, file), os.path.join(new_absdir, file))
            binary.SaveSqlite()
            li('[+] Sqlite Saved')
            # step2 get result from database 
            bd = BD(os.path.join(old_absdir, file) + ".old.sqlite", os.path.join(new_absdir, file) + ".new.sqlite", args.local)
            bd.main()
            # ./new/aa
            # ./old/bb
    else:
        parser.print_help()
        sys.exit(1)




