/*
 * Function of press the 'Convert' button
 * This function bind button to an JQuery AJAX function
 * After click the button, AJAX will post /convert_playlist
 */
$(function () {
    $('#convert_btn').click(function() {
        var form_data = new FormData($('#convert_playlist')[0]);
        $.ajax({
            type: 'POST',
            url: '/convert_playlist',
            data: form_data,
            contentType: false,
            cache: false,
            processData: false,
            success: function (data) {
                console.log('aaa')
            },
        });
    });
});
/*
 * Function of press the 'Get playlist' button
 * This function bind button to an JQuery AJAX function
 * After click the button, AJAX will query /get/spotify/playlist and get the playlists of user
 */
$(function () {
    $('a#get_sp_playlist').bind(
        'click',
        function() {
            $.getJSON(
                $SCRIPT_ROOT + '/get/spotify/playlist', //url
                {}, // url parameter
                function (data) {
                    if (data.status == 'failed') {
                        $("#convert_playlist").html('<p>Check auth failed! Please login spotify!</p>')
                        return
                    }
                    playlist = data.playlist.items
                    html = ''
                    for (let i = 0; i < playlist.length; i++) {
                        const element = playlist[i];
                        /*
                         * <input type="checkbox" name="sp_playlist" value="{{ playlist_id }}">
                         * {{ Playlist name }}
                         * <a name="sp_playlist_detail_btn" href="#" id="{{ playlist_id }}">Detail</a>
                         * <br>
                         * <div id="sp_playlist_track_detail_{{ playlist_id }}"></div>
                         */
                        html += "<div>"
                        html += "<input type='checkbox' name='" + element.name + "' value='" + element.id + "'>" + element.name;
                        html += "<a name='sp_playlist_detail_btn' href=# id='" + element.id + "'>Detail</a></br>";
                        html += "<div id='sp_playlist_track_detail_" + element.id + "'></div>";
                        html += "</div>"
                    }
                    $("#convert_playlist").html(html)
                    bindIDToButton();
                } // return function
            );
            return false;
        }
    );
});
/*
 * Function of press the 'Detail' button next to the playlist name
 * This function bind all playlist-id to button
 * After click the button, AJAX will query /get/spotify/playlist/track and get all tracks of playlist
 */
function bindIDToButton() {
    btn_list = $('a[name="sp_playlist_detail_btn"]')
    btn_num = $('a[name="sp_playlist_detail_btn"]').length
    for (let i = 0; i < btn_num; i++) {
        const btn_id = btn_list[i].id
        btn = 'a#' + btn_id
        $(btn).bind(
            'click',
            function () {
                $.getJSON(
                    $SCRIPT_ROOT + '/get/spotify/playlist/track', //url
                    {
                        playlist_id: btn_id
                    }, // url parameter
                    function (data) {
                        detail_div = $('div#sp_playlist_track_detail_' + btn_id)
                        tracks = data.tracks // a list contain every songs in playlist
                        html = '<ol>'
                        for (let n = 0; n < tracks.length; n++) {
                            const element = tracks[n];
                            html += "<li>" + element.track.name + "</li>"
                        }
                        html += '</ol>'
                        detail_div.html(html)
                    } // return function
                );
                return false;
            }
        )
    }
}