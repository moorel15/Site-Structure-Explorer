var linksRecieved = []
//check if the input is in the pages returned
function checkSearch(input, linksRecieved) {
    for(var i=0; i < linksRecieved.length; i++) {
        if(input == linksRecieved[i].title) {
            return true;
        }
    }
    return false;
}

//when document is ready perform the following to construct content.
$(document).ready(function() {
    //set up to be accepted by the server when sending the request.
    var csrf_token = $('meta[name=csrf-token]').attr('content');
    var pages = 0
    var childrenQueue = []

    //set up the ajax in order for it to be accepted by the server.
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            }
        }
    });

    //send AJAX request for stats and wait then display dynamically
    //display the statistics when recieved from the server
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

    //get the links from the server using ajax get request and then wait for server.
    //when recieved store all links in an array of objects to be used later on. when adding links to the tree. 
    $.ajax({
        type: 'GET',
        url: '/getLinks',
        contentType: 'application/json; charset=utf-8',
        success: function(response) {
            var data = JSON.parse(response)
            for(i=0; i < data.length; i++) {
                linksRecieved.push({title: data[i].name, link: data[i].link})
            }
        },
        error: function(error) {
            console.log(error);
        }
    });

    //send AJAX request and wait for reply from the server.
    //once recieved the JSON format, parse the json and work with it.
    $.ajax({
        type: 'GET',
        url: '/getJSON',
        contentType: 'application/json; charset=utf-8',
        success: function(response) {
            var data = JSON.parse(response);
            //get the root directory
            var root = data.name;
            $(document).find("#tree").append("<ul id='structure'></ul>");
            var children = data.children;
            var layers = 0;
            var idCounter = 0;
            var href = "";
            //for each in children. check if it has children if it does then add them to a queue, and add element, otherwise add an element directly.
            for(i=0;i<children.length;i++) {
                for(var j=0; j < linksRecieved.length; j++) {
                    if(children[i].name == linksRecieved[j].title) {
                        href = linksRecieved[j].link;
                        break;
                    }
                }
                var insert = $(document).find("#structure");
                if(children[i].hasOwnProperty("children")) {
                    idCounter++;
                    var parentID = "layer" + idCounter;
                    var parentIDchild = "layer" + idCounter + "c"
                    childrenQueue.push({parentID: parentID, children:children[i].children});
                    if(children[i].name.indexOf("Title Not Found") >= 0) {
                        insert.append("<li><span class='pointer' id='" + parentIDchild + "'>" + children[i].name + " - <a href='" + href + "' target='_blank'>Link</a></span></li>");
                    }else {
                        var displayName = (children[i].name).replace(/[0-9]/g, '')
                        if(displayName == "") {
                            displayName = "Title not obtained by scraper";
                        }
                        insert.append("<li><span class='pointer' id='" + parentIDchild + "'>" + displayName + " - <a href='" + href + "' target='_blank'>Link</a></span></li>");
                    }
                    insert = $(document).find("#" + parentIDchild)
                    insert.append("<ul class='children' id='" + parentID + "'></ul>");
                }else {
                    if(children[i].name.indexOf("Title Not Found") >= 0) {
                        insert.append("<li>" + children[i].name + " - <a href='" + href + "' target='_blank'>Link</a></li>");  
                    }else {
                        var displayName = (children[i].name).replace(/[0-9]/g, '')
                        if(displayName == "") {
                            displayName = "Title not obtained by scraper";
                        }
                        insert.append("<li>" + displayName + " - <a href='" + href + "' target='_blank'>Link</a></li>"); 
                    }
                }
            }

            //repeat the above stages for all chidren in the queue. 
            while(layers < childrenQueue.length) {
                layer = childrenQueue[layers];
                children = layer.children;
                var location = $(document).find("#" + layer.parentID);
                for(i=0;i<children.length;i++) {
                    for(var j=0; j < linksRecieved.length; j++) {
                        if(children[i].name == linksRecieved[j].title) {
                            href = linksRecieved[j].link;
                            break;
                        }
                    }
                    if(children[i].hasOwnProperty("children")) {
                        idCounter++;
                        var parentID = "layer" + idCounter;
                        var parentIDchild = "layer" + idCounter + "c"
                        childrenQueue.push({parentID: parentID, children:children[i].children});
                        if(children[i].name.indexOf("Title Not Found") >= 0) {
                            location.append("<li><span class='pointer' id='" + parentIDchild + "'>" + children[i].name + " - <a href='" + href + "' target='_blank'>Link</a></span></li>");
                        }else {
                            var displayName = (children[i].name).replace(/[0-9]/g, '')
                            if(displayName == "") {
                                displayName = "Title not obtained by scraper";
                            }
                            location.append("<li><span class='pointer' id='" + parentIDchild + "'>" + displayName + " - <a href='" + href + "' target='_blank'>Link</a></span></li>");
                        }
                        location = $(document).find("#" + parentIDchild)
                        location.append("<ul class='children' id='" + parentID + "'></ul>");
                    }else {
                        if(children[i].name.indexOf("Title Not Found") >= 0) {
                            location.append("<li>" + children[i].name + " - <a href='" + href + "' target='_blank'>Link</a></li>");
                        }else {
                            var displayName = (children[i].name).replace(/[0-9]/g, '');
                            if(displayName == "") {
                                displayName = "Title not obtained by scraper";
                            }
                            location.append("<li>" + displayName + " - <a href='" + href + "' target='_blank'>Link</a></li>");
                        }   
                    }
                }
                layers++;
            }
            //for all the pointers - create the interactivty of dropping down to show list of children pages if they have them.
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

    //if downnload button clicked then chek the input is valid if so submit the form, otherwise show them a message to say input invalid
    $("#generateButton").on("click", function(evt) {
        evt.preventDefault();
        var input = $("#node").val();
        if(!(input.includes("Title Not Found"))) {
            input = (input + "0").replace(/\s/g, '');
        }   
        var location = $(document).find("#information")
        if(checkSearch(input, linksRecieved)) {
            location.append("<div class='alert alert-success' role='alert'>Check your downloads for your graphical representation</div>").hide().fadeIn(1000).fadeOut(1000);
            $('form').submit();
        }else {
            location.append("<div class='alert alert-danger' role='alert'>The name you have inputted does not match. Try again</div>").hide().fadeIn(1000).fadeOut(1000);
        }
    });
});

