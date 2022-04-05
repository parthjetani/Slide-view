from .models import Folder,Slide

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
                        'image_size': chld.Filesize,
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
            'image_size': rf.Filesize,

            'type': 'file',
        }
        tree.append(fld)

    return tree

    
def get_folder_structure():
    main_list = []
    root_folders = Folder.objects.filter(Parent=None)

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








