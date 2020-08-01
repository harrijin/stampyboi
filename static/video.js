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



function seekVideo(sec) {
    var player = document.getElementById("player-vid");
    player.pause();
    player.currentTime = sec;
    player.play();
}
