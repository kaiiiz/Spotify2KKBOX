$(function () {
    $('#upload_kbl_btn').click(function () {
        var form_data = new FormData($('#upload_kbl')[0]);
        $.ajax({
            type: 'POST',
            url: '/upload_kbl',
            data: form_data,
            cache: false,
            processData: false,
            contentType: false,
            success: function (data) {
                response = data.response
                if (response.status == "Success") {
                    $('#kbl_status').html(response.status)
                    $('#kbl_kkbox_ver').html(response.data.kkbox_ver)
                    $('#kbl_package_ver').html(response.data.package_ver)
                    $('#kbl_package_descr').html(response.data.package_descr)
                    $('#kbl_package_packdate').html(response.data.package_packdate)
                }
                else if (response.status == "Failed") {
                    $('#kbl_status').html(response.status + ' - ' + response.msg)
                }
            },
        });
    });
});