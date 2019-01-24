import os
import sys
import shutil
import compileall

def release(dir):
    modify_lib_setup(dir)
    compileall.compile_dir(dir)
    move_pyc(dir)
    delete_dummy_files(dir)

def modify_lib_setup(dst):
    for sub in os.listdir(dst):
        subpath = os.path.sep.join([dst, sub])
        if os.path.isdir(subpath):
            modify_lib_setup(subpath)
        else:
            if sub == 'setup.py':
                content = open(subpath).read()
                content = content.replace('"*.pyc", ', '')
                open(subpath, 'w').write(content)

def move_pyc(dst):
    for sub in os.listdir(dst):
        subpath = os.path.sep.join([dst, sub])
        if os.path.isdir(subpath):
            if sub == 'workspace':
                continue
            if sub == '__pycache__':
                for pyc in os.listdir(subpath):
                    srcfile = os.path.sep.join([dst, sub, pyc])
                    dstfile = os.path.sep.join([dst, pyc.replace('.cpython-35.pyc', '.pyc')])
                    shutil.move(srcfile, dstfile)
            else:
                move_pyc(subpath)

def delete_dummy_files(dst, suffix='.py'):
    for sub in os.listdir(dst):
        subpath = os.path.sep.join([dst, sub])
        if os.path.isdir(subpath):
            if sub == 'workspace':
                delete_dummy_files(subpath, suffix='pyc')
                continue
            
            if sub == '.git':
                os.system('rd /s/q '+subpath)
                
            elif sub == '__pycache__':
                shutil.rmtree(subpath, ignore_errors=False)
                
            else:
                delete_dummy_files(subpath, suffix=suffix)
                			
        else:
            if sub == 'setting.py' and dst[dst.rfind(os.path.sep)+1:] == 'device':
                continue
                    
            if sub.endswith(suffix):
                os.remove(subpath)
                
def getAtideDir():
    execfilepath = os.path.abspath(sys.argv[0])
    toos_execdirpath = execfilepath[:execfilepath.rfind(os.path.sep)]
    atide_execdirpath = toos_execdirpath[:toos_execdirpath.rfind(os.path.sep)]
    return atide_execdirpath

if __name__ == '__main__':
    release(getAtideDir())
    print('well done!')