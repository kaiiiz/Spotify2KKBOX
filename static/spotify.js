/*
 * Function of press the 'Convert' button
 * This function bind button to an JQuery AJAX function
 * After click the button, AJAX will post /spotify_playlist
 */
$(function () {
    $('#search_btn').click(function () {
        var form_data = new FormData($('#spotify_playlist')[0]);
        $.ajax({
            type: 'POST',
            url: '/search/all_tracks',
            data: form_data,
            contentType: false,
            cache: false,
            processData: false,
            success: function (data) {
                var sp_playlists = data.sp_playlists
                var log_html = ''
                for (let i = 0; i < sp_playlists.length; i++) {
                    log_html += '<div id="search_log_' + i + '">'
                    log_html += '<h4>' + sp_playlists[i][0] + '</h4>'
                    log_html += '<div id="success_' + i + '">'
                    log_html += '<h5>Success</h5>'
                    log_html += '</div>'
                    log_html += '<div id="failed_' + i + '">'
                    log_html += '<h5>Failed</h5>'
                    log_html += '</div>'
                    log_html += '</div>'
                }
                $('#search_detail').html(log_html)
                sp_playlists.forEach(sp_playlist => {
                    search_in_kkbox(sp_playlist)
                    // console.log(sp_playlist)
                });
            },
        });
    });
});
function search_in_kkbox(sp_playlist) {
    playlist_name = sp_playlist[0]
    playlist_cnt = 0
    sp_playlist[1].forEach(track => {
        $.ajax({
            type: 'POST',
            url: '/search/trackdata_in_kkbox',
            data: JSON.stringify({ 'data': track }),
            contentType: 'application/json; charset=utf-8',
            cache: false,
            processData: false,
            success: function (data) {
                console.log(data.track_data.status)
            },
        });
    });
}
/*
 * Function of press the 'Get playlist' button
 * This function bind button to an JQuery AJAX function
 * After click the button, AJAX will query /get/spotify/playlist and get the playlists of user
 */
$(function () {
    $('a#get_sp_playlist').bind(
        'click',
        function () {
            $.getJSON(
                $SCRIPT_ROOT + '/get/spotify/playlist', //url
                {}, // url parameter
                function (data) {
                    if (data.status == 'failed') {
                        $("#spotify_playlist").html('<p>Check auth failed! Please login spotify!</p>')
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
                    $("#spotify_playlist").html(html)
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