import os
from slide_management.settings import PATHHUB_REST_PASSWORD
import time
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler
import shutil
from pathlib import Path
import threading
from enum import Enum
import copy
from dashboard.models import Folder, Slide, Activity, Annotation
from django.conf import settings
import datetime
from api.utils import _get_folder_size_and_count, _get_folder_size_word, _get_file_size, _get_unique_filename, _get_iso_date, _is_valid_date
# import requests
# from requests.auth import HTTPBasicAuth

TIMEOUT = 5*60*60 # 5 hours
SINGFILE_IMAGE = ['svs', 'tif', 'ndpi', 'scn', 'tiff', 'bif', 'dcm', 'dcim']
MULTIFILE_IMAGE = ['vms', 'vmu', 'mrxs']

HEADERS = {
    'Content-Type': 'application/json',
    'X-API-KEY': settings.PATHHUB_REST_PASSWORD,
    'Accpet': 'application/json',
    'Origin': 'https://'+settings.ALLOWED_HOSTS[0],
    'Access-Control-Request-Method': 'POST',
    "X-Requested-With": "XMLHttpRequest"
}
# Check if FTP folder exists in database
folders = Folder.objects.filter(Parent=None)
ftp_exists = False
DB_FLD = None
for fld in folders:
    if fld.Name == 'FTP':
        ftp_exists = True
        DB_FLD = fld
        break

if not ftp_exists:
    fld = Folder(Name='FTP')
    fld.save()
    DB_FLD = fld

print("DB FOLDER: ")
print(DB_FLD)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'



class Status(Enum):
    RUNNING = 0
    COMPLETED = 1
    ERROR = 2

class Pool:
    def __init__(self) -> None:
        self.files = {}
        self.lock = threading.Lock()
        self.isEmpty = True
    
    def add(self, path, status):
        self.lock.acquire()
        try:
            self.isEmpty = False
            self.files[path] = status
        finally:
            self.lock.release()
    
    def checkRunning(self):
        self.lock.acquire()
        try:
            for path, status in self.files.items():
                if status == Status.RUNNING:
                    return True
            return False
        finally:
            self.lock.release()

    def getFiles(self):
        # Return a copy of self.files
        self.lock.acquire()
        try:
            return copy.deepcopy(self.files)
        finally:
            self.lock.release()
    
    def emptyFiles(self):
        self.lock.acquire()
        try:
            self.isEmpty = True
            self.files = {}
        finally:
            self.lock.release()

    def isFilesEmpty(self):
        return self.isEmpty

class ThreadPoolWait(threading.Thread):
    def __init__(self, pool, dir):
        threading.Thread.__init__(self)
        self.pool = pool
        self.killed = False
        self.dir = dir
    
    def kill(self):
        self.killed = True
    
    def uploadSlide(self, path, fld):
        print("Uploading slide "+path+"  To folder: "+fld.Name)
        ext = Path(path).suffix
        if len(ext) > 1:
            ext = ext[1:]
        
        slide_name = os.path.basename(path)
        res = Slide.objects.filter(Name=slide_name, Folder=fld)
        if len(res) > 0:
            print("Slide exits returning")
            return

        today_folder_name = datetime.datetime.now().strftime('%d-%m-%Y')
        today_folder = os.path.join(settings.SLIDES_DIR, today_folder_name)
        if not os.path.exists(today_folder):
            os.mkdir(today_folder)
        # Get file extension from path
        ext = Path(path).suffix[1:]
        slide_type = 2
        if ext in ['dcm', 'dcim', 'DCM', 'DCIM']:
            slide_type = 1
        us_full_name = slide_name
        label_location = '/static/images/placeholder.png'
        if ext in SINGFILE_IMAGE:
            print("Single image type file")
            retry = 0
            while retry < 5:
                try:
                    print("Copying file retry "+str(retry))
                    shutil.copyfile(path, os.path.join(today_folder, us_full_name))
                    break
                except Exception as e:
                    print("Copy failed")
                    print(e)
                    time.sleep(4)
                    retry += 1
            print("Processing {}".format(path))
        if ext in MULTIFILE_IMAGE:
            print("Multi file image type")
            retry = 0
            while retry < 5:
                try:
                    print("Copying file retry "+str(retry))
                    shutil.copyfile(path, os.path.join(today_folder, us_full_name))
                    break
                except Exception as e:
                    print("Copy failed ")
                    print(e)
                    time.sleep(4)
                    retry += 1
            parts = path.split('.')
            fld_path = ''.join(parts[:-1])
            if os.path.exists(fld_path):
                print("Found data folder : "+fld_path)
                retry = 0
                while retry < 2:
                    try:
                        print("Copying data folder retry "+str(retry))
                        shutil.copytree(fld_path, os.path.join(today_folder, os.path.basename(fld_path)),  dirs_exist_ok=True)
                        break
                    except Exception as e:
                        print("Copy failed ")
                        print(e)
                        time.sleep(2)
                        retry += 1
            if os.path.exists(fld_path+'.xml'):
                print("Found xml file")
                retry = 0
                while retry < 5:
                    try:
                        print("Copying file retry "+str(retry))
                        shutil.copyfile(fld_path+'.xml', os.path.join(today_folder, os.path.basename(fld_path)+'.xml'))
                        break
                    except Exception:
                        time.sleep(4)
                        retry += 1
        sld = Slide(
            SlideType=slide_type,
            Name=slide_name,
            ScannedBy='FTP',
            ScannedDate=datetime.datetime.now(),
            InsertedBy='FTP',
            InsertedDate=datetime.datetime.now(),
            UrlPath=today_folder_name+'/'+us_full_name,
            LabelUrlPath=label_location,
            Annotations=True,
            Folder=fld,
            Filesize=Path(os.path.join(
                today_folder, us_full_name)).stat().st_size,
            Tag='',
        )
        sld.save()
        print("Slide saved")
        return sld.id

    def run(self):
        while True and not self.killed:
            time.sleep(10)
            print("Checking if pool has completed")
            if not self.pool.checkRunning():
                print("All files are completed")
                break
        
        # File copy completed
        # Process each file
        # Remove from pool
        files = self.pool.getFiles()
        self.pool.emptyFiles()
        all_slides = {}
        for path, status in files.items():
            # Get the file extension from path
            slide_id = None
            ext = Path(path).suffix
            if len(ext) > 1:
                ext = ext[1:]
            else:
                continue
            print("Found extension: "+ext)
            if ext not in SINGFILE_IMAGE and ext not in MULTIFILE_IMAGE:
                continue
            rel = os.path.relpath(path, self.dir)
            print("Rel path :  "+rel)
            parts = rel.split('/')
            if len(parts) == 1:
                slide_id = self.uploadSlide(path, DB_FLD)
            else:
                folders = parts[:-1]
                parent = DB_FLD
                current = None
                for fld in folders:                     
                    print("Checking for folder "+fld)
                    try:
                        current = Folder.objects.get(Name=fld, Parent=parent)
                        print("Found folder ")
                        parent = current
                    except Exception:
                        current = Folder(Name=fld, Parent=parent)
                        current.save()
                        print("Created folder")
                        parent = current
                print("Parent folder")
                print(parent)
                slide_id = self.uploadSlide(path, parent)
            
            if len(parts) == 2:
                folder_name = parts[0]
                if folder_name in all_slides.keys():
                    all_slides[folder_name].append({'id': str(slide_id), 'name': parts[1]})
                else:
                    all_slides[folder_name] = [{'id': str(slide_id), 'name': parts[1]}]

        for folder_name, slides in all_slides.items():    
            slide_array = []
            for s in slides:
                if s['id'] is None:
                    continue
                slide_array.append({
                'url': 'https://'+settings.ALLOWED_HOSTS[0]+'/slide/'+s['id'], 
                'thumbnail': 'https://'+settings.ALLOWED_HOSTS[0]+'/slide/'+s['id']+'/fullthumbnail', 
                'slide_name': s['name']})
            body = {
                'req_identifier': folder_name,
                'slide_array': slide_array
            }
            if len(slide_array) > 0:
                r = requests.post(settings.PATHHUB_REST_URL+'addSlideToSpecimen', 
                json = body, headers=HEADERS, 
                auth=HTTPBasicAuth(username=settings.PATHHUB_REST_USER, password=settings.PATHHUB_REST_PASSWORD))
                if r.status_code == 400:
                    print(r.json())
                print(r.status_code)
                print("Request to database sent")
                

class CheckFileReady(threading.Thread):
    def __init__(self, pool, path):
        threading.Thread.__init__(self)
        self.pool = pool
        self.path = path
        self.killed = False

    def kill(self):
        self.killed = True

    def _check_file_ready(self):
        path = self.path
        if not os.path.exists(path):
            raise Exception("File not found: {}".format(path))
        if not os.path.isfile(path):
            raise Exception("Not a file: {}".format(path))
        if not os.access(path, os.R_OK):
            raise Exception("Not Readable: {}".format(path))
        # Check if the size of file every 3 seconds
        intital_size = os.stat(path).st_size
        time.sleep(4)
        if os.stat(path).st_size == intital_size:
            return True
        print(f"{self.path} File is being copied waiting for the copy to be finished")
        timeout_time = TIMEOUT / 10
        counter = 0
        while True and not self.killed:
            counter += 1
            time.sleep(10)
            if os.stat(path).st_size == intital_size:
                break
            print(f"{self.path} File still busy checking again after 10 sec")
            intital_size = os.stat(path).st_size
            if counter > timeout_time:
                raise Exception("Timeout")
        return True

    def run(self):
        self.pool.add(self.path, Status.RUNNING)
        try:
            self._check_file_ready()
            self.pool.add(self.path, Status.COMPLETED)
        except Exception:
            self.pool.add(self.path, Status.ERROR)
        
class FileProcessStateMachine:
    def __init__(self, dir) -> None:
        pool = Pool()
        self.pool = pool
        self.dir = dir
    
    def add(self, path):
        initial = self.pool.isFilesEmpty()
        CheckFileReady(self.pool, path).start()
        if initial:
            ThreadPoolWait(self.pool, self.dir).start()
        

class FileStatusHandler(FileSystemEventHandler):    
    def __init__(self, dir, fpsm) -> None:
        super().__init__()
        self.dir = dir
        self.observer = Observer()
        self.started = False
        self.fpsm = fpsm

    def start(self):    
        logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
        self.observer.schedule(self, self.dir, recursive=True)
        self.observer.start()
        self.started = True

    def join(self):
        if self.started:
            self.observer.join()

    def stop(self):
        if self.started:
            self.observer.stop()

    def isRunning(self):
        return self.started

    def on_created(self, event):
        name = os.path.basename(event.src_path)
        rel = os.path.relpath(event.src_path, self.dir)
        print(f'{bcolors.OKGREEN} Created: {rel} {bcolors.ENDC}')
        if (name[0] == '.'):
            return
        if (os.path.isdir(event.src_path)):
            # print("Processing the dir")
            pass
        elif (os.path.isfile(event.src_path)):
            self.fpsm.add(event.src_path)
            # print("Processing the file")

def __uploadSlide(path, fld):
    print("Uploading slide "+path+"  To folder: "+fld.Name)
    ext = Path(path).suffix
    if len(ext) > 1:
        ext = ext[1:]
    
    slide_name = os.path.basename(path)
    res = Slide.objects.filter(Name=slide_name, Folder=fld)
    if len(res) > 0:
        print("Slide exits returning")
        return res[0].id

    today_folder_name = datetime.datetime.now().strftime('%d-%m-%Y')
    today_folder = os.path.join(settings.SLIDES_DIR, today_folder_name)
    if not os.path.exists(today_folder):
        os.mkdir(today_folder)
    # Get file extension from path
    ext = Path(path).suffix[1:]
    slide_type = 2
    if ext in ['dcm', 'dcim', 'DCM', 'DCIM']:
        slide_type = 1
    us_full_name = slide_name
    label_location = '/static/images/placeholder.png'
    if ext in SINGFILE_IMAGE:
        print("Single image type file")
        retry = 0
        while retry < 5:
            try:
                print("Copying file retry "+str(retry))
                shutil.copyfile(path, os.path.join(today_folder, us_full_name))
                break
            except Exception as e:
                print("Copy failed")
                print(e)
                time.sleep(4)
                retry += 1
        print("Processing {}".format(path))
    if ext in MULTIFILE_IMAGE:
        print("Multi file image type")
        retry = 0
        while retry < 5:
            try:
                print("Copying file retry "+str(retry))
                shutil.copyfile(path, os.path.join(today_folder, us_full_name))
                break
            except Exception as e:
                print("Copy failed ")
                print(e)
                time.sleep(4)
                retry += 1
        parts = path.split('.')
        fld_path = ''.join(parts[:-1])
        if os.path.exists(fld_path):
            print("Found data folder : "+fld_path)
            retry = 0
            while retry < 2:
                try:
                    print("Copying data folder retry "+str(retry))
                    shutil.copytree(fld_path, os.path.join(today_folder, os.path.basename(fld_path)),  dirs_exist_ok=True)
                    break
                except Exception as e:
                    print("Copy failed ")
                    print(e)
                    time.sleep(2)
                    retry += 1
        if os.path.exists(fld_path+'.xml'):
            print("Found xml file")
            retry = 0
            while retry < 5:
                try:
                    print("Copying file retry "+str(retry))
                    shutil.copyfile(fld_path+'.xml', os.path.join(today_folder, os.path.basename(fld_path)+'.xml'))
                    break
                except Exception:
                    time.sleep(4)
                    retry += 1
    sld = Slide(
        SlideType=slide_type,
        Name=slide_name,
        ScannedBy='FTP',
        ScannedDate=datetime.datetime.now(),
        InsertedBy='FTP',
        InsertedDate=datetime.datetime.now(),
        UrlPath=today_folder_name+'/'+us_full_name,
        LabelUrlPath=label_location,
        Annotations=True,
        Folder=fld,
        Filesize=Path(os.path.join(
            today_folder, us_full_name)).stat().st_size,
        Tag='',
    )
    sld.save()
    print("Slide saved with id "+str(sld.id))
    return sld.id


def initial_scan(dir):
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(dir):
        for file in f:
            files.append(os.path.join(r, file))
    all_slides = {}
    for path in files:
        slide_id = None
        # Get the file extension from path
        ext = Path(path).suffix
        if len(ext) > 1:
            ext = ext[1:]
        else:
            continue
        print("Found extension: "+ext)
        if ext not in SINGFILE_IMAGE and ext not in MULTIFILE_IMAGE:
            continue
        rel = os.path.relpath(path, dir)
        print("Rel path :  "+rel)
        parts = rel.split('/')
        if len(parts) == 1:
            slide_id = __uploadSlide(path, DB_FLD)
        else:
            folders = parts[:-1]
            parent = DB_FLD
            current = None
            for fld in folders:                        
                print("Checking for folder "+fld)
                try:
                    current = Folder.objects.get(Name=fld, Parent=parent)
                    print("Found folder ")
                    parent = current
                except Exception:
                    current = Folder(Name=fld, Parent=parent)
                    current.save()
                    print("Created folder")
                    parent = current
            print("Parent folder")
            print(parent)
            slide_id = __uploadSlide(path, parent)
        
        if len(parts) == 2:
                folder_name = parts[0]
                if folder_name in all_slides.keys():
                    all_slides[folder_name].append({'id': str(slide_id), 'name': parts[1]})
                else:
                    all_slides[folder_name] = [{'id': str(slide_id), 'name': parts[1]}]

    print("All slides to be send to main app")
    for folder_name, slides in all_slides.items():    
        print(f"{folder_name}: {slides}")
        slide_array = []
        for s in slides:
            if s['id'] is None:
                continue
            slide_array.append({
            'url': 'https://'+settings.ALLOWED_HOSTS[0]+'/slide/'+s['id'], 
            'thumbnail': 'https://'+settings.ALLOWED_HOSTS[0]+'/slide/'+s['id']+'/fullthumbnail', 
            'slide_name': s['name']})
        body = {
            'req_identifier': folder_name,
            'slide_array': slide_array
        }
        if len(slide_array) > 0:
            print("Sending request")
            r = requests.post(settings.PATHHUB_REST_URL+'addSlideToSpecimen', 
            json = body, headers=HEADERS, 
            auth=HTTPBasicAuth(username=settings.PATHHUB_REST_USER, password=settings.PATHHUB_REST_PASSWORD))
            if r.status_code == 400:
                print(r.json())
            print(r.status_code)
            print("Request to database sent")