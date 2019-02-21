$(function () {
    $('#get_sp_playlist').click(function () {
        $.ajax({
            type: 'GET',
            url: '/get/spotify_playlists',
            success: function (data) {
                var status = data.response.status
                var msg = data.response.msg
                var data = data.response.data
                if (status == 'Failed') {
                    $("#spotify_playlists").html('<p>Failed - ' + msg + '</p>')
                    return
                }
                var playlists = data.playlists.items
                var html = ''
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
                $("#spotify_playlists").html(html)
            }
        });
    });
});
$(function () {
    $('#search_btn').click(function () {
        var form_data = new FormData($('#spotify_playlists')[0]);
        // Create frame
        $('#search_detail').empty()
        var html = ''
        var playlist_cnt = 0
        for (var pair of form_data.entries()) {
            playlist_name = pair[0]
            html += `<div id="search_log_${playlist_cnt}">`
            html += `<h4>${playlist_name}</h4>`
            html += `<h5>Success</h5>`
            html += `<form id="search_success_${playlist_cnt}" name="${playlist_name}"></form>`
            html += `<h5>Failed</h5>`
            html += `<ol id="search_failed_${playlist_cnt}"></ol>`
            html += `</div>`
            playlist_cnt += 1
        }
        $('#search_detail').html(html)
        $.ajax({
            type: 'POST',
            url: '/search/all_tracks_in_sp',
            data: form_data,
            contentType: false,
            cache: false,
            processData: false,
            success: function (data) {
                var status = data.response.status
                var msg = data.response.msg
                var sp_playlists = data.response.data
                if (status == "Failed") {
                    $("#search_detail").html('<p>Failed - ' + msg + '</p>')
                    return
                }
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