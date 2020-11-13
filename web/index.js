const ws = new WebSocket('ws://31.134.153.18:8765');
const sendMessage = (msg) => {
    ws.send(msg);
    return false;
}
ws.onopen = function (e) {
    console.log("[open] Соединение установлено");
    console.log("Отправляем данные на сервер");
}
ws.onclose = function (event) {
    if (event.wasClean) {
        console.log(event)
    } else {
        console.log('[close] Соединение прервано');
    }
};
ws.onerror = function (error) {
    console.log(`[error] ${error.message}`);
};
ws.onmessage = function (event) {
    addMessage(event.data);
    console.log(event.data)
};

var $messages = $('.messages-content'),
    d, h, m,
    i = 0;

$(window).load(function () {
    $messages.mCustomScrollbar();
    // setTimeout(function () {
    // fakeMessage();
    // }, 100);
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
    // setTimeout(function () {
    // fakeMessage();
    // }, 1000 + Math.random() * 20 * 100);
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

// var Fake = [
//     'Hi there, I\'m Fabio and you?',
//     'Nice to meet you',
//     'How are you?',
//     'Not too bad, thanks',
//     'What do you do?',
//     'That\'s awesome',
//     'Codepen is a nice place to stay',
//     'I think you\'re a nice person',
//     'Why do you think that?',
//     'Can you explain?',
//     'Anyway I\'ve gotta go now',
//     'It was a pleasure chat with you',
//     'Time to make a new codepen',
//     'Bye',
//     ':)'];


// function fakeMessage() {
//     if ($('.message-input').val() != '') {
//     return false;
//     }
//     $('<div class="message loading new"><figure class="avatar"><img src="https://s3-us-west-2.amazonaws.com/s.cdpn.io/156381/profile/profile-80.jpg" /></figure><span></span></div>').appendTo($('.mCSB_container'));
//     updateScrollbar();

//     setTimeout(function () {
//     $('.message.loading').remove();
//     $('<div class="message new"><figure class="avatar"><img src="https://s3-us-west-2.amazonaws.com/s.cdpn.io/156381/profile/profile-80.jpg" /></figure>' + Fake[i] + '</div>').appendTo($('.mCSB_container')).addClass('new');
//     setDate();
//     updateScrollbar();
//     i++;
//     }, 1000 + Math.random() * 20 * 100);

// }