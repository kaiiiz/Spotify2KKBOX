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
                status = data.response.status
                msg = data.response.msg
                filename = data.response.filename
                if (status == 'Success') {
                    window.location.replace('download/' + filename)
                }
            },
        })
    });
});
function get_all_playlists() {
    playlists = []
    playlists_num = $('#search_detail').children().length
    for (let i = 0; i < playlists_num; i++) {
        playlist = []
        playlist_name = $('#search_success_' + i).prop("name")
        playlist_checked = $('#search_success_' + i).find('input:checked')
        $.each(playlist_checked, function (i, track) {
            var track_data = {
                'song_artist_id': $(track).data('song_artist_id'),
                'song_album_id': $(track).data('song_album_id'),
                'song_pathname': $(track).data('song_pathname'),
                'song_song_idx': $(track).data('song_song_idx')
            }
            playlist.push(track_data)
        })
        playlists.push([playlist_name, playlist])
    }
    return playlists
}