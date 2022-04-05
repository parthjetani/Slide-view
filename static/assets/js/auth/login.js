$(() => {
    $("#login-form").on('submit', function(event) {
        event.preventDefault();
        var username = $(this).find('#username').val();
        var password = $(this).find('#password').val();
        if (username.length === 0 || password.length === 0) {
            $("#error-message").html('Please enter username or password').show();
            $("#username, #password").addClass('is-invalid');
        }else{
            $.post('/auth/login', {username, password}, function(response) {
                if (response.type === 'success') {
                    var url = new URL(window.location.href);
                    if (url.searchParams.has('next')) {
                        window.location.href = url.searchParams.get('next');
                    } else {
                        window.location.href = '/';
                    }
                }else{
                    $("#error-message").html(response.message).show();
                    $("#username, #password").addClass('is-invalid');
                }
            }).fail(function(err) {
                $("#error-message").html('Server side error. Please try again later').show();
            });
        }
    });
});