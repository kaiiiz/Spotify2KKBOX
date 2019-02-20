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