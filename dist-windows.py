"""
Create a Windows executable using py2exe.
"""
from distutils.core import setup
import py2exe
import os
import sys
 
sys.argv.append('py2exe')
 
target_file = 'roguelike.py'
 
assets_dir = '.\\'
 
excluded_file_types = ['py', 'pyc', 'pyproj',
                       'sdf', 'sln', 'spec']

excluded_file_names = ['.gitattributes', '.gitignore', 'savegame']

excluded_directories = ['.git', '.vs']
 
def get_data_files(base_dir, target_dir, list=[]):
    """
    " * get_data_files
    " *    base_dir:    The full path to the current working directory.
    " *    target_dir:  The directory of assets to include.
    " *    list:        Current list of assets. Used for recursion.
    " *
    " *    returns:     A list of relative and full path pairs. This is 
    " *                 specified by distutils.
    """
    for file in os.listdir(base_dir + target_dir):
 
        full_path = base_dir + target_dir + file
        if os.path.isdir(full_path):
            if (file in excluded_directories):
                continue
            get_data_files(base_dir, target_dir + file + '\\', list)
        elif os.path.isfile(full_path):
            if (len(file.split('.')) == 2 and file.split('.')[1] in excluded_file_types):
                continue
            if (file in excluded_file_names):
                continue
            list.append((target_dir, [full_path]))
 
    return list
 
my_files = get_data_files(sys.path[0] + '\\', assets_dir)
 
opts = { 'py2exe': {
                    'ascii':'True',
                    'excludes':['_ssl','_hashlib'],
                    'includes' : ['anydbm', 'dbhash'],
                    'bundle_files':'1',
                    'compressed':'True'}}
 
setup(console=[target_file],
      data_files=my_files,
      zipfile=None,
      options=opts)