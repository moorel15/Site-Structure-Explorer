$(document).ready(function() {
    
    //set up to be accepted by the server when sending the request.
    var csrf_token = $('meta[name=csrf-token]').attr('content');
    var pages = 0
    $.ajaxSetup({
	    beforeSend: function(xhr, settings) {
	        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
	            xhr.setRequestHeader("X-CSRFToken", csrf_token);
	        }
	    }
	});
    //send AJAX request for stats and wait then display dynamically
    $.ajax({
        type: 'GET',
        url: '/getStats',
        contentType: 'application/json; charset=utf-8',
        success: function(response) {
            var data = JSON.parse(response)
            pages = data.pagesFound
            var insert = $(document).find(".stats")
            insert.append("<p>Number of pages found: " + data.pagesFound + "</n>")
            insert.append("<p>Time taken: " + data.minutes + " mins</p>")
            insert.append("<p>Efficiency: " + data.pagesPerMinute + " pages/min</p>")
            insert.append("<p>Number of titles not found: " + data.titleNotFound + "</p>")
            insert.append("<p>Politeness window: " + data.delay + " secs</p>")
        },
        error: function(error) {
            console.log(error)
        }
    });
    
    //send AJAX request and wait for reply from the server.
    $.ajax({
        type: 'GET',
        url: '/getJSON',
        contentType: 'application/json; charset=utf-8',
        success: function(response) {
            var data = JSON.parse(response)
            var root = data.name
            var insertIfChild = $(document).find('.tree')
            var insertNotChild = $(document).find('.tree')
            insertNotChild.append('<ul id="treeStructure"></ul>')
            insertIfChild = $(document).find('#treeStructure')
            insertNotChild = $(document).find('#treeStructure')
            insertNotChild.append('<li><span class="pointer">' + root + '</span></li>')
            while(i < pages) {
                //js object into sub jsobjects.
                //if that js object contains a children key then create a new sublist - build its children. - uses if child
                //if it doesnt have a children key then create a regular list item in current level - uses if not child 
            }
        },
        error: function(error) {
            console.log(error)
        }
        
    });
    
});
