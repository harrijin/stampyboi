var player;
if (apiReady) {
    new YT.Player('player', {
        events: {
            'onReady': onPlayerReady
        }
    });
}

function onPlayerReady(event) {
    player = event.target;
    player.playVideo();
    console.log('player ready');
}

function seek(sec) {
    if (player) {
        player.seekTo(parseInt(sec), true);
    }
}

// https://stackoverflow.com/questions/1403615/use-jquery-to-hide-a-div-when-the-user-clicks-outside-of-it
$(document).mouseup(function(e) {
    var container = $(".clip-container");
    var share = $("#share");

    // if the target of the click isn't the container nor a descendant of the container
    if (!container.is(e.target) && container.has(e.target).length === 0
        && !share.is(e.target) && share.has(e.target).length === 0) {
        
        $('body').css('overflow', 'auto');
        $('.overlay').remove();
    }
});

function setActive(el) {
    $('.activeStamp').removeClass('activeStamp');
    $(el).addClass('activeStamp');
}

function shareBoi(dest){
    //dest values
    //1 - facebook
    //2 - twitter
    //3 - reddit
    var a = $('.activeStamp .timestamp').html().split(':');
    var seconds = (+a[0]) * 60 * 60 + (+a[1]) * 60 + (+a[2]);
    var link = "https://youtu.be/{{doc['id']}}?t=" + seconds;
    if(dest < 3){
        link = encodeURIComponent(link);
    } else if(dest == 3){
        link = encodeURI(link);
    }
    console.log(link);
    switch(dest){
        case 1:
            window.open("https://www.facebook.com/sharer.php?u="+link, "_blank");
        break;
        case 2:
            window.open("https://twitter.com/intent/tweet?url="+link, "_blank");
        break;
        case 3:
            window.open("https://www.reddit.com/submit?url="+link, "_blank");
        break;
        case 4:
            var dummy = document.createElement("textarea");
            document.body.appendChild(dummy);
            dummy.textContent = link;
            dummy.select();
            document.execCommand("copy");
            document.body.removeChild(dummy);
            if(!$('#copied').length){
                $('body').append("<p id='copied'>Link copied!</p>");
            }else if($('#copied').css('display')=='none' || $('#copied').css('opacity') < 1){
                $('#copied').css('display','inherit');
                $('#copied').stop(true, true);
                $('#copied').fadeTo(10, 1);
            }
            $('#copied').fadeOut(3000);
        break;
        default:
            var result = window.confirm('The timestamp you have selected has been copied to your clipboard. Redirecting you to gifs.com');
            if (result){
                var dummy = document.createElement("textarea");
                document.body.appendChild(dummy);
                var minutes = (+a[0]) * 60 + (+a[1]);
                var sec_60 = (+a[2]);
                dummy.textContent = minutes + ":" + sec_60;
                dummy.select();
                document.execCommand("copy");
                document.body.removeChild(dummy);
                window.open("https://gifs.com/watch?v={{doc['id']}}", "_blank");
            }

        break;
    }
}

function seekVideo(sec) {
    var player = document.getElementById("player-vid");
    player.pause();
    player.currentTime = sec;
    player.play();
}
