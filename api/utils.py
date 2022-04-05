from pathlib import Path
import os
import uuid
import datetime
from django.conf import settings
from dashboard.models import Folder,Slide

def convert_size_to_mb(sz):
    return str(round(sz / 1024 / 1024,2))+' MB'


def add_children(id):
    tree = []
    root_folders = Folder.objects.filter(Parent=id)
    for rf in root_folders:
        fld = {
            'id': rf.id,
            'text': rf.Name,
            'type': 'folder',
            'created_at': rf.Created.strftime("%Y-%m-%d"),
            'children': [],
        }
        rf.json = fld['children']
        stack = [rf]
    
        while len(stack) > 0:
            tp = stack.pop()

            #check instance of tp
            if isinstance(tp, Folder):             
                
                children_files = Slide.objects.filter(Folder=tp)
                for chld in children_files:
                    c = {
                        'id': chld.id,
                        'text': chld.Name,
                        'created_at': chld.InsertedDate.strftime("%Y-%m-%d"),
                        'created_by': chld.InsertedBy,
                        'case_no': chld.CaseNo,
                        'image_size': convert_size_to_mb(chld.Filesize),
                        'type': 'file',
                    }
                   
                    tp.json.append(c)
                    stack.append(chld)

                children = Folder.objects.filter(Parent=tp)
                if len(children) > 0:
                    for ch in children:
                        c = {
                            'id': ch.id,
                            'text': ch.Name,
                            'type': 'folder',
                            'children': [],
                        }
                        tp.json.append(c)
                        ch.json = c['children']
                        stack.append(ch)          

        tree.append(fld)

    root_files = Slide.objects.filter(Folder=id)
    for rf in root_files:
        fld = {
            'id': rf.id,
            'text': rf.Name,
            'created_at': rf.InsertedDate.strftime("%Y-%m-%d"),
            'created_by': rf.InsertedBy,
            'image_size': convert_size_to_mb(rf.Filesize),
            'case_no': rf.CaseNo,
            'type': 'file',
        }
        tree.append(fld)

    return tree

    
def get_folder_structure(user):
    main_list = []
    root_folders = Folder.objects.filter(Parent=None,  organization=user.organization_id)

    for rf in root_folders:
        fld = {
            'id': rf.id,
            'text': rf.Name,
            'type': 'folder',
            'created_at': rf.Created.strftime("%Y-%m-%d"),
            'children': [],
        }

        b = add_children(rf.id)
        fld['children'] = b
        main_list.append(fld)


    return main_list


# Helper functions
def _get_folder_size_and_count(pth, extension=None):
    root_directory = Path(pth)
    sz = 0
    count = 0
    for f in root_directory.glob('**/*'):
        if f.is_file():
            sz += f.stat().st_size
            if extension is not None:
                if str(f).split('.')[-1] == extension:
                    count += 1
            else:
                count += 1
    return (sz, count)

def _get_folder_size_word(pth, sz = None):
    if sz is None:
        sz = _get_folder_size_and_count(pth)[0]
    if sz < 1024:
        return str(round(sz, 1))+' B'
    sz = sz / 1024
    if sz < 1024:
        return str(round(sz, 1))+ ' KB'
    sz = sz / 1024
    if sz < 1024:
        return str(round(sz, 1))+ ' MB'
    sz = sz / 1024
    return str(round(sz, 1))+ ' GB'

def _get_file_size(pth):
    full_path = Path(os.path.join(settings.SLIDES_DIR, pth))
    if full_path.is_file():
        sz = full_path.stat().st_size
        words = _get_folder_size_and_count('.', sz)
        return (sz, words)
    return None
    

def _get_unique_filename(fn):
    us_exts = fn.split('.')
    us_old_name = us_exts[0]
    unique_filename = str(uuid.uuid4())
    us_new_name = us_old_name+'__'+unique_filename
    us_exts[0] = us_new_name
    us_full_name = '.'.join(us_exts)
    return us_full_name

def _get_iso_date(dt):
    if len(dt) == 0:
        return str(datetime.date.today())
    d = dt.split('/')
    return str(datetime.date(int(d[2]), int(d[0]), int(d[1])))

def _is_valid_date(dt):
    if type(dt) != str:
        return False
    parts = dt.split('/')
    if len(parts) != 3:
        return False
    for p in parts:
        if not p.isnumeric():
            return False
    return True 