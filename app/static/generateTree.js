$(document).ready(function() {
    
    //set up to be accepted by the server when sending the request.
    var csrf_token = $('meta[name=csrf-token]').attr('content');
    var pages = 0
    var childrenQueue = []
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
            var insert = $(document).find("#stats")
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
    
    //send AJAX request to get the links of the pages scraped and display the links with the page name
    $.ajax({
        type: 'GET',
        url: '/getLinks',
        contentType: 'application/json; charset=utf-8',
        success: function(response) {
            var data = JSON.parse(response)
            var insert = $(document).find('#links')
            for(i=0; i < data.length; i++) {
                insert.append('<a href="' + data[i].link + '"><p>' + data[i].name + '</p></a>')
            }
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
            $(document).find("#tree").append("<ul id='structure'></ul>")
            var insert = $(document).find("#structure")
            var children = data.children
            var layers = 0
            var idCounter = 0
            for(i=0;i<children.length;i++) {
                if(children[i].hasOwnProperty("children")) {
                    idCounter++;
                    var parentID = "layer" + idCounter
                    childrenQueue.push({parentID: parentID, children:children[i].children})
                    insert.append("<li><span class='pointer'>" + children[i].name + "</span></li>")
                    insert.append("<ul class='children' id='" + parentID + "'></ul>")
                }else {
                    insert.append("<li>" + children[i].name + "</li>")
                }
            }
            while(layers < childrenQueue.length) {
                layer = childrenQueue[layers]
                children = layer.children
                console.log(children)
                var location = $(document).find("#" + layer.parentID)
                console.log(location)
                for(i=0;i<children.length;i++) {
                    if(children[i].hasOwnProperty("children")) {
                        idCounter++;
                        var parentID = "layer" + idCounter
                        childrenQueue.push({parentID: parentID, children:children[i].children})
                        location.append("<li><span class='pointer'>" + children[i].name + "</span></li>")
                        location.append("<ul class='children' id='" + parentID + "'></ul>")
                    }else {
                        location.append("<li>" + children[i].name + "</li>")
                    }
                }
                layers++;
                
                //TODO: check the tree creation section of server as not being done correctly. Therefore need to fix that. The jquery is working correctly and matching the layout of the json exported by anytree. Need to fix the tree structure though - when finished will work correctly hopefully. Could be an issue with the scraping order.
            }
        },
        error: function(error) {
            console.log(error)
        }
        
    });
    
});
