$(() => {
    $.get('/api/folder/content?folder_id=1', function(data) {
        console.log(data);
    });

});