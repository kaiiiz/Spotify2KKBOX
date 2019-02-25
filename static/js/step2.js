$(function () {
    var bar = document.getElementById('js-progressbar');
    UIkit.upload('.js-upload', {
        url: '/upload_kbl',
        multiple: true,
        loadStart: function (e) {
            bar.removeAttribute('hidden');
            bar.max = e.total;
            bar.value = e.loaded;
        },
        progress: function (e) {
            bar.max = e.total;
            bar.value = e.loaded;
        },
        loadEnd: function (e) {
            bar.max = e.total;
            bar.value = e.loaded;
        },
        completeAll: function () {
            response = JSON.parse(arguments[0].response).response
            if (response.status == "success") {
                $('#kbl_kkbox_ver').html(response.data.kkbox_ver)
                $('#kbl_package_ver').html(response.data.package_ver)
                $('#kbl_package_descr').html(response.data.package_descr)
                $('#kbl_package_packdate').html(response.data.package_packdate)
                $('#step2_status').removeClass('uk-label-danger')
                $('#step2_status').addClass('uk-label-success')
                $('#step2_status').attr('uk-tooltip', response.msg)
                $('#step2_status').html('SUCCESS')
            }
            else if (response.status == "failed") {
                $('#step2_status').removeClass('uk-label-success')
                $('#step2_status').addClass('uk-label-danger')
                $('#step2_status').attr('uk-tooltip', response.msg)
                $('#step2_status').html('FAILED')
            }
            bar.setAttribute('hidden', 'hidden');
        }
    });
});