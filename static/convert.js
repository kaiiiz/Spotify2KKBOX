var source = new EventSource("/convert");
source.addEventListener(
    'abc',
    function (event) {
        $('#text').text(event.data)
        if (event.data == 100) {
            source.close()
        }
    }
)
source.onmessage = function (event) {
    $('.progress-bar').css('width', event.data + '%').attr('aria-valuenow', event.data);
    $('.progress-bar-label').text(event.data + '%');
}