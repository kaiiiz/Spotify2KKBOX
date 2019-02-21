$(function () {
    $('#get_sp_playlist').click(function () {
        $.ajax({
            type: 'GET',
            url: '/get/spotify_playlists',
            success: function (data) {
                status = data.response.status
                msg = data.response.msg
                data = data.response.data
                if (status == 'Failed') {
                    $("#spotify_playlist").html('<p>Failed - ' + msg + '</p>')
                    return
                }
                playlists = data.playlists.items
                html = ''
                /*
                 * <input type="checkbox" name="sp_playlist" value="{{ playlist_id }}">
                 * {{ playlist_name }}
                 */
                for (let i = 0; i < playlists.length; i++) {
                    const element = playlists[i]
                    html += `<div>`
                    html += `<input type='checkbox' name='${element.name}' value='${element.id}'>`
                    html += element.name
                    html += `</div>`
                }
                $("#spotify_playlist").html(html)
            }
        });
    });
});
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
                    log_html += '<h5>Success</h5>'
                    log_html += '<form id="search_success_' + i + '" name="' + sp_playlists[i][0] + '">'
                    log_html += '</form>'
                    log_html += '<h5>Failed</h5>'
                    log_html += '<ol id="search_failed_' + i + '">'
                    log_html += '</ol>'
                    log_html += '</div>'
                }
                $('#search_detail').html(log_html)
                var playlist_cnt = 0
                sp_playlists.forEach(sp_playlist => {
                    var done = search_in_kkbox(sp_playlist, playlist_cnt)
                    if (done) playlist_cnt++
                });
            },
        });
    });
});
function search_in_kkbox(sp_playlist, playlist_cnt) {
    playlist_name = sp_playlist[0]
    sp_playlist[1].forEach(track => {
        $.ajax({
            type: 'POST',
            url: '/search/trackdata_in_kkbox',
            data: JSON.stringify({ 'data': track }),
            contentType: 'application/json; charset=utf-8',
            cache: false,
            processData: false,
            success: function (data) {
                var track_data = data.track_data.data
                var status = data.track_data.status
                if (status == 'success') {
                    var track_name = track_data['name']
                    var track_album = track_data['album']['name']
                    var track_artist = track_data['album']['artist']['name']
                    var track_id = track_data['id']
                    var success_log = '<div>'
                    success_log += "<input type='checkbox' name='" + track_name + "' value='" + track_id + "'checked>"
                    success_log += track_name + ' - ' + track_artist + ' - ' + track_album
                    success_log += '</div>'
                    $('#search_success_' + playlist_cnt).append(success_log)
                }
                else if (status == 'failed') {
                    track_name = track_data['track']['name']
                    track_album = track_data['track']['album']['name']
                    track_artist = track_data['track']['artists'][0]['name']
                    $('#search_failed_' + playlist_cnt).append('<li>' + track_name + ' - ' + track_artist + ' - ' + track_album + '</li>')
                }
            },
        });
    });
    return 1
}