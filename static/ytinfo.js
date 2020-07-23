function getInfo(id) {
    const ytApiKey = getYtDataAPIKey();
    console.log("https://www.googleapis.com/youtube/v3/videos?part=snippet&id=" + id + "&key=" + ytApiKey);

    $.get("https://www.googleapis.com/youtube/v3/videos?part=snippet&id=" + id + "&key=" + ytApiKey, function(data) {
        const parent = document.getElementById(id);
        const info = data.items[0].snippet;

        parent.getElementsByClassName('title')[0].innerHTML = info.title;

        let channelElement = parent.getElementsByClassName('channel')[0];
        channelElement.innerHTML = info.channelTitle;
        
        let dateElement = parent.getElementsByClassName('date')[0];
        let date = new Date(info.publishedAt);
        let options = {month: 'short', day: 'numeric', year: 'numeric'};
        dateElement.innerHTML = date.toLocaleDateString(date, options);

        let thumbElement = parent.getElementsByClassName('thumbnail')[0];
        thumbElement.setAttribute('src', info.thumbnails.default.url);
    });
}