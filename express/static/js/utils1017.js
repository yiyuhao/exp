/**
 * Created by yiwen on 2/6/17.
 */
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrfToken = getCookie('csrftoken');
var ajaxSetup = function () {
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            // if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            if (!this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrfToken);
            }
        }
    });

    $body = $("body");
    $(document).on({
        ajaxStart: function () {
            //console.log("start");
            $body.addClass("loading");
        },
        ajaxStop: function () {
            //console.log("stop");
            $body.removeClass("loading");
        }

    });
};


function ajax_return_alert(elem, css, message) {
    elem.attr('class', 'alert alert-' + css).text(message).fadeIn(100).fadeOut(100).fadeIn(100);
}

function sound_alert(title, body_text) {
    var error_modal = $('#error_modal').modal('hide');
    $('#sound_alert').get(0).play();
    $('#sound_alert_modal_title').text(title);
    $('#sound_alert_modal_message').text(body_text);
    error_modal.modal('show');
    $('#error_modal_close_btn').focus();
}

function sound_alert2(title, body_text, sound_id) {
    var error_modal = $('#error_modal').modal('hide');
    $(sound_id).get(0).play();
    $('#sound_alert_modal_title').text(title);
    $('#sound_alert_modal_message').text(body_text);
    error_modal.modal('show');
    $('#error_modal_close_btn').focus();
}

function play_bc_sound() {
    $('#sound_bc').get(0).play();
}

function play_usps_sound() {
    $('#sound_usps').get(0).play();
}

function play_add_to_pallet_sound() {
    $('#sound_add_to_pallet').get(0).play();
}

//
// $.postJSON = function(url, data, callback, error_callback) {
//     return jQuery.ajax({
//         'type': 'POST',
//         'url': url,
//         'contentType': 'application/json',
//         'data': data,
//         'dataType': 'json',
//         'success': callback,
//         'error': error_callback
//     });
// };


function select_all_populate() {
    checkall = $('th.cb > input');
    if (checkall.length > 0) {
        checkall.click(function () {
            var is_check = $(this).prop('checked');
            $('td.cb > input').each(function () {
                $(this).prop('checked', is_check)
            });
        })
    }
}
function count_selected() {
    td_cb = $('td.cb > input');
    cnt = 0;
    if (td_cb <= 0) {
        return 0
    }
    else {
        td_cb.each(function () {
            console.log($(this).prop('checked'));
            if ($(this).prop('checked') == true) {
                cnt++;
            }
        });
        return cnt
    }
}

function set_up_datepicker() {
    if ($('.datepicker').length > 0) {
        $('.datepicker').datepicker();
    }
}