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
                $('#kbl_status').html(response.status)
                $('#kbl_kkbox_ver').html(response.data.kkbox_ver)
                $('#kbl_package_ver').html(response.data.package_ver)
                $('#kbl_package_descr').html(response.data.package_descr)
                $('#kbl_package_packdate').html(response.data.package_packdate)
                $('#step2_status').removeClass('label-failed')
                $('#step2_status').addClass('label-success')
            }
            else if (response.status == "failed") {
                $('#kbl_status').html(response.msg)
                $('#step2_status').removeClass('label-success')
                $('#step2_status').addClass('label-failed')
            }
            bar.setAttribute('hidden', 'hidden');
        }
    });
});