function message(msg, level = 'info') {
    $("#alert-message").show().html(msg);
    $("#alert-message").removeClass().addClass('alert').addClass('alert-' + level);
    setTimeout(function () {
        $("#alert-message").fadeOut();
    }, 2500);
}

function containsOnlyFiles(children) {

    for (var i = 0; i < children.length; i++) {
        if (children[i].type == 'folder') {
            return false
        }
    }
    return true;
}

function containsFiles(children) {
    for (var i = 0; i < children.length; i++) {
        if (children[i].type == 'file') {
            return true
        }
    }
    return false;
}

function edit_folder(folder_id) {
    $.get(`/api/folder/get?folder_id=${folder_id}`, function (data) {
        if (data.type === 'success') {
            $("#edit-folder-name-input").val(data.folder.Name);
            $("#editfolder-add-button").attr('data-id', data.folder.id);
            $("#editfolder-modal").modal('show');
        } else {
            message(data.message, 'danger');
        }
    }).fail(function (err) {
        message('Server error, try again later', 'danger');
        console.log(err);
    });
}

$("#editfolder-add-button").on('click', function () {
    var folder_id = $(this).attr('data-id');
    var folder_name = $("#edit-folder-name-input").val();
    $.post(`/api/folder/edit`, {
        folder_id,
        folder_name
    }, function (data) {
        if (data.type === 'success') {
            $("#editfolder-modal").modal('hide');
            draw_table_tree()

        } else {
            $("#edit-folder-name-input").siblings('.invalid-feedback').html(data.message);
            $("#editfolder-form").addClass('was-validated');
        }
    });
});

function delete_folder(folder_id) {
    $("#delete-file-button").attr('data-id', folder_id);
    $("#delete-file-button").attr('data-type', 'folder');
    $("#delete-modal").modal('show');
}

$("#delete-file-button").on('click', function (e) {
    var id = $(this).attr('data-id');
    var type = $(this).attr('data-type');
    if (type === 'file') {
        $.get("/api/file/delete?file_id=" + id, function (data) {
            $("#delete-modal").modal('hide');
            if (data.type === 'success') {
                draw_table_tree()
            } else {
                message(data.message, 'danger');
            }
        }).fail(function (err) {
            console.log(err);
            message('Server error, try again later', 'danger');
        });
    } else {
        $.get("/api/folder/delete?folder_id=" + id, function (data) {
            $("#delete-modal").modal('hide');
            if (data.type === 'success') {
                //refresh page
                draw_table_tree();
            } else {
                message(data.message, 'danger');
            }
        }).fail(function (err) {
            console.log(err);
            message('Server error, try again later', 'danger')
        });
    }
});

function delete_file(file_id) {
    $("#delete-file-button").attr('data-id', file_id);
    $("#delete-file-button").attr('data-type', 'file');
    $("#delete-modal").modal('show');
}

function add_file(parent_folder_id) {
    $("#newfile-add-button").attr('folder-id', parent_folder_id);
    //empty the form
    $("#newfile-form").trigger('reset');
    $("#newfile-modal").modal('show');
}

$("form#newfile-form").on('submit', function (e) {
    e.preventDefault();
    var form_data = $(this).serializeArray();
    var data = {};
    $(form_data).each(function (index, obj) {
        data[obj.name] = obj.value;
    });
    data['parent'] = parseInt($("#newfile-add-button").attr('folder-id'));
    var fd = new FormData();
    for (const [key, value] of Object.entries(data)) {
        fd.append(key, value);
    }
    console.log(fd);
    var errors = false;


    if (data.slidename.length == 0) {
        $("#slidename-input").addClass('is-invalid');
        $("#slidename-input").siblings('.invalid-feedback').html('Slide Name cannot be empty');
        $("#newfile-form").addClass('was-validated');
        errors = true;
    } else {
        $("#slidename-input").removeClass('is-invalid');
        $("#slidename-input").siblings('.invalid-feedback').html('');
    }



    if (data.slide_type.length == 0) {
        $("#slidetype-input").addClass('is-invalid');
        $("#slidetype-input").siblings('.invalid-feedback').html('Please select a slide type');
        $("#newfile-form").addClass('was-validated');
        errors = true;
    } else {
        $("#slidetype-input").removeClass('is-invalid');
        $("#slidetype-input").siblings('.invalid-feedback').html('');
    }


    var slide_input = $("#slide-input")[0].files;
    var label_input = $("#customlabel-input")[0].files;
    if (slide_input.length === 0) {
        $("#slide-input").addClass('is-invalid');
        $("#slide-input").siblings('.invalid-feedback').html('Please select a file');
        $("#newfile-form").addClass('was-validated');
        errors = true;
    } else {
        var ext = slide_input[0]['name'].split('.').pop().toLowerCase();
        if ($.inArray(ext, ['svs', 'tiff', 'mrsx', 'dicom']) == -1) {
            $("#slide-input").addClass('is-invalid');
            $("#slide-input").siblings('.invalid-feedback').html('Not accepted file type(Allowed: svs, tiff, mrsx, dicom)');
            $("#newfile-form").addClass('was-validated');
            errors = true;
        } else {
            $("#slide-input").removeClass('is-invalid');
            $("#slide-input").siblings('.invalid-feedback').html('');
        }
    }

    if (errors) return;
    fd.append('slide_upload', slide_input[0]);
    fd.append('label_upload', label_input.length === 0 ? '' : label_input[0]);

    $(".newfile-modal-close-button").hide();
    $("#newfile-cancel-button").show();
    $("#newfile-add-button").attr('disabled', true);
    ajaxCall = $.ajax({
        url: '/api/file/new',
        type: 'post',
        data: fd,
        contentType: false,
        processData: false,

        success: function (d) {
            console.log(d);
            if (d.type === 'fail') {
                message(d.message, 'danger');
            } else {
                message('File uploaded', 'success');
                
            }
        },
        complete: function () {
            $("#newfile-modal").modal('hide');
            $(".newfile-modal-close-button").show();
            $("#newfile-upload-progress").hide();
            $("#newfile-upload-label").hide();
            draw_table_tree();
            $("#newfile-add-button").attr('disabled', false);
            $("#newfile-cancel-button").hide();
            ajaxCall = null;

        },
        error: function (jqXhr, status, statusText) {
            if (status === 'abort') {
                message('Upload Canceled', 'warning');
            } else {
                message('Server error, Try again later', 'danger');
                console.log(jqXhr, status, statusText);
            }
        },
        xhr: function () {
            const xhr = new window.XMLHttpRequest();
            xhr.upload.addEventListener('progress', function (e) {
                if (e.lengthComputable) {
                    var loaded = e.loaded;
                    var total = e.total;
                    var percent = (loaded / total) * 100;
                    loaded = bytes_to_words(loaded);
                    total = bytes_to_words(total);
                    $("#newfile-upload-progress").find('.progress-bar').css({
                        'width': percent + '%'
                    }).attr('aria-valuenow', percent.toFixed(1)).html(percent.toFixed(1) + '%');
                    $("#newfile-upload-progress").show();
                    $("#newfile-upload-label").html(loaded + ' / ' + total).show();
                }
            });
            return xhr;
        }
    });

});

function draw_table_tree() {
    //empty the table
    $('#folder-structure-tbody').empty();

    $.ajax({
        url: '/api/folder-structure',
        type: 'get',}).done(function(data) {
            var folder_data = data['folder'];
            var appendhtml='';            
            $.each(folder_data, function (index, value) {        
                appendhtml += `<tr data-toggle="collapse" data-target="#${value.id}_${value.type}_id" class="accordion-toggle">
                    <td class="text-center"><i class="fa fa-eye"></i></td>
                    <td>${index+1}</td>
                    <td>${value.text}</td>
                    <td>${value.created_at}</td>
                    <td><a href="#" class="btn btn-outline-light dropdown-toggle btn-sm"
                        data-toggle="dropdown">
                        Add
                    </a>
                    <div class="dropdown-menu">
                        <a href="#" class="dropdown-item" data-toggle="modal" data-target="#new-folder-modal"><i class="fa fa-plus mr-2"></i> Folder</a>
                        <a href="#" onclick="add_file(${value.id})" class="dropdown-item newfile-button"><i class="fa fa-plus mr-2"></i> File</a>
                    </div></td>
                    <td><div class="dropdown">
                        <a href="#" class="btn btn-floating" data-toggle="dropdown">
                            <i class="fa fa-ellipsis-v" aria-hidden="true"></i>
                        </a>
                        <div class="dropdown-menu dropdown-menu-right text-left">
                            <a href="#" onclick="edit_folder(${value.id})" class="dropdown-item"><i class="fa fa-retweet ml-2" aria-hidden="true"></i>
Rename</a>
                            <a href="#" onclick="delete_folder(${value.id})" class="dropdown-item"><i class="fa fa-trash-o ml-2" aria-hidden="true"></i>
 Delete</a>
                        </div>
                    </div></td>
                </tr>`;
            if (value.type == 'folder' && value.children.length > 0) {
                appendhtml += addmorechild(value.children, value.id, value.type);
            }
        });
        $('#folder-structure-tbody').append(appendhtml);

        $(".accordion-toggle").click(function () {
            var id = $(this).attr("data-target");
            $(id).toggleClass("show");
        });
    })

}

function addmorechild(element, id, type) {
    child_id = `${id}_${type}_table`;
    if (containsOnlyFiles(element)) {
        var html = `<tr>
            <td colspan="12" class="hiddenRow">
                <div class="accordian-body collapse" id="${id}_${type}_id">
                    <table class="table last-child" id="${child_id}">
                        <thead>
                            <tr>
                                <th width='30px'></th>
                                <th>Sr. No.</th>
                                <th></th>
                                <th>File Name</th>
                                <th>Created On</th>
                                <th>CASE ID</th>
                                <th>CASE No.</th>
                                <th>Created by</th>
                                <th>Image Size</th>
                                <th>
                                    <div class="dropdown">
                                    <a href="#" class="btn btn-outline-light dropdown-toggle"
                                    data-toggle="dropdown">
                                    Actions
                                    </a>
                                        <div class="dropdown-menu dropdown-menu-right">
                                            <a href="#" class="dropdown-item" onclick="delete_multiple_files('${child_id}')" >Delete Selected</a>
                                        </div>
                                    </div>
                                </th>                               
                            </tr>
                        </thead>
                        <tbody>`;

        $.each(element, function (index, value) {
            html += `<tr>
                <td class="text-center"><i class="fa fa-eye"></i></td>
                <td>${index+1}</td>
                <td><input type="checkbox" name="file_checkbox" value="${value.id}"></td>
                <td class="hiddenRow"><div id="file-row"><p style="color: blue;cursor:pointer" onclick="edit_file(${value.id})">${value.text}</p></div></td>
                <td>${value.created_at}</td>
                <td><p style="color: blue;cursor:pointer" onclick="edit_file(${value.id})">${value.id}</p></td>
                <td>${value.case_no}</td>
                <td>${value.created_by}</td>
                <td>${value.image_size}</td>
                <td>
                    <div class="dropdown">
                        <a href="#" class="btn btn-floating" data-toggle="dropdown">
                            <i class="fa fa-ellipsis-v" aria-hidden="true"></i>
                        </a>
                        <div class="dropdown-menu dropdown-menu-right">
                            <a href="#" onclick="window.open('/slide/${value.id}')" class="dropdown-item">View</a>
                            <a href="/slide/${value.id}/download/" class="dropdown-item" download>Download</a>
                            <a href="#" onclick="delete_file(${value.id})" class="dropdown-item"><i class="fa fa-trash-o ml-2" aria-hidden="true"></i>
 Delete</a>
                        </div>
                    </div>
                </td>
            </tr>`

        });

    } else {
        var html = `<tr>
            <td colspan="12" class="hiddenRow">
                <div class="accordian-body collapse" id="${id}_${type}_id">
                    <table class="table first-child" id="${child_id}" style="background:#fbfbfb">
                        <thead>
                            <tr>
                                <th width='30px'></th>
                                <th>Sr. No.</th>
                                <th>Folder Name</th>
                                <th>Created On</th>
                                <th></th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>`;


        var folder_count = 0;
        $.each(element, function (index, value) {
            if (value.type == 'folder') {
                folder_count++;
                // console.log(index,value);                
                html += `<tr data-toggle="collapse" class="accordion-toggle" data-target="#${value.id}_${value.type}_id">
                            <td class="text-center"><i class="fa fa-eye"></i></td>
                            <td>${folder_count}</td>
                            <td>${value.text}</td>
                            <td>${value.created_at}</td>
                            <td><a href="#" class="btn btn-outline-light dropdown-toggle btn-sm"
                                data-toggle="dropdown">
                                Add
                            </a>
                            <div class="dropdown-menu">
                                <a class="dropdown-item" data-toggle="modal" data-target="#new-folder-modal" href="#"><i class="fa fa-plus mr-2"></i> Folder</a>
                                <a href="#" onclick="add_file(${value.id})" class="dropdown-item newfile-button"><i class="fa fa-plus mr-2"></i> File</a>
                            </div></td>
                            <td><div class="dropdown">
                                <a href="#" class="btn btn-floating" data-toggle="dropdown">
                                    <i class="fa fa-ellipsis-v" aria-hidden="true"></i>
                                </a>
                                <div class="dropdown-menu dropdown-menu-right text-left">
                                    <a href="#" onclick="edit_folder(${value.id})" class="dropdown-item"><i class="fa fa-retweet ml-2" aria-hidden="true"></i>
Rename</a>
                                    <a href="#" onclick="delete_folder(${value.id})" class="dropdown-item"><i class="fa fa-trash-o ml-2" aria-hidden="true"></i>
 Delete</a>
                                </div>
                            </div></td>
                        </tr>`;

                if (value.type == 'folder' && value.children.length > 0) {
                    html += addmorechild(value.children, value.id, value.type);
                }

            }
        });

        if (containsFiles(element)) {
            file_table_html = `<tr>
                <td colspan="12" class="hiddenRow">
                    <div class="accordian-body" id="${id}_${type}_id">
                        <table class="table table-striped" id="${child_id}">
                            <thead>
                                <tr>
                                    <th>Sr. No.</th>
                                    <th></th>
                                    <th>File Name</th>
                                    <th>Created On</th>
                                    <th>CASE ID</th>
                                    <th>Created by</th>
                                    <th>Image Size</th>
                                    <th>
                                        <div class="dropdown">
                                        <a href="#" class="btn btn-outline-light dropdown-toggle"
                                        data-toggle="dropdown">
                                        Actions
                                        </a>

                                            <div class="dropdown-menu dropdown-menu-right">
                                                <a href="#" class="dropdown-item" onclick="delete_multiple_files('${child_id}')" >Delete Selected</a>
                                            </div>
                                        </div>

                                    </th>
                                </tr>
                            </thead>
                            <tbody>`

            file_count = 0;
            $.each(element, function (index, value) {
                if (value.type == 'file') {
                    file_count += 1;
                    file_table_html += `<tr>
                        <td>${file_count}</td>
                        <td><input type="checkbox" name="file_checkbox" value="${value.id}"></td>
                        <td class="hiddenRow"><div id="file-row"><p style="color: blue;cursor:pointer" onclick="edit_file(${value.id})">${value.text}</p></div></td>
                        <td>${value.created_at}</td>
                        <td><p style="color: blue;cursor:pointer" onclick="edit_file(${value.id})">${value.id}</p></td>
                        <td>${value.created_by}</td>
                        <td>${value.image_size}</td>
                        <td>
                            <div class="dropdown">
                                <a href="#" class="btn btn-floating" data-toggle="dropdown">
                                    <i class="fa fa-ellipsis-v" aria-hidden="true"></i>
                                </a>
                                <div class="dropdown-menu dropdown-menu-right">
                                    <a href="#" onclick="window.open('/slide/${value.id}')" class="dropdown-item">View</a>
                                    <a href="slide/${value.id}/download/" class="dropdown-item" download>Download</a>
                                    <a href="#" onclick="delete_file(${value.id})" class="dropdown-item"><i class="fa fa-trash-o ml-2" aria-hidden="true"></i>
 Delete</a>
                                </div>
                            </div>
                        </td>
                    </tr>`
                }
            });


            file_table_html += `</tbody>
                            </table>
                        </div>
                    </td>
                </tr>`;

            html += file_table_html;

        }

    }

    html += `</tbody>
                </table>
            </div>
        </td>
    </tr>`;
    return html;
}
$('.datepicker-input').daterangepicker({
    singleDatePicker: true,
    showDropdowns: true
});

function delete_multiple_files(table_id) {
    if($(`table#${table_id}`).find('input[type="checkbox"]:checked').length > 0){

        $("#delete-modal").modal('show');
        $("#delete-modal").on('click', '#delete-file-button', function () {
            var file_ids = [];
            $(`table#${table_id}`).find('input[type="checkbox"]:checked').each(function () {
                file_ids.push($(this).val());
            });

            console.log(file_ids);
            $.ajax({
                type: "POST",
                url: "/api/file/delete-multiple",
                data: {
                    files_ids: JSON.stringify(file_ids)
                },
                success: function (data) {
                    draw_table_tree();
                },
                error: function (data) {
                    console.log(data);
                }
            });
        });
    }
    else{
        message('Please select atleast one file to delete','danger');
    }
}

function edit_file(file_id) {
    $.get(`/api/file/get?slide_id=${file_id}`, function(data) {
        if (data.type === 'success') {
            $("#edit-slidename-input").val(data.slide.Name);
            $("#edit-scannedby-input").val(data.slide.ScannedBy);
            $("#edit-scanneddate-input").val(data.slide.ScannedDate);
            $("#edit-insertedby-input").val(data.slide.InsertedBy);
            $("#edit-inserteddate-input").val(data.slide.InsertedDate);
            $("#edit-slidetype-input").val(data.slide.SlideType);
            $("#edit-caseNumber-input").val(data.slide.CaseNo);

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
            draw_table_tree();
        }else{
            $("#editfile-form").addClass('was-validated');
            for (let i = 0 ; i < response.errors.length; i++) {
                var err = response.errors[i];
                $("#editfile-form").find(`input[name="${err.name}"], select[name="${err.name}"]`).addClass('is-invalid').siblings('.invalid-feedback').html(err.message);
            }
        }
    });
});