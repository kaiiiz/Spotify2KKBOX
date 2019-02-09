/*
 * Function of press the 'Upload' button
 * This function bind button to an JQuery AJAX function
 * After click the button, AJAX will upload kbl file and get kbl information
 */
$(function () {
    $('#upload_kbl_btn').click(function() {
        var form_data = new FormData($('#upload_kbl')[0]);
        $.ajax({
            type: 'POST',
            url: '/upload_kbl',
            data: form_data,
            contentType: false,
            cache: false,
            processData: false,
            success: function (data) {
                $('span#kbl_status').html(data.kbl.status)
                if (data.kbl.status == "Success") {
                    $('span#kbl_kkbox_ver').html(data.kbl.kkbox_ver)
                    $('span#kbl_package_ver').html(data.kbl.package_ver)
                    $('span#kbl_package_descr').html(data.kbl.package_descr)
                    $('span#kbl_package_packdate').html(data.kbl.package_packdate)
                }
            },
        });
    });
});