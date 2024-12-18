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
    def __init__(self, old, new, file_path) -> None:
        self.old = old
        self.new = new
        self.file_path = file_path
    
    def GetConfig(self):
        self.config = configparser.ConfigParser()
        self.config.read(current_path + "/setting.cfg")
        return self.config
    
    def ExecuteCommand(self, ida_path, i):
        command = [
            ida_path,
            "-A",
            "-B",
            "-S" + current_path + "/diaphora/diaphora.py",
            i
        ]
        sqlite_name = i + ".sqlite"
        os.environ['DIAPHORA_AUTO'] = "1"
        os.environ['DIAPHORA_EXPORT_FILE'] = sqlite_name
        li(f"{i}(binary) to {sqlite_name}")
        li("[*] watting")
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stdout)


    def SaveSqlite(self):
        self.GetConfig()
        ida_path = self.config['ida_path']['path']
        FileName = [self.old, self.new]
        li('[*] Multi-process startup')
        with concurrent.futures.ProcessPoolExecutor(max_workers = 2) as executor:
            futures = [executor.submit(self.ExecuteCommand, ida_path, i) for i in FileName]

            for future in concurrent.futures.as_completed(futures):
                future.result()  
        
        command = [
            sys.executable,
            current_path + "/diaphora/diaphora.py",
            self.old + ".sqlite",
            self.new + ".sqlite",
            "-o",
            self.file_path + "/output.sqlite"
        ]
        print(command)
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stdout)
        
# BinaryDiff
class BD():
    def __init__(self, old, new) -> None:
        self.old = old
        self.new = new
        self.file_name = os.path.dirname(os.path.abspath(self.old)) + '/' + os.path.basename(old) + '-' + os.path.basename(new) + ".diff"
        self.out_path = os.path.dirname(os.path.abspath(self.old))
        self.output = self.out_path + "/output.sqlite"
    
    def SqliteOutput(self, file_name, sql):
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
    
    def NewFuncDiff(self):
        primary_unmatch = self.SqliteOutput(self.output, "select address, name from unmatched where type = 'primary'")
        li("[+] Newly added functions")
        for row in primary_unmatch:
            address, name = row
            print(address + ' | ' + name)

            functions = self.SqliteOutput(self.new, f"select prototype, pseudocode from functions where address = 0x{address}")
            prototype, pseudocode = functions[0]
            if not prototype:
                break
            pp = prototype + pseudocode
            Func_diff = self.UpdateDict(name, None, None, pp)

            diff = difflib.unified_diff(Func_diff['old'].splitlines(), Func_diff['new'].splitlines(), fromfile=name, tofile=name, lineterm='')
            # for line in diff:
            #     print(line, end='\n')
            with open(f'{self.file_name}', 'a+') as file:
                for line in diff:
                    file.write(f'{line}\n')  
        
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
            Func_diff = self.UpdateDict(name, None, None, pp)

            diff = difflib.unified_diff(Func_diff['new'].splitlines(), Func_diff['old'].splitlines(), fromfile=name, tofile=name, lineterm='')
            # for line in diff:
            #     print(line, end='\n')
            with open(f'{self.file_name}', 'a+') as file:
                for line in diff:
                    file.write(f'{line}\n')
    
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
            Func_diff = self.UpdateDict(name, name2, pp1, pp2)

            diff = difflib.unified_diff(Func_diff['old'].splitlines(), Func_diff['new'].splitlines(), fromfile=name, tofile=name2, lineterm='')
            with open(f'{self.file_name}', 'a+') as file:
                for line in diff:
                    file.write(f'{line}\n')
    
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
        desc = B2S.GetConfig(self)
        self.gist_desc = desc['gist']['desc']
        self.PartialDiff()
        self.MultimatchDiff()
        self.NewFuncDiff()
        self.GistUpload()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Diff old_file and new_file.')
    
    parser.add_argument('--old', type=str, help='The old file')
    parser.add_argument('--new', type=str, help='The new file')

    args = parser.parse_args()

    if args.old is None and args.new is None:
        parser.print_help()
        sys.exit(1)
    elif args.old is None or args.new is None:
        print("Error: Both --old and --new parameters are required.")
        parser.print_help()
        sys.exit(1)
    
    file_path = os.path.dirname(os.path.abspath(args.old))
    binary = B2S(args.old, args.new, file_path)
    binary.SaveSqlite()
    li('[+] Sqlite Saved')
    bd = BD(args.old + ".sqlite", args.new + ".sqlite")
    bd.main()

