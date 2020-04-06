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
            console.log(error);
        }
    });
    
    //send AJAX request to get the links of the pages scraped and display the links with the page name
    //TO BE EDITED AND INCORPORATED ANOTHER WAY INTO TREE.
//    $.ajax({
//        type: 'GET',
//        url: '/getLinks',
//        contentType: 'application/json; charset=utf-8',
//        success: function(response) {
//            var data = JSON.parse(response)
//            var insert = $(document).find('#links')
//            for(i=0; i < data.length; i++) {
//                if (data[i].name.indexOf("Title Not Found") >= 0) {
//                    insert.append('<a href="' + data[i].link + '"><p>' + data[i].name + '</p></a>')
//                } else {
//                    var displayName = (data[i].name).replace(/[0-9]/g, '');
//                    if(displayName == "") {
//                        displayName = "Unknown URL type"
//                    }
//                    insert.append('<a href="' + data[i].link + '"><p>' + displayName + '</p></a>')
//                }
//            }
//        },
//        error: function(error) {
//            console.log(error);
//        }
//    });
    
    //send AJAX request and wait for reply from the server.
    $.ajax({
        type: 'GET',
        url: '/getJSON',
        contentType: 'application/json; charset=utf-8',
        success: function(response) {
            var data = JSON.parse(response);
            var root = data.name;
            $(document).find("#tree").append("<ul id='structure'></ul>");
            var children = data.children;
            var layers = 0;
            var idCounter = 0;
            for(i=0;i<children.length;i++) {
                var insert = $(document).find("#structure");
                if(children[i].hasOwnProperty("children")) {
                    idCounter++;
                    var parentID = "layer" + idCounter;
                    var parentIDchild = "layer" + idCounter + "c"
                    childrenQueue.push({parentID: parentID, children:children[i].children});
                    if(children[i].name.indexOf("Title Not Found") >= 0) {
                        insert.append("<li><span class='pointer' id='" + parentIDchild + "'>" + children[i].name + "</span></li>");
                    } else {
                        var displayName = (children[i].name).replace(/[0-9]/g, '')
                        if(displayName == "") {
                            displayName = "Unknown URL type"
                        }
                        insert.append("<li><span class='pointer' id='" + parentIDchild + "'>" + displayName + "</span></li>");
                    }
                    insert = $(document).find("#" + parentIDchild)
                    insert.append("<ul class='children' id='" + parentID + "'></ul>");
                }else {
                    if(children[i].name.indexOf("Title Not Found") >= 0) {
                        insert.append("<li>" + children[i].name + "</li>");  
                    } else {
                        var displayName = (children[i].name).replace(/[0-9]/g, '')
                        if(displayName == "") {
                                displayName = "Unknown URL type"
                            }
                        insert.append("<li>" + displayName + "</li>"); 
                    }
                    
                }
            }
            while(layers < childrenQueue.length) {
                layer = childrenQueue[layers];
                children = layer.children;
                var location = $(document).find("#" + layer.parentID);
                for(i=0;i<children.length;i++) {
                    if(children[i].hasOwnProperty("children")) {
                        idCounter++;
                        var parentID = "layer" + idCounter;
                        var parentIDchild = "layer" + idCounter + "c"
                        childrenQueue.push({parentID: parentID, children:children[i].children});
                        if(children[i].name.indexOf("Title Not Found") >= 0) {
                            location.append("<li><span class='pointer' id='" + parentIDchild + "'>" + children[i].name + "</span></li>");
                        } else {
                            var displayName = (children[i].name).replace(/[0-9]/g, '')
                            if(displayName == "") {
                                displayName = "Title not obtained by scraper";
                            }
                            location.append("<li><span class='pointer' id='" + parentIDchild + "'>" + displayName + "</span></li>");
                        }
                        location = $(document).find("#" + parentIDchild)
                        location.append("<ul class='children' id='" + parentID + "'></ul>");
                    }else {
                        if(children[i].name.indexOf("Title Not Found") >= 0) {
                            location.append("<li>" + children[i].name + "</li>");
                        } else {
                            var displayName = (children[i].name).replace(/[0-9]/g, '');
                            if(displayName == "") {
                                displayName = "Title not obtained by scraper";
                            }
                            location.append("<li>" + displayName + "</li>");
                        }
                       
                    }
                }
                layers++;
            }
            $('body').on('click', '.pointer', function(e) {
                this.parentElement.querySelector(".children").classList.toggle("active");
                this.classList.toggle("pointer-down");
                e.stopPropagation();
            });
        },
        error: function(error) {
            console.log(error);
        }
    });
    
});

