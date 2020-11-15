const ws = new WebSocket('ws://31.134.153.18:8765');
const sendMessage = (msg) => {
    ws.send(msg);
    return false;
}
ws.onopen = function (e) {
    addMessage("😋");
}
ws.onclose = function (event) {
    addMessage('Ой, мне пора... 🏃‍♀️');
    if (event.wasClean) {
        console.log(event)
    }
};
ws.onerror = function (error) {
    addMessage('Ой... ⚠️');
    console.log(`[error] ${error.message}`)
};
ws.onmessage = function (event) {
    addMessage(event.data);
};

var $messages = $('.messages-content'),
    d, h, m,
    i = 0;

$(window).load(function () {
    $messages.mCustomScrollbar();
});

function updateScrollbar() {
    $messages.mCustomScrollbar("update").mCustomScrollbar('scrollTo', 'bottom', {
        scrollInertia: 10,
        timeout: 0
    });

}

function setDate() {
    d = new Date()
    if (m != d.getMinutes()) {
        m = d.getMinutes();
        $('<div class="timestamp">' + d.getHours() + ':' + m + '</div>').appendTo($('.message:last'));
    }
}

function insertMessage() {
    const msg = $('.message-input').val();
    if ($.trim(msg) == '') {
        return false;
    }
    sendMessage(msg);
    $('<div class="message message-personal">' + msg + '</div>').appendTo($('.mCSB_container')).addClass('new');
    setDate();
    $('.message-input').val(null);
    updateScrollbar();
}

$('.message-submit').click(function () {
    insertMessage();
});

$(window).on('keydown', function (e) {
    if (e.which == 13) {
        insertMessage();
        return false;
    }
});

function addMessage(text) {
    if ($('.message-input').val() != '') {
        return false;
    }
    $('<div class="message loading new"><figure class="avatar"><img src="https://i.pinimg.com/236x/29/4c/b3/294cb357c2ae3576ebd6f7c2605cc095.jpg" /></figure><span></span></div>').appendTo($('.mCSB_container'));
    updateScrollbar();

    setTimeout(function () {
        $('.message.loading').remove();
        $('<div class="message new"><figure class="avatar"><img src="https://i.pinimg.com/236x/29/4c/b3/294cb357c2ae3576ebd6f7c2605cc095.jpg" /></figure>' + text + '</div>').appendTo($('.mCSB_container')).addClass('new');
        setDate();
        updateScrollbar();
        i++;
    }, 1000 + (Math.random() * 20) * 100);
}