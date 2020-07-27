function check_spelling(){
    document.getElementById('spellcheckButton').style='display:none';
    var userIn=encodeURIComponent(document.getElementById('inputQuote').value);
    var suggestRequest = new XMLHttpRequest();
    var suggestions;
    suggestRequest.open('POST','/spellcheck', true);
    suggestRequest.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    suggestRequest.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            suggestions = JSON5.parse(this.responseText);
            if(suggestions.length > 0){
                generateSpellcheck();
                suggestions.forEach(addSuggestion);
            }
        }
    };
    suggestRequest.send("q="+userIn);

}

function generateSpellcheck(){
    let prefix = document.createElement('span');
    let form = document.createElement('form');
    let searchSrc = document.createElement('input');
    let dropdown = document.createElement('select');
    let submitButton = document.createElement('input');
    prefix.style = 'color:red';
    prefix.innerHTML = "Did you mean:";
    form.action = '/results';
    form.id = 'searchSuggestion';
    form.enctype = 'application/x-www-form-urlencoded';
    form.method = 'POST';
    form.style = 'display:inline';
    searchSrc.type = 'text';
    searchSrc.id='search_src';
    searchSrc.style='display:none'; // this line BAD (limits searching to only solr search, can't set additional options)
    searchSrc.value='none';
    searchSrc.name='search_src';
    dropdown.id='quote';
    dropdown.name='quote';
    submitButton.type='submit';
    submitButton.value='Search';
    form.appendChild(searchSrc);
    form.appendChild(dropdown);
    form.appendChild(submitButton);
    document.getElementById('spellchecking').appendChild(prefix);
    document.getElementById('spellchecking').appendChild(form);
}

function addSuggestion(suggestion){
    let option = document.createElement('option');
    suggestion = suggestion.substring('script:'.length);//gets rid of 'script:'' from query
    option.value=suggestion;
    option.innerHTML=suggestion;
    document.getElementById("quote").appendChild(option);
}

function directToVideo(info, stampIndex) {
    info.index = stampIndex;
    console.log(info)
    $.ajax({
        url: '/video',
        type: 'POST', 
        data: JSON.stringify(info),
        contentType: 'application/json',
        success: function(response) {
            document.write(response);
        }
    });
}