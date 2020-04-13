function validateInput(input) {
    var checks = true
    var expression = /[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)?/gi;
    var regex = new RegExp(expression);
    if(!(regex.test(input))) {
        $("#information").empty();
        $(document).find("#information").append("<div id='alert' class='alert alert-danger' role='alert'>The URL provided doesn't follow the correct format. Try again with another URL.</div>").hide().fadeIn(1000);
        checks = false
    }
    var request = new XMLHttpRequest();
    request.open('GET', 'http://' + input, true);
    request.onreadystatechange = function() {
        if(request.readyState === 4) {
            if(request.status === 404) {
                $("#information").empty();
                $(document).find("#information").append("<div class='alert alert-danger' role='alert'>The URL you entered responded with a 404 error. Try again with another URL.</div>").hide().fadeIn(1000);
                checks = false
            }
        }
    }
    return checks
}

$(document).ready(function() {
    $("#searchButton").on("click", function(evt) {
        evt.preventDefault();
        var inputOK = true;
        var input = $("#URL").val()
        if(validateInput(input)) {
            $("#information").empty();
            if($('#custom'). is(':checked')) {
                var iterations = $('#iterations').val();
                if(!(/^\d+$/.test(iterations))) {
                    $(document).find("#information").append("<div class='alert alert-danger' role='alert'>The number of iterations your entered is invalid, please try again.</div>").hide().fadeIn(1000);
                    inputOK = false;
                }
            }
            if(inputOK) {
                $(document).find("#information").append("<div class='alert alert-success' role='alert'>Moore's maps is building your site map, please wait...</div>").hide().fadeIn(1000);
                $('form').submit();
            }
        }else {
            console.log("URL inputted incorrectly.")
        }
        
    });
});