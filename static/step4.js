$(function () {
    $('#convert_btn').click(function () {
        playlist_num = $('#search_detail').children().length
        create_frame(playlist_num)
        for (let i = 0; i < playlist_num; i++) {
            var form_data = new FormData($('#search_success_' + i)[0]);
            for (var pair of form_data.entries()) {
                track_name = pair[0];
                track_id = pair[1];
                $.ajax({
                    type: 'POST',
                    url: '/convert/crawler_search_id',
                    data: JSON.stringify({ 'track_id': track_id }),
                    contentType: 'application/json; charset=utf-8',
                    cache: false,
                    processData: false,
                    success: function (data) {
                        // reply variables
                        var track_data = data.kbl.track_data
                        var kbl_data = data.kbl.kbl_data
                        var status = data.kbl.status
                        // track variables
                        var track_name = track_data['name']
                        var track_album = track_data['album']['name']
                        var track_artist = track_data['album']['artist']['name']
                        // append entry to log
                        if (status == 'success') {
                            var success_log = '<div>'
                            success_log += `<input type='checkbox'`
                            success_log += `data-song_album_id=${kbl_data['song_album_id']} `
                            success_log += `data-song_artist_id='${kbl_data['song_artist_id']}' `
                            success_log += `data-song_pathname='${kbl_data['song_pathname']}' `
                            success_log += `data-song_song_idx='${kbl_data['song_song_idx']}' checked>`
                            success_log += track_name + ' - ' + track_artist + ' - ' + track_album
                            success_log += '</div>'
                            $('#convert_success_' + i).append(success_log)
                        }
                        else if (status == 'failed') {
                            $('#convert_failed_' + i).append('<li>' + track_name + ' - ' + track_artist + ' - ' + track_album + '</li>')
                        }
                    },
                });
            }
        }
    });
});
function create_frame(playlist_num) {
    $('#convert_detail').empty()
    var convert_html = ''
    for (let i = 0; i < playlist_num; i++) {
        checked_num = $('#search_success_' + i).find('input:checked').length
        if (checked_num) {
            playlist_name = $('#search_success_' + i).prop("name")
            convert_html += '<div id="convert_log_' + i + '">'
            convert_html += '<h4>' + playlist_name + '</h4>'
            convert_html += '<h5>Success</h5>'
            convert_html += `<form id='convert_success_${i}' name='${playlist_name}'>`
            convert_html += '</form>'
            convert_html += '<h5>Failed</h5>'
            convert_html += '<ol id="convert_failed_' + i + '">'
            convert_html += '</ol>'
            convert_html += '</div>'
        }
    }
    $('#convert_detail').html(convert_html)
}
// Download
$(function () {
    $('#download_btn').click(function () {
        playlists = get_all_playlists()
        if (playlists.length == 0) return;
        $.ajax({
            type: 'POST',
            url: '/download/generate_kbl',
            data: JSON.stringify(playlists),
            contentType: 'application/json; charset=utf-8',
            cache: false,
            processData: false,
            success: function (data) {
                window.location.replace('download/' + data.reply.name)
            },
        })
    });
});
function get_all_playlists() {
    playlists = []
    num = $('#convert_detail').children().length
    for (let i = 0; i < num; i++) {
        p = []
        p_name = $('#convert_success_' + i).prop("name")
        p_checked = $('#convert_success_' + i).find('input:checked')
        $.each($('#convert_success_' + i).find('input:checked'), function (i, track) {
            var track_data = {
                'song_artist_id': $(track).data('song_artist_id'),
                'song_album_id': $(track).data('song_album_id'),
                'song_pathname': $(track).data('song_pathname'),
                'song_song_idx': $(track).data('song_song_idx')
            }
            p.push(track_data)
        })
        playlists.push([p_name, p])
    }
    return playlists
}