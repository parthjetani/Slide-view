from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.db.models import Q
from django.forms.models import model_to_dict
from authentication.models import CustomUser

from dashboard.models import Folder, Slide, Activity, Annotation
from dashboard.forms import SlideForm
from .utils import get_folder_structure


import sys
import psutil
from pathlib import Path
import datetime
import os
import shutil
import json

from api.utils import _get_folder_size_and_count, _get_folder_size_word, _get_file_size, _get_unique_filename, _get_iso_date, _is_valid_date

# Create your views here.

upload_progress = None

@login_required
@require_GET
def index(request):
    JsonResponse({
        'message': 'Slide Management API',
        'type': 'success'
    })


@login_required
@require_GET
def storage_info(request):
    data = {}
    # Get storage data
    # Check storage for other platforms
    base_path = '/'
    if sys.platform != 'linux':
        base_path = 'C:/'
    disk_usage = psutil.disk_usage(base_path)
    data['disk_usage'] = disk_usage
    data['folders'] = []
    media_folder = settings.BASE_DIR+'/media/slides'
    all_folder = Folder.objects.filter(Parent=None)
    total = 0
    for fld in all_folder:
        fld_pth = media_folder+'/'+fld.Name
        sz = [0, 0]
        stack = [fld]
        count = 0
        while len(stack) > 0:
            tp = stack.pop()
            # Get all files in this folder
            files = Slide.objects.filter(Folder=tp)
            for f in files:
                sz[0] += f.Filesize
                count += 1
            children = Folder.objects.filter(Parent=tp)
            for c in children:
                stack.append(c)

        total += sz[0]
        data['folders'].append(
            (fld.Name, _get_folder_size_word(fld_pth, sz[0]), count))
    cache_folder = settings.BASE_DIR+'/static/dzi'
    cache_folder_size = _get_folder_size_and_count(
        cache_folder, extension='dzi')
    data['folders'].append(('Cache', _get_folder_size_word(
        cache_folder, cache_folder_size[0]), cache_folder_size[1]))

    label_folder = settings.BASE_DIR+'/static/images/labels'
    label_folder_size = _get_folder_size_and_count(label_folder)
    data['folders'].append(('Labels', _get_folder_size_word(
        label_folder, label_folder_size[0]), label_folder_size[1]))

    total += label_folder_size[0]
    total += cache_folder_size[0]
    other_size = data['disk_usage'][1] - total
    data['other'] = _get_folder_size_word('.', other_size)
    data['total'] = _get_folder_size_word('.', data['disk_usage'][0])

    return JsonResponse(data)


# @login_required
# @require_GET
# def folder_edit(request):
#     print(request.POST)
#     folder_id = request.POST.get('folder_id', '')
#     print(folder_id)
#     message = {'type':'success'}
#     return JsonResponse(message)


@login_required
@require_GET
def folder_structure(request):
    user = CustomUser.objects.get(user = request.user)
    node = request.GET.get('node', '')
    data = {
        'folders': [
            {
                'id': 'fld_0',
                'text': 'Slides',
                'type': 'folder',
                'children': [],
                'state': {
                    'opened': len(node) == 0,
                    'selected': len(node) == 0
                }
            }
        ]
    }

    root_folders = Folder.objects.filter(Parent=None, organization=user.organization_id)
    for rf in root_folders:
        fld = {
            'id': 'fld_'+str(rf.id),
            'text': rf.Name,
            'type': 'folder',
            'children': [],
            'state': {
                'opened': node == 'fld_'+str(rf.id),
                'selected': node == 'fld_'+str(rf.id)
            }
        }
        rf.json = fld['children']
        stack = [rf]
        while len(stack) > 0:
            tp = stack.pop()
            children = Folder.objects.filter(Parent=tp, organization=user.organization_id)
            for chld in children:
                c = {
                    'id': 'fld_'+str(chld.id),
                    'text': chld.Name,
                    'type': 'folder',
                    'children': [],
                    'state': {
                        'opened': node == 'fld_'+str(chld.id),
                        'selected': node == 'fld_'+str(chld.id)
                    }
                }
                chld.json = c['children']
                tp.json.append(c)
                stack.append(chld)
        data['folders'][0]['children'].append(fld)

    data['type'] = 'success'
    return JsonResponse(data)


@login_required
def folder_structure_for_my_folder(request):
    user = CustomUser.objects.get(user = request.user)
    data = {}
    folderStructure = get_folder_structure(user)
    data['folder'] = folderStructure
    return JsonResponse(data)


def convert_size_to_mb(sz):
    return str(round(sz / 1024 / 1024,2))+' MB'

@login_required
def only_folder(request):
    user = CustomUser.objects.get(user = request.user)
    data = {}
    main_list = []
    root_folders = Folder.objects.filter(Parent=None, organization=user.organization_id)

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

            if isinstance(tp, Folder):             
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

        main_list.append(fld)
    data['folder'] = main_list
    return JsonResponse(data)


@login_required
def cases(request):
    user = CustomUser.objects.get(user = request.user)
    main_list = []
    root_folders = Folder.objects.filter(Parent=None, organization=user.organization_id)
    for rf in root_folders:
        sub_folder = Folder.objects.filter(Parent=rf.id, organization=user.organization_id)
        for sb in sub_folder:
            fld = {
                'id': sb.id,
                'text': sb.Name,
                'type': 'folder',
                'created_at': sb.Created.strftime("%Y-%m-%d"),
                'children': [],
            }
            sb.json = fld['children']
            stack = [sb]
        
            while len(stack) > 0:
                tp = stack.pop()
                if isinstance(tp, Folder):             
                    children_files = Slide.objects.filter(Folder=tp, organization=user.organization_id)
                    for chld in children_files:
                        c = {
                            'id': chld.id,
                            'text': chld.Name,
                            'folder': chld.Folder.Name,
                            'created_at': chld.InsertedDate.strftime("%Y-%m-%d"),
                            'created_by': chld.InsertedBy,
                            'case_no': chld.CaseNo,
                            'image_size': convert_size_to_mb(chld.Filesize),
                            'type': chld.get_SlideType_display(),
                        }
                        main_list.append(c)
                        stack.append(chld)

                    children = Folder.objects.filter(Parent=tp, organization=user.organization_id)
                    if len(children) > 0:
                        for ch in children:
                            c = {
                                'id': ch.id,
                                'text': ch.Name,
                                'type': 'folder',
                                'children': [],
                            }
                            ch.json = c['children']
                            stack.append(ch)          
            
        root_files = Slide.objects.filter(Folder=rf.id, organization=user.organization_id)
        for rf in root_files:
            fld = {
                'id': rf.id,
                'text': rf.Name,
                'folder': rf.Folder.Name,
                'created_at': rf.InsertedDate.strftime("%Y-%m-%d"),
                'created_by': rf.InsertedBy,
                'image_size': convert_size_to_mb(rf.Filesize),
                'case_no': rf.CaseNo,
                'type': rf.get_SlideType_display(),
            }
            main_list.append(fld)
    
    count = 1
    tmp = []
    for item in main_list:
        item['sn_no'] = count
        count += 1
        tmp.append(item)

    return render(request, 'cases.html', {'main_list':tmp})

@login_required
def only_slide(request, pk=None):
    user = CustomUser.objects.get(user = request.user)
    main_list = []
    root_folders = Folder.objects.get(id=pk, organization=user.organization_id)
    children_files = Slide.objects.filter(Folder=root_folders, organization=user.organization_id)
    for chld in children_files:
        c = {
            'id': chld.id,
            'text': chld.Name,
            'folder': chld.Folder.Name,
            'created_at': chld.InsertedDate.strftime("%Y-%m-%d"),
            'created_by': chld.InsertedBy,
            'case_no': chld.CaseNo,
            'image_size': convert_size_to_mb(chld.Filesize),
            'type': chld.get_SlideType_display(),
        }
        main_list.append(c)
    count = 1
    tmp = []
    for item in main_list:
        item['sn_no'] = count
        count += 1
        tmp.append(item)

    return render(request, 'only_slide.html', {'main_list':tmp})

@login_required
@require_POST
def folder_create(request):
    user = CustomUser.objects.get(user = request.user)
    folder_name = request.POST['folder_name'].strip()
    data = {}
    parent_id = int(request.POST['parent_id'])
    if len(folder_name) == 0:
        data['type'] = 'fail'
        data['message'] = 'Folder name cannot be empty'
        return JsonResponse(data)
    if parent_id == 0:
        parent_id = None

    # Check if Folder name exists within this parent
    folders = Folder.objects.filter(Parent=parent_id)
    for fld in folders:
        if fld.Name == folder_name:
            data['type'] = 'fail'
            data['message'] = 'Folder already exists'
            return JsonResponse(data)
    if parent_id is not None:
        parent = Folder.objects.get(pk=parent_id)
        fld = Folder(Name=folder_name, Parent=parent, organization=user.organization_id)
        fld.save()
    else:
        fld = Folder(Name=folder_name, organization=user.organization_id)
        fld.save()
    return JsonResponse({'type': 'success', 'message': 'Folder successfully created'})

@login_required
@require_POST
def folder_search(request):
    folder_name = request.POST['folder_name'].strip()
    data = {}
    if len(folder_name) == 0:
        
        data['folders'] = list(Folder.objects.all().values())
        data['type'] = 'success'
        data['message'] = ''
        return JsonResponse(data)
    else:

        try:
            folders = Folder.objects.filter(Name__contains=folder_name).values()
            data['folders'] = list(folders)
            data['type'] = 'success'
            data['message'] = ''
            return JsonResponse(data)
        
        except Exception as e:
            
            data['type'] = 'fail'
            data['message'] = e
            return JsonResponse(data)



    # Check if Folder name exists within this parent
    folders = Folder.objects.filter(Parent=parent_id)

@login_required
@require_GET
def folder_content(request):
    user = CustomUser.objects.get(user=request.user)
    data = {
        'type': 'fail',
        'message': '',
        'data': []
    }
    folder_id = request.GET.get('folder_id', None)
    if folder_id == '0':
        folder_id = None
    folders = []
    files = []
    parent = None
    try:
        if folder_id is None:
            folders = Folder.objects.filter(Parent=None, organization=user.organization_id)
        else:
            parent = Folder.objects.get(pk=folder_id, organization=user.organization_id)
            folders = Folder.objects.filter(Parent=parent, organization=user.organization_id)
            files = Slide.objects.filter(Folder=parent, organization=user.organization_id)
    except (Folder.DoesNotExist, Slide.DoesNotExist):
        data['message'] = 'Invalid folder'
        return JsonResponse(data)
    data['type'] = 'success'
    if parent is not None:
        parent = parent.Parent
        if parent is not None:
            data['data'].append({
                'name': {
                    'name': '..',
                    'type': 'folder',
                    'id': parent.id
                },
                'created': parent.Created,
                'tag': '',
                'cached': '',
                'id': {
                    'type': 'folder',
                    'id': parent.id,
                    'name': parent.Name
                }
            })
        else:
            data['data'].append({
                'name': {
                    'name': '..',
                    'type': 'folder',
                    'id': 0
                },
                'created': '2021/02/01',
                'tag': '',
                'cached': '',
                'id': {
                    'type': 'folder',
                    'id': 0,
                    'name': '..'
                }
            })
    for fld in folders:
        data['data'].append({
            'name': {
                'name': fld.Name,
                'type': 'folder',
                'id': fld.id
            },
            'created': fld.Created,
            'tag': '',
            'cached': '',
            'id': {
                'type': 'folder',
                'id': fld.id,
                'name': fld.Name
            }
        })

    for fl in files:
        sz = _get_folder_size_word('.', fl.Filesize)
        cached = False
        try:
            ac = Activity.objects.get(pk=fl)
            cached = ac.Saved
        except:
            pass
        data['data'].append({
            'name': {
                'name': fl.Name,
                'size': sz,
                'type': 'file',
                'id': fl.id,
            },
            'created': fl.ScannedDate,
            'tag': fl.Tag,
            'cached': cached,
            'id': {
                'type': 'file',
                'id': fl.id,
                'name': fl.Name
            }
        })
    return JsonResponse(data)


@login_required
@require_GET
def folder_delete(request):
    data = {
        'type': 'fail',
        'message': ''
    }
    if 'folder_id' not in request.GET:
        data['message'] = 'Invalid Folder'
        return JsonResponse(data)
    try:
        folder = Folder.objects.get(pk=request.GET['folder_id'])
    except:
        data['message'] = 'Folder does not exists'
        return JsonResponse(data)
    # Check if folder contains folders
    empty = True
    child_folders = Folder.objects.filter(Parent=folder)
    empty = len(child_folders) == 0
    
    if empty:
        child_files = Slide.objects.filter(Folder=folder)
        empty = len(child_files) == 0
        
    if empty:
        folder.delete()
        data['type'] = 'success'
        return JsonResponse(data)
    else:
        data['message'] = 'Folder not empty'
        return JsonResponse(data)


@login_required
@require_GET
def file_delete(request):
    data = {
        'type': 'fail',
        'message': ''
    }
    if 'file_id' not in request.GET:
        data['message'] = 'Invalid file'
        return JsonResponse(data)
    try:
        slide = Slide.objects.get(pk=request.GET['file_id'])
    except:
        data['message'] = 'File not found'
        return JsonResponse(data)

    # Check if file is a copy of something
    if slide.CopyOf is not None:
        # if it is then delete
        slide.delete()
        data['type'] = 'success'
        return JsonResponse(data)
    # If it is original
    # Find all copies
    copies = Slide.objects.filter(CopyOf=slide)
    # if no copies then delete the slide itself and the label
    if len(copies) == 0:
        # delete the slide file and the cache
        try:
            slide_file = Path(os.path.join(settings.SLIDES_DIR, slide.UrlPath))
            slide_file.unlink()
        except:
            pass
        # Check if label file is placeholder
        label_path = slide.LabelUrlPath
        filename = label_path.split('/')[-1]
        if filename != 'placeholder.png':
            # delete this file
            try:
                label_file = Path(os.path.join(
                    settings.LABELS_DIR, slide.LabelUrlPath))
                label_file.unlink()
            except:
                pass
        # Check if cache exists
        if os.path.exists(os.path.join(settings.STATIC_DIR, 'dzi', str(slide.id)+'.dzi')):
            Path(os.path.join(settings.STATIC_DIR,
                              'dzi', str(slide.id)+'.dzi')).unlink()
            shutil.rmtree(os.path.join(settings.STATIC_DIR,
                                       'dzi', str(slide.id)+'_files'))
        slide.delete()
        data['type'] = 'success'
        return JsonResponse(data)

    # If copies exists
    if len(copies) == 1:
        copies[0].CopyOf = None
        copies[0].save()
    else:
        first_copy = copies[0]
        copies[0].CopyOf = None
        copies[0].save()
        for i in range(1, len(copies)):
            copies[i].CopyOf = first_copy
            copies[i].save()
    slide.delete()
    data['type'] = 'success'
    return JsonResponse(data)


@login_required
def bulk_files_delete(request):
    if request.method == 'POST':
        data = {
            'type': 'fail',
            'message': ''
        }

        files_ids = json.loads(request.POST.get('files_ids'))
        print(files_ids)

        for file_id in files_ids:
            try:
                slide = Slide.objects.get(pk=int(file_id))
                slide.delete()
                data['type'] = 'success'
                data['message'] = 'Files deleted'
            except:
                data['type'] = 'fail'
                data['message'] = f'File with id {file_id} not found'
                return JsonResponse(data)

        return JsonResponse(data)
        

@login_required
@require_GET
def file_copy(request):
    data = {
        'type': 'fail',
        'message': ''
    }
    if 'file_id' not in request.GET:
        data['message'] = 'Invalid file'
        return JsonResponse(data)
    try:
        slide = Slide.objects.get(pk=request.GET['file_id'])
    except:
        data['message'] = 'File not found'
        return JsonResponse(data)

    if 'folder_id' not in request.GET:
        data['message'] = 'Invalid folder'
        return JsonResponse(data)
    try:
        folder = Folder.objects.get(pk=request.GET['folder_id'])
    except:
        data['message'] = 'Folder not found'
        return JsonResponse(data)
    slidename = request.GET.get('slidename', '')
    if len(slidename) == 0:
        data['message'] = 'Invalid file name'
        return JsonResponse(data)
    # Check if file exists with samename
    other_slides = Slide.objects.filter(Name=slidename, Folder=folder)
    if len(other_slides) != 0:
        data['message'] = 'File already exists'
        return JsonResponse(data)

    new_copy = Slide(Name=slidename, 
                    ScannedBy=slide.ScannedBy, 
                    ScannedDate=slide.ScannedDate, 
                    InsertedBy=slide.InsertedBy, 
                    InsertedDate=slide.InsertedDate, 
                    SlideType=slide.SlideType, 
                    UrlPath=slide.UrlPath,
                    LabelUrlPath=slide.LabelUrlPath, 
                    Group=slide.Group, 
                    GroupName=slide.GroupName, 
                    Annotations=slide.Annotations, 
                    Folder=folder, 
                    Filesize=slide.Filesize, 
                    Tag=slide.Tag, 
                    CopyOf=slide)
    new_copy.save()
    data['type'] = 'success'
    return JsonResponse(data)


@login_required
@require_GET
def folder_parents(request):
    data = {
        'type': 'fail',
        'message': ''
    }
    if 'folder_id' not in request.GET:
        data['message'] = 'Invalid Folder'
        return JsonResponse(data)

    folder_id = request.GET.get('folder_id', '0')
    parents = []
    print('Folder ID received: '+folder_id)
    try:
        folder = Folder.objects.get(pk=folder_id)
        while folder is not None:
            parents.insert(0, folder.Name)
            folder = folder.Parent
    except Folder.DoesNotExist:
        data['message'] = 'Invalid Folder'
        return JsonResponse(data)
    data['type'] = 'success'
    data['parents'] = parents
    return JsonResponse(data)


@login_required
@require_GET
def file_exist(request):
    data = {
        'type': 'fail',
        'message': '',
        'response': False
    }
    if 'folder_id' not in request.GET:
        data['message'] = 'Invalid folder'
        return JsonResponse(data)

    if 'slidename' not in request.GET:
        data['message'] = 'Provide slidename'
        return JsonResponse(data)

    try:
        parent = Folder.objects.get(pk=request.GET['folder_id'])
    except:
        data['message'] = 'Invalid folder'
        return JsonResponse(data)

    data['type'] = 'success'
    slds = Slide.objects.filter(Folder=parent)
    for s in slds:
        if s.Name == request.GET['slidename']:
            data['response'] = True
            return JsonResponse(data)
    data['response'] = False
    return JsonResponse(data)


@login_required
@require_GET
def valid_filename(request):
    data = {
        'type': 'fail',
        'message': '',
        'response': False
    }
    if 'filename' not in request.GET:
        data['message'] = 'Provide filename'
        return JsonResponse(data)
    data['type'] = 'success'
    exts = request.GET['filename'].split('.')
    if len(exts) == 1:
        data['response'] = True
        return JsonResponse(data)
    ext = exts[-1]
    for e in settings.VALID_SLIDE_EXT:
        if ext.lower() == e:
            data['response'] = True
            return JsonResponse(data)
    return JsonResponse(data)


@login_required
@require_POST
def slide_upload(request):
    user = CustomUser.objects.get(user = request.user)
    slide_form = SlideForm(request.POST, request.FILES)
    data = {
        'type': 'fail'
    }
    print("Slide upload started")
    if slide_form.is_valid():
        upload_progress = 0
        print('Form valid')
        today_folder_name = datetime.datetime.now().strftime('%d-%m-%Y')
        today_folder = os.path.join(settings.SLIDES_DIR, today_folder_name)

        # Validations

        # Check if parent folder exists
        parent_id = request.POST['parent']
        try:
            parent = Folder.objects.get(pk=parent_id, organization=user.organization_id)
        except Folder.DoesNotExist:
            data['message'] = 'Invalid folder'
            upload_progress = None
            return JsonResponse(data)

        # Check if parent folder contains file with same name
        slds = Slide.objects.filter(Folder=parent, organization=user.organization_id)
        for s in slds:
            if s.Name == request.POST['slidename']:
                data['message'] = 'File exists'
                upload_progress = None
                return JsonResponse(data)

        if not os.path.exists(today_folder):
            os.mkdir(today_folder)
        uploaded_slide = request.FILES['slide_upload']
        uploaded_label = request.FILES['label_upload'] if 'label_upload' in request.FILES else '/static/images/placeholder.png'
        us_full_name = _get_unique_filename(uploaded_slide.name)

        # Check if file is of valid ext
        exts = uploaded_slide.name.split('.')
        valid_ext = False
        if len(exts) != 1:
            ext = exts[-1]
            for e in settings.VALID_SLIDE_EXT:
                if ext.lower() == e:
                    valid_ext = True
                    break

        if not valid_ext:
            data['message'] = 'Slide not supported'
            return JsonResponse(data)

        with open(os.path.join(today_folder, us_full_name), 'wb+') as us_dest:
            count = 1
            for chunk in uploaded_slide.chunks():                
                count += 1
                us_dest.write(chunk)

        label_location = '/static/images/placeholder.png'
        if 'label_upload' in request.FILES:
            ul_full_name = _get_unique_filename(uploaded_label.name)
            label_location = '/static/images/labels/'+ul_full_name
            with open(os.path.join(settings.LABELS_DIR, ul_full_name), 'wb+') as dest:
                for chunk in uploaded_label.chunks():
                    dest.write(chunk)


        sld = Slide(
            SlideType=request.POST['slide_type'],
            Name=request.POST['slidename'],
            ScannedBy=request.POST['scanned_by'],
            ScannedDate=_get_iso_date(request.POST['scanned_date']),
            InsertedBy=request.POST['inserted_by'],
            InsertedDate=_get_iso_date(request.POST['inserted_date']),
            UrlPath=today_folder_name+'/'+us_full_name,
            LabelUrlPath=label_location,
            Annotations='annotations' in request.POST,
            Folder=parent,
            Filesize=Path(os.path.join(
                today_folder, us_full_name)).stat().st_size,
            Tag='',
            CaseNo=request.POST.get('case_no', "CASE_NO"),
            organization=user.organization_id,
        )
        sld.save()
        upload_progress = None
        return JsonResponse({'type': 'success'})

    else:
        print('Invalid form')
        data['errors'] = list(slide_form.errors.items())
        for field, errors in slide_form.errors.items():
            print('Field')
            print(field)
            for error in errors:
                print(error)
    return JsonResponse(data)


@login_required
@require_GET
def folder_get(request):
    data = {
        'type': 'fail',
        'message': ''
    }
    if 'folder_id' not in request.GET:
        data['message'] = 'Invalid folder'
        return JsonResponse(data)

    try:
        folder = Folder.objects.get(pk=request.GET['folder_id'])
        data['folder'] = {
            'Name': folder.Name,
            'id': folder.id
        }
        data['type'] = 'success'
        return JsonResponse(data)
    except Folder.DoesNotExist:
        data['message'] = 'Folder not found'
        return JsonResponse(data)


@login_required
@require_POST
def folder_edit(request):
   
    data = {
        'type': 'fail',
        'message': ''
    }
    if 'folder_id' not in request.POST or 'folder_name' not in request.POST:
        data['message'] = 'Please provide folder name and id'
        return JsonResponse(data)
    folder_id = request.POST['folder_id']
    folder_name = request.POST['folder_name']
    try:
        folder = Folder.objects.get(pk=folder_id)
    except Folder.DoesNotExist:
        data['message'] = 'Folder does not exist'
        return JsonResponse(data)
    other_folders = Folder.objects.filter(
        Name=folder_name, Parent=folder.Parent)
    if len(other_folders) == 0:
        folder.Name = folder_name
        folder.save()
        data['type'] = 'success'
        return JsonResponse(data)
    else:
        data['message'] = 'Folder already exists'
        return JsonResponse(data)


@login_required
@require_GET
def file_get(request):
    user = CustomUser.objects.get(user = request.user)
    data = {
        'type': 'fail',
        'message': ''
    }
    if 'slide_id' not in request.GET:
        data['message'] = 'Slide not found'
        return JsonResponse(data)
    try:
        slide = Slide.objects.get(pk=request.GET['slide_id'], organization=user.organization_id)
    except:
        data['message'] = 'Slide not found'
        return JsonResponse(data)
    slide_data = {}
    slide_data['id'] = slide.id
    slide_data['Name'] = slide.Name
    slide_data['ScannedBy'] = slide.ScannedBy
    slide_data['InsertedBy'] = slide.InsertedBy
    slide_data['SlideType'] = slide.SlideType
    slide_data['ScannedDate'] = slide.ScannedDate.strftime('%m/%d/%Y')
    slide_data['InsertedDate'] = slide.InsertedDate.strftime('%m/%d/%Y')
    slide_data['annotations'] = slide.Annotations
    slide_data['CaseNo'] = slide.CaseNo
    data['slide'] = slide_data
    data['type'] = 'success'
    return JsonResponse(data)


@login_required
@require_POST
def file_edit(request):
    slide_id = request.POST.get('id', '')
    data = {
        'type': 'fail',
        'message': '',
        'errors': []
    }
    try:
        slide = Slide.objects.get(pk=slide_id)
    except:
        data['message'] = 'Slide not found'
        return JsonResponse(data)
    # Input validations
    # Slidename
    # Required
    err = {'name': 'slidename', 'message': ''}
    if 'slidename' not in request.POST or len(request.POST['slidename'].strip()) == 0:
        err['message'] = 'Please provide Slide Name'
        data['errors'].append(err)
    slidename = request.POST['slidename'].strip()
    try:
        slide = Slide.objects.get(pk=request.POST['id'])
    except:
        data['message'] = 'Slide Not found'
        return JsonResponse(data)
    other_slides = Slide.objects.filter(
        Name=slidename, Folder=slide.Folder).exclude(id=slide.id)

    if len(other_slides) != 0:
        err['message'] = 'Slide Name already exists'
        data['errors'].append(err)

    err = {'name': 'scanned_date'}
    if 'scanned_date' in request.POST:
        if not _is_valid_date(request.POST['scanned_date']):
            err['message'] = 'Invalid date'
            data['errors'].append(err)

    err = {'name': 'inserted_date'}
    if 'inserted_date' in request.POST:
        if not _is_valid_date(request.POST['inserted_date']):
            err['message'] = 'Invalid date'
            data['errors'].append(err)

    err = {'name': 'slide_type'}
    if 'slide_type' not in request.POST:
        err['message'] = 'Please provide slide type'
        data['errors'].append(err)
    else:
        valid = False
        for vs in settings.VALID_SLIDE_TYPE:
            if request.POST['slide_type'] == vs[0]:
                valid = True
        if not valid:
            err['message'] = 'Please provide a valid slide type'
            data['errors'].append(err)

    if len(data['errors']) == 0:
        slide.Name = slidename
        slide.ScannedBy = request.POST['scanned_by']
        slide.ScannedDate = _get_iso_date(request.POST['scanned_date'])
        slide.InsertedBy = request.POST['inserted_by']
        slide.InsertedDate = _get_iso_date(request.POST['inserted_date'])
        slide.SlideType = request.POST['slide_type']
        slide.CaseNo = request.POST['case_no']
        slide.Annotations = 'annotations' in request.POST
        slide.save()
        data['type'] = 'success'
    return JsonResponse(data)

from django.template.loader import render_to_string
from django.views import View

class SlidesView(View):
    def post(self, request, *args, **kwargs):
        action = kwargs.get('action')
        if action == 'delete':
            ids = request.POST.getlist('slides')
            Slide.objects.filter(pk__in=ids).delete()
            ctx ={
                "type":"success",
                "slides":Slide.objects.filter()
            }
            ctx['slides'] = render_to_string('slides/slide-list.html', ctx)
            return JsonResponse(ctx, status=200)
        if action == 'search':
            ctx ={
                "type":"success",
                "slides":Slide.objects.filter(Name__icontains=request.POST.get('folder_name'))
            }
            ctx['slides'] = render_to_string('slides/slide-list.html', ctx)
            return JsonResponse(ctx, status=200)
