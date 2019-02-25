$(function () {
    $('#get_sp_playlist').click(function () {
        $.ajax({
            type: 'GET',
            url: '/get/spotify_playlists',
            success: function (data) {
                var status = data.response.status
                var msg = data.response.msg
                var data = data.response.data
                // failed
                if (status == 'failed') {
                    $('#step3_status').removeClass('uk-label-success')
                    $('#step3_status').addClass('uk-label-danger')
                    $('#step3_status').attr('uk-tooltip', msg)
                    $('#step3_status').html('FAILED')
                    return
                }
                // success
                $('#step3_status').removeClass('uk-label-danger')
                $('#step3_status').addClass('uk-label-success')
                $('#step3_status').attr('uk-tooltip', msg)
                $('#step3_status').html('SUCCESS')
                var playlists = data.playlists.items
                var html = ''
                html += `
                        <table class="uk-table uk-table-hover uk-table-middle uk-table-divider" id="sp_playlists">
                            <thead>
                                <tr>
                                    <th class="uk-table-shrink"><input class="uk-checkbox" type='checkbox' id="sp_playlists_checkall"></input></th>
                                    <th class="uk-table-shrink uk-text-center">Cover</th>
                                    <th class="uk-table-expand">Playlist name</th>
                                </tr>
                            </thead>
                            <tbody>
                        `
                for (let i = 0; i < playlists.length; i++) {
                    const element = playlists[i]
                    const playlist_cover = element['images'][0].url
                    html += `
                                <tr>
                                    <td><input class="uk-checkbox" type='checkbox' name='${element.name}' value='${element.id}'></td>
                                    <td><img class="uk-preserve-width" src="${playlist_cover}" width="60" alt=""></td>
                                    <td>${element.name}</td>
                                </tr>
                            `
                }
                html += `
                            </tbody>
                        </table>
                        `
                $("#sp_playlists").addClass('uk-margin-top')
                $("#sp_playlists").html(html)
                $('#sp_playlists_checkall').click(function () {
                    $('#sp_playlists tbody input:checkbox').prop('checked', this.checked)
                })
            }
        });
    });
});
$(function () {
    $('#search_btn').click(function () {
        var form_data = new FormData($('#sp_playlists')[0]);
        // Create frame
        $('#search_detail').empty()
        var html = ''
        var playlist_cnt = 0
        for (var pair of form_data.entries()) {
            playlist_name = pair[0]
            html += `
                    <div id="search_log_${playlist_cnt}" class="uk-card uk-card-default uk-card-body uk-margin-bottom">
                        <h3 class="uk-grid-collapse" uk-grid>
                            <div class="uk-text-left uk-width-expand">
                                <span>${playlist_name}</span>
                            </div>
                            <div class="uk-text-right uk-width-auto">
                                <span id="search_progress_${playlist_cnt}">0</span>
                                <span>/</span>
                                <span id="search_songnum_${playlist_cnt}">0</span>
                            </div>
                        </h3>
                        <ul uk-accordion="multiple: true">
                            <li>
                                <a class="uk-accordion-title" href="#">Success</a>
                                <table class="uk-table uk-table-hover uk-table-middle uk-table-divider uk-accordion-content">
                                    <thead>
                                        <tr>
                                            <th class="uk-table-shrink"><input class="uk-checkbox" type='checkbox' id="search_checkall_${playlist_cnt}" checked></input></th>
                                            <th class="uk-table-shrink uk-text-center">Cover</th>
                                            <th class="uk-width-1-3">Track</th>
                                            <th class="uk-width-1-3">Artist</th>
                                            <th class="uk-width-1-3">Album</th>
                                            <th class="uk-table-shrink">URL</th>
                                        </tr>
                                    </thead>
                                    <tbody id="search_success_${playlist_cnt}">
                                    </tbody>
                                </table>
                            </li>
                            <li>
                                <a class="uk-accordion-title" href="#">Failed</a>
                                <table class="uk-table uk-table-hover uk-table-middle uk-table-divider uk-accordion-content">
                                    <thead>
                                        <tr>
                                            <th class="uk-table-shrink"><input class="uk-checkbox" type='checkbox' disabled></input></th>
                                            <th class="uk-table-shrink uk-text-center">Cover</th>
                                            <th class="uk-width-1-3">Track</th>
                                            <th class="uk-width-1-3">Artist</th>
                                            <th class="uk-width-1-3">Album</th>
                                            <th class="uk-table-shrink">URL</th>
                                        </tr>
                                    </thead>
                                    <tbody id="search_failed_${playlist_cnt}">
                                    </tbody>
                                </table>
                            </li>
                        </ul>
                    </div>
                    `
            playlist_cnt += 1
        }
        $('#search_detail').html(html)
        $(`#search_log_${playlist_cnt-1}`).removeClass('uk-margin-bottom')
        for (let i = 0; i < playlist_cnt; i++) {
            $('#search_checkall_' + i).click(function () {
                $(`#search_success_${i} input:checkbox`).prop('checked', this.checked)
            })
        }
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
                if (status == "failed") {
                    $("#search_detail").html('<p>Failed - ' + msg + '</p>')
                    return
                }
                else {
                    var playlist_cnt = 0
                    sp_playlists.forEach(sp_playlist => {
                        var track_num = sp_playlist[1].length
                        $('#search_songnum_' + playlist_cnt).html(track_num)
                        var done = search_in_kkbox(sp_playlist, playlist_cnt)
                        if (done) playlist_cnt++
                    });
                }
            },
        });
    });
});
function search_in_kkbox(sp_playlist, playlist_cnt) {
    var search_progress = 0
    sp_playlist[1].forEach(track => {
        $.ajax({
            type: 'POST',
            url: '/search/kbl_attribute',
            data: JSON.stringify({ 'sp_data': track }),
            contentType: 'application/json; charset=utf-8',
            cache: false,
            processData: false,
            success: function (data) {
                var status = data.response.status
                var msg = data.response.msg
                var track_data = data.response.data.track_data
                var kbl_attr = data.response.data.kbl_attr
                var html = ''
                if (status == 'success') {
                    var track_name = track_data['name']
                    var track_album = track_data['album']['name']
                    var track_artist = track_data['album']['artist']['name']
                    var track_cover = track_data['album']['images'][0]['url']
                    var track_url = track_data['url']
                    var song_pathname = kbl_attr['song_pathname']
                    var song_artist_id = kbl_attr['song_artist_id']
                    var song_album_id = kbl_attr['song_album_id']
                    var song_song_idx = kbl_attr['song_song_idx']
                    html += `
                                <tr>
                                    <td>
                                        <input class="uk-checkbox" type='checkbox' checked
                                         data-song_album_id='${song_album_id}' data-song_artist_id='${song_artist_id}'
                                         data-song_pathname='${song_pathname}' data-song_song_idx='${song_song_idx}'>
                                    </td>
                                    <td><img class="uk-preserve-width" src="${track_cover}" width="60" alt=""></td>
                                    <td>${track_name}</td>
                                    <td>${track_artist}</td>
                                    <td>${track_album}</td>
                                    <td><a target="_blank" class="uk-link-text" href="${track_url}"><span uk-icon="arrow-right"></span></a></td>
                                </tr>
                            `
                    $('#search_success_' + playlist_cnt).append(html)
                }
                else {
                    var track_name = track_data['track']['name']
                    var track_album = track_data['track']['album']['name']
                    var track_artist = track_data['track']['artists'][0]['name']
                    var track_cover = track['track']['album']['images'][0]['url']
                    var track_url = track['track']['external_urls']['spotify']
                    html += `
                                <tr>
                                    <td><input class="uk-checkbox" type='checkbox' disabled></td>
                                    <td><img class="uk-preserve-width" src="${track_cover}" width="60" alt=""></td>
                                    <td>${track_name}</td>
                                    <td>${track_artist}</td>
                                    <td>${track_album}</td>
                                    <td><a target="_blank" class="uk-link-text" href="${track_url}"><span uk-icon="arrow-right"></span></a></td>
                                </tr>
                            `
                    $('#search_failed_' + playlist_cnt).append(html)
                }
                search_progress++
                $('#search_progress_' + playlist_cnt).html(search_progress)
            },
        });
    });
    return 1
}