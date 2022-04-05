var row_template = `
    <tr>
        <td></td>
        <td>
            <a href="#" class="d-flex align-items-center">
                <figure class="avatar avatar-sm mr-3">
                    <span
                        class="avatar-title bg-warning text-black-50 rounded-pill">
                        <i class="ti-folder"></i>
                    </span>
                </figure>
                <span class="d-flex flex-column">
                    <span class="text-primary">Design Thinking Project</span>
                    <span class="small font-italic">550 KB</span>
                </span>
            </a>
        </td>
        <td>3/9/19, 2:40PM</td>
        <td>
            <div class="badge bg-info-bright text-info">Design</div>
        </td>
        <td>
            <div class="avatar-group">
                <figure class="avatar avatar-sm" title="Lisle Essam"
                    data-toggle="tooltip">
                    <img src="/static/assets/media/image/user/women_avatar2.jpg"
                        class="rounded-circle" alt="image">
                </figure>
                <figure class="avatar avatar-sm" title="Baxie Roseblade"
                    data-toggle="tooltip">
                    <img src="/static/assets/media/image/user/man_avatar5.jpg"
                        class="rounded-circle" alt="image">
                </figure>
                <figure class="avatar avatar-sm" title="Jo Hugill"
                    data-toggle="tooltip">
                    <img src="/static/assets/media/image/user/man_avatar1.jpg"
                        class="rounded-circle" alt="image">
                </figure>
                <figure class="avatar avatar-sm" title="Cullie Philcott"
                    data-toggle="tooltip">
                    <img src="/static/assets/media/image/user/women_avatar5.jpg"
                        class="rounded-circle" alt="image">
                </figure>
            </div>
        </td>
        <td class="text-right">
            <div class="dropdown">
                <a href="#" class="btn btn-floating" data-toggle="dropdown">
                    <i class="ti-more-alt"></i>
                </a>
                <div class="dropdown-menu dropdown-menu-right">
                    <a href="#" class="dropdown-item"
                        data-sidebar-target="#view-detail">View
                        Details</a>
                    <a href="#" class="dropdown-item">Share</a>
                    <a href="#" class="dropdown-item">Download</a>
                    <a href="#" class="dropdown-item">Copy to</a>
                    <a href="#" class="dropdown-item">Move to</a>
                    <a href="#" class="dropdown-item">Rename</a>
                    <a href="#" class="dropdown-item">Delete</a>
                </div>
            </div>
        </td>
    </tr>
    `;
    


function message(msg, level='info') {
    $("#alert-message").show().html(msg);
    $("#alert-message").removeClass().addClass('alert').addClass('alert-'+level);
    setTimeout(function() {
        $("#alert-message").fadeOut();
    }, 2500);
}

var selectedNode = null;
var table = null;



function initJSTree(jsonData) {
    $('#files').jstree({
        'core': jsonData,
        "types": {
            "folder": {
                "icon": "ti-folder text-warning",
            },
            "file": {
                "icon": "ti-file",
            }
        },
        plugins: ["types"]
    });

    

    $("#files").on('select_node.jstree', function(e, data) {
        var id = data.node.id;
        var folder_id = id.split('_')[1];
        selectedNode = data.node;
        if (folder_id == '0') {
            $(".newfile-button").hide();
        }else{
            $(".newfile-button").show();
        }
        
        $("#folder-heading").html(data.node.text);
        table.ajax.url('/api/folder/content?folder_id='+folder_id).load();
    });
} 



function refreshTree(sn) {
    $.get('/api/folder?node='+(sn === null ? '': sn.id), function(data) {
        var jsonData = {
            'data': data.folders,
            themes: {
                dots: false
            }
        }
        $("#files").jstree('destroy');
        initJSTree(jsonData);
    }).fail(function(err) {
        console.log(err);
    });
}

function selectNode(folder_id) {
    $("#files").jstree(true).deselect_all();
    $("#files").jstree(true).select_node('fld_'+folder_id);
    $("#files").jstree(true).open_node('fld_'+folder_id);
}

function edit_folder(folder_id) {
    $.get(`/api/folder/get?folder_id=${folder_id}`, function(data) {
        if (data.type === 'success') {
            $("#edit-folder-name-input").val(data.folder.Name);
            $("#editfolder-add-button").attr('data-id', data.folder.id);
            $("#editfolder-modal").modal('show');
        }else {
            message(data.message, 'danger');
        }
    }).fail(function(err) {
        message('Server error, try again later', 'danger');
        console.log(err);
    });
}

$("#editfolder-add-button").on('click', function() {
    var folder_id = $(this).attr('data-id');
    var folder_name = $("#edit-folder-name-input").val();
    $.post(`/api/folder/edit`, {folder_id, folder_name}, function(data) {
        if (data.type === 'success') {
            $("#editfolder-modal").modal('hide');
            message('Folder renamed', 'success');
            table.ajax.url('/api/folder/content?folder_id='+selectedNode.id.split('_')[1]).load();
            refreshTree(selectedNode);
        } else {
            $("#edit-folder-name-input").siblings('.invalid-feedback').html(data.message);
            $("#editfolder-form").addClass('was-validated');
        }
    });
});

function edit_file(file_id) {
    $.get(`/api/file/get?slide_id=${file_id}`, function(data) {
        if (data.type === 'success') {
            $("#edit-slidename-input").val(data.slide.Name);
            $("#edit-scannedby-input").val(data.slide.ScannedBy);
            $("#edit-scanneddate-input").val(data.slide.ScannedDate);
            $("#edit-insertedby-input").val(data.slide.InsertedBy);
            $("#edit-inserteddate-input").val(data.slide.InsertedDate);
            $("#edit-slidetype-input").val(data.slide.SlideType);
            if (data.slide.annotations) {
                $("#edit-annotaions-input").attr('checked', true);
            }else{ 
                $("#edit-annotaions-input").attr('checked', false);
            }
            $("#editfile-add-button").attr('data-id', data.slide.id);
            $("#editfile-modal").modal('show');
        }else{
            message(data.message, 'danger');
        }
    }).fail(function(err) {
        message('Server error, try again later', 'danger');
        console.log(err);
    });
}

function delete_folder(folder_id) {
    $("#delete-file-button").attr('data-id', folder_id);
    $("#delete-file-button").attr('data-type', 'folder');
    $("#delete-modal").modal('show');
}

function delete_file(file_id) {
    $("#delete-file-button").attr('data-id', file_id);
    $("#delete-file-button").attr('data-type', 'file');
    $("#delete-modal").modal('show');
}

$("#delete-file-button").on('click', function(e) {
    var id = $(this).attr('data-id');
    var type = $(this).attr('data-type');
    if (type === 'file') {
        $.get("/api/file/delete?file_id="+id, function(data) {
            $("#delete-modal").modal('hide');
            if (data.type === 'success') {
                message('File deleted', 'success');
                table.ajax.url('/api/folder/content?folder_id='+selectedNode.id.split('_')[1]).load();
                refreshTree(selectedNode);
            }else{
                message(data.message, 'danger');
            }
        }).fail(function(err) {
            console.log(err);
            message('Server error, try again later', 'danger');
        });
    }else{
        $.get("/api/folder/delete?folder_id="+id, function(data) {
            $("#delete-modal").modal('hide');
            if (data.type === 'success') {
                message('Folder deleted', 'success');
                table.ajax.url('/api/folder/content?folder_id='+selectedNode.id.split('_')[1]).load();
                refreshTree(selectedNode);
            }else{
                message(data.message, 'danger');
            }
        }).fail(function(err) {
            console.log(err);
            message('Server error, try again later', 'danger')
        });
    }
});

function copy_file(file_id, filename, ele) {
    $(ele).parents('.dropdown-menu').dropdown('toggle');
    $("#paste-button-container").show();
    $("#paste-button").attr('data-id', file_id);
    $("#paste-button").attr('data-name', filename);
}

$("#paste-button").on('click', function() {
    var id = $(this).attr('data-id');
    var filename = $(this).attr('data-name');
    if (selectedNode === null || selectedNode.id === 'fld_0') {
        message('Cannot paste file in root folder', 'danger');
    }else{
        if (typeof id === 'undefined' || id.length === 0 || isNaN(id)) {
            message('Invalid file', 'danger');
            return;
        }
        if (typeof filename === 'undefined' || filename.length === 0) {
            message('Invalid file', 'danger');
            return;
        }
    }
    $(this).hide();
    var folder_id = selectedNode.id.split('_')[1];
    $("#copy-name-input").val(filename);
    $("#copy-add-button").attr('data-id', id);
    $("#copy-add-button").attr('data-folder', folder_id);
    $("#copy-modal").modal('show');
});

$("#copy-add-button").on('click', function() {
    var id = $(this).attr('data-id');
    var folder_id = $(this).attr('data-folder');
    var name = $("#copy-name-input").val();
    $.get(`/api/file/copy?file_id=${id}&slidename=${name}&folder_id=${folder_id}`, function(data) {
        if (data.type === 'success') {
            $("#copy-modal").modal('hide');
            table.ajax.url('/api/folder/content?folder_id='+selectedNode.id.split('_')[1]).load();
        }else{
            $("#copy-name-input").parents('form').addClass('was-validated');
            $("#copy-name-input").addClass('is-invalid');
            $("#copy-name-input").siblings('.invalid-feedback').html(data.message);
        }
    });
});



$("#editfile-form").on('submit', function(e) {
    e.preventDefault();
    var id = $("#editfile-add-button").attr('data-id');
    var form_data = $(this).serializeArray();
    var data = {};
    $(form_data).each(function(index, obj) {
        data[obj.name] = obj.value;
    });
    data['id'] = id;
    $.post('/api/file/edit', data, function(response) {
        if (response.type === 'success') {
            $("#editfile-modal").modal('hide');
            message('Slide saved successfully', 'success');
            table.ajax.url('/api/folder/content?folder_id='+selectedNode.id.split('_')[1]).load();
        }else{
            $("#editfile-form").addClass('was-validated');
            for (let i = 0 ; i < response.errors.length; i++) {
                var err = response.errors[i];
                $("#editfile-form").find(`input[name="${err.name}"], select[name="${err.name}"]`).addClass('is-invalid').siblings('.invalid-feedback').html(err.message);
            }
        }
    });
});


$(() => {

    $('.datepicker-input').daterangepicker({
        singleDatePicker: true,
        showDropdowns: true
    });

    $("#newfile-modal").on('show.bs.modal', function() {
        if (selectedNode == null) {
            return;
        }
        var folder_id =  selectedNode.id.split('_')[1];
        $(this).find('input').val('').removeClass('is-invalid').removeClass('is-valid');
        $(this).find('select').val('').removeClass('is-invalid').removeClass('is-valid');
        $(this).removeClass('was-validated');

        $.get('/api/folder/parent?folder_id='+folder_id, function(data) {
            if (data.type == 'fail') {
                $("#parent-folder-reference").html(data.message).addClass('text-danger');
                $("#newfile-add-button").attr('disabled', true);
            }else {
                var parents = data.parents.join(' &#129042; ');
                $("#newfile-add-button").attr('disabled', false);
                $("#parent-folder-reference").html(parents).removeClass('text-danger');
            }


        }).fail(function() {
            $("#parent-folder-reference").html('Server error, try again later').addClass('text-danger');
            $("#newfile-add-button").attr('disabled', true);
        });
    });

    var ajaxCall = null;

    $("#newfile-form").on('submit', function(e) {
        e.preventDefault();
        var form_data = $(this).serializeArray();
        var data = {};
        $(form_data).each(function(index, obj) {
            data[obj.name] = obj.value;
        });
        data['parent'] = parseInt(selectedNode.id.split('_')[1]);
        var fd = new FormData();
        for (const [key, value] of Object.entries(data)) {
            fd.append(key, value);
        }
        var errors = false;   
        if (data.slidename.length == 0) {
            $("#slidename-input").addClass('is-invalid');
            $("#slidename-input").siblings('.invalid-feedback').html('Slide Name cannot be empty');
            $("#newfile-form").addClass('was-validated');
            errors = true;
        } 
        if (data.slide_type.length == 0) {
            $("#slidetype-input").addClass('is-invalid');
            $("#slidetype-input").siblings('.invalid-feedback').html('Please select a slide type');
            $("#newfile-form").addClass('was-validated');
            errors = true;
        }
        var slide_input = $("#slide-input")[0].files;
        var label_input = $("#customlabel-input")[0].files;
        if (slide_input.length === 0) {
            $("#slide-input").addClass('is-invalid');
            $("#slide-input").siblings('.invalid-feedback').html('Please select a file');
            $("#newfile-form").addClass('was-validated');
            errors = true;
        }
        if (errors) return;
        fd.append('slide_upload', slide_input[0]);
        fd.append('label_upload', label_input.length === 0 ? '' : label_input[0]);

        $(".newfile-modal-close-button").hide();
        $("#newfile-cancel-button").show();
        $("#newfile-add-button").attr('disabled', true);
        debugger
        ajaxCall = $.ajax({
            url: '/api/file/new',
            type: 'post',
            data: fd,
            contentType: false,
            processData: false,

            success: function(d) {
                console.log(d);
                if (d.type === 'fail') {
                    message(d.message, 'danger');
                }else {
                    message('File uploaded', 'success');
                }
            },
            complete: function() {
                $("#newfile-modal").modal('hide');
                $(".newfile-modal-close-button").show();
                $("#newfile-upload-progress").hide();
                $("#newfile-upload-label").hide();
                var folder_id = selectedNode.id.split('_')[1];
                table.ajax.url('/api/folder/content?folder_id='+folder_id).load();
                $("#newfile-add-button").attr('disabled', false);
                $("#newfile-cancel-button").hide();
                ajaxCall = null;
            },
            error: function(jqXhr, status, statusText) {
                if (status === 'abort') {
                    message('Upload Canceled' , 'warning');
                } else {
                    message('Server error, Try again later', 'danger');
                    console.log(jqXhr, status, statusText);
                }
            },
            xhr: function() {
                const xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener('progress', function(e) {
                    if (e.lengthComputable) {
                        var loaded = e.loaded;
                        var total = e.total;
                        var percent = (loaded / total) * 100;
                        loaded = bytes_to_words(loaded);
                        total = bytes_to_words(total);
                        $("#newfile-upload-progress").find('.progress-bar').css({'width': percent+'%'}).attr('aria-valuenow', percent.toFixed(1)).html(percent.toFixed(1)+'%');
                        $("#newfile-upload-progress").show();
                        $("#newfile-upload-label").html(loaded+' / '+total).show();
                    }
                });
                return xhr;
            }
        });

    });

    $("#newfile-cancel-button").on('click', function() {
        if (ajaxCall) {
            ajaxCall.abort();
        }
    });

    $("#slidename-input").on('change', function() {
        var val = $(this).val();
        var parent_id = selectedNode.id.split('_')[1];
        if (val.trim().length == 0) {
            $(this).removeClass('is-valid');
            $(this).addClass('is-invalid');
            $(this).siblings('.invalid-feedback').html('Slide Name cannot be empty');
        }else{
            $.get(`/api/file/exist?folder_id=${parent_id}&slidename=${val}`, function(data) {
                if (data.type == 'success') {
                    if (data.response) {
                        $(this).removeClass('is-valid');
                        $(this).addClass('is-invalid');
                        $(this).siblings('.invalid-feedback').html('A file with same name already exists');
                    }else{
                        $(this).addClass('is-valid');
                        $(this).removeClass('is-invalid');            
                    }
                }else{
                    $(this).removeClass('is-valid');
                    $(this).addClass('is-invalid');
                    $(this).siblings('.invalid-feedback').html(data.message);
                }
            });
        }
    });

    $("#slide-input").on('change', function() {
        var val = $(this).val();
        if (val.trim().length == 0) {
            $(this).removeClass('is-valid');
            $(this).addClass('is-invalid');
            $(this).siblings('.invalid-feedback').html('Please select a file');
        }else{
            $.get(`/api/file/valid?filename=${val}`, function(data) {
                if (data.type == 'success') {
                    if (data.response) {
                        $(this).addClass('is-valid');
                        $(this).removeClass('is-invalid');
                    } else {
                        $(this).removeClass('is-valid');
                        $(this).addClass('is-invalid');
                        $(this).siblings('.invalid-feedback').html('File not supported');
                    }
                }else{
                    $(this).removeClass('is-valid');
                    $(this).addClass('is-invalid');
                    $(this).siblings('.invalid-feedback').html(data.message);
                }
            });
            
        }
    });

    $("#slidetype-input").on('change', function() {
        var val = $(this).val();
        if (val.trim().length == 0) {
            $(this).removeClass('is-valid');
            $(this).addClass('is-invalid');
            $(this).siblings('.invalid-feedback').html('Please select a slide type');
        }else{
            $(this).addClass('is-valid');
            $(this).removeClass('is-invalid');
        }
    });

    $.get('/api/folder/content?folder_id=1', function(data) {
        console.log(data);
        
    });

    table = $('#table-files').DataTable({
        'ajax': {
            'url': '/api/folder/content',
            'dataSrc': 'data'
        },
        'columnDefs': [
            {
                'targets': 0,
                'className': 'dt-body-center',
                'render': function (data, type, full, meta) {
                    return '<div class="custom-control custom-checkbox">' +
                        '<input type="checkbox" class="custom-control-input" id="customCheck' + meta.row + '">' +
                        '<label class="custom-control-label" for="customCheck' + meta.row + '"></label>' +
                        '</div>';
                }
            },
            {
                'targets': 1,
                'data': 'name',
                'render': function(data, type, row, meta) {
                    if (type == 'display') {
                        if (data.type == 'file') {
                            return `
                            <a onclick="window.open('/slide/${data.id}')"  class="d-flex pointer align-items-center list-item-name">
                                <figure class="avatar avatar-sm mr-3">
                                    <span
                                        class="avatar-title text-black-50 rounded-pill">
                                        <i class="ti-${data.type}"></i>
                                    </span>
                                </figure>
                                <span class="d-flex flex-column">
                                    <span class="text-primary">${data.name}</span>
                                    <span class="small font-italic">${data.size}</span>
                                </span>
                            </a>
                            `;
                        } else if (data.type == 'folder') {
                            return `
                            <a href="#" onclick="selectNode('${data.id}')" class="d-flex align-items-center list-item-name">
                                <figure class="avatar avatar-sm mr-3">
                                    <span
                                        class="avatar-title bg-warning text-black-50 rounded-pill">
                                        <i class="ti-${data.type}"></i>
                                    </span>
                                </figure>
                                <span class="d-flex flex-column">
                                    <span class="text-primary">${data.name}</span>
                                </span>
                            </a>
                            `;
                        }
                    }
                    return data.name;                    
                }
                
            },
            {
                'targets': 2,
                'data': 'created',
                'render': function(data, type, raw, meta) {
                    var created = new Date(data);
                    if (type == 'display') {
                        return created.toDateString();
                    }
                    return created;
                }

            },
            {
                'targets': 3,
                'data': 'tag',
                'render': function(data, type, raw, meta) {
                    if (data === '') {
                        return '';
                    }
                    return `<div class="badge bg-info-bright text-info">${data}</div>`;
                }

            },
            {
                'targets': 4,
                'data': 'cached',
                'render': function(data, type, raw, meta) {
                    if (data === '') {
                        return '';
                    }
                    if (data) {
                        return `<div class="badge bg-success-bright text-info">Cached</div>`;
                    }else {
                        return `<div></div>`;
                    }
                }
            },
            {
                'targets': 5,
                'className': 'text-right',
                'data': 'id',
                'render': function(data, type, raw, meta) {
                    if (data.type === 'folder') {
                        return `
                        <div class="dropdown">
                            <a href="#" class="btn btn-floating" data-toggle="dropdown">
                                <i class="ti-more-alt"></i>
                            </a>
                            <div class="dropdown-menu dropdown-menu-right">
                                <a href="#" class="dropdown-item"
                                    data-sidebar-target="#view-detail">View
                                    Details</a>
                                <a href="#" onclick="edit_folder(${data.id})" class="dropdown-item">Rename</a>
                                <a href="#" onclick="delete_folder(${data.id})" class="dropdown-item">Delete</a>
                            </div>
                        </div>
                        `;
                    } else {
                        return `
                        <div class="dropdown">
                            <a href="#" class="btn btn-floating" data-toggle="dropdown">
                                <i class="ti-more-alt"></i>
                            </a>
                            <div class="dropdown-menu dropdown-menu-right">
                                <a href="#" class="dropdown-item"
                                    data-sidebar-target="#view-detail">View
                                    Details</a>
                                <a href="#" class="dropdown-item">Download</a>
                                <a href="#" onclick="copy_file(${data.id}, '${data.name}', this)" class="dropdown-item">Copy</a>
                                <a href="#" onclick="edit_file(${data.id})" class="dropdown-item">Edit</a>
                                <a href="#" onclick="delete_file(${data.id})" class="dropdown-item">Delete</a>
                            </div>
                        </div>
                        `;
                    }
                }
            },
            {
                "orderable": false,
                "targets": [0, 5]
            }
        ],
        'order': [1, 'asc']
    });



    if ($('#justgage_five').length) {
        $.get('api/storage', function(data) {
            new JustGage({
                id: 'justgage_five',
                value: data.disk_usage[3],
                minTxt: " ",
                min: 0,
                max: 100,
                maxTxt: " ",
                symbol: '%',
                label: "Storage Usage",
                gaugeWidthScale: 0.7,
                counter: true,
                relativeGaugeSize: true,
                levelColors: ['#4c62df'],
                gaugeColor: '#f3f3f3',
                valueFontColor: 'black',
                valueFontFamily: 'Josefin Sans'
            });
            for(let i = 0; i < data.folders.length; i++) {
                var fld = data.folders[i];
                var template = $($("#storage-overview-template").html());
                if (fld[0] === 'Labels') {
                    template.find('.ti-files').removeClass('ti-files').addClass('ti-image');
                }
                template.find('.folder-name').html(fld[0]);
                template.find('.folder-size').html(fld[1]);
                template.find('.folder-files').html(fld[2]+' Files');
                $("#storage-overview-container").append(template);
            }
            
            var template = $($("#storage-overview-template").html());
            template.find('.ti-files').removeClass('ti-files').addClass('ti-file');
            template.find('.folder-name').html("Other Files");
            template.find('.folder-size').html(data['other']);
            template.find('.folder-files').html('');
            $("#storage-overview-container").append(template);


            var template = $($("#storage-overview-template").html());
            template.find('.ti-files').removeClass('ti-files').addClass('ti-file');
            template.find('.folder-name').html("Total Storage");
            template.find('.folder-size').html(data['total']);
            template.find('.folder-files').html('');
            $("#storage-overview-container").append(template);
        }).fail(function() {
            $("#storage-error-message").show();
        });
    }

    if ($('#files').length) {
        $.get('/api/folder?node='+(selectedNode === null ? '': selectedNode.id), function(data) {
            var jsonData = {
                'data': data.folders,
                themes: {
                    dots: false
                }
            }
            initJSTree(jsonData);

            setTimeout(function() {
                
            }, 1000);
        }).fail(function(err) {
            console.log(err);
        });

        $("#newfolder-add-button").on('click', function() {
            var folder_name = $("#folder-name-input").val();
            var parent_id = 0;
            if (selectedNode !== null) {
                var parent_id = parseInt(selectedNode.id.split('_')[1]);
            }
            $.post('/api/folder/new', {
                folder_name,
                parent_id
            }, function(data) {
                if (data.type == 'success') {
                    message('Folder successfully created', 'success');
                    table.ajax.url('/api/folder/content?folder_id='+parent_id).load();
                    refreshTree(selectedNode);
                }else{
                    message(data.message, 'danger');
                }
                // Refresh JSTree
            }).fail(function(err) {
                console.log(err);
                message('Error Creating folder', 'danger')
            }).always(function() {
                $("#new-folder-modal").modal('hide');
            });
        });
    }
});


