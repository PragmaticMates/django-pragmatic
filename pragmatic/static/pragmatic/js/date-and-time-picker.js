jQuery(document).ready(function ($) {
    'use strict';
    init_date_and_time_pickers();
});

function init_date_and_time_pickers() {
    function getKeyBinds(input) {
        return {
            left: function (widget) {
                var selectionStart = input[0].selectionStart;
                if (selectionStart > 0) {
                    input[0].selectionStart = selectionStart - 1;
                    input[0].selectionEnd = input[0].selectionStart;
                }
            },
            right: function (widget) {
                var selectionStart = input[0].selectionStart;
                if (selectionStart < input[0].value.length) {
                    input[0].selectionStart = selectionStart + 1;
                    input[0].selectionEnd = input[0].selectionStart;
                }
            }
        };
    }


    $('.datetime-picker, [name$="datetime"], .datetimeinput').each(function () {
        $(this).attr('autocomplete', 'off');
        $(this).datetimepicker({
            format: 'DD.MM.YYYY HH:mm',
            // debug: true,
            focusOnShow: false,
            keyBinds: getKeyBinds($(this))
        });
    });

    $('.date-picker, .dateinput').each(function () {
        $(this).attr('autocomplete', 'off');
        $(this).datetimepicker({
            format: 'DD.MM.YYYY',
            // debug: true,
            focusOnShow: false,
            keyBinds: getKeyBinds($(this))
        });
    });

    $('.time-picker').each(function () {
        $(this).attr('autocomplete', 'off');
        $(this).datetimepicker({
            format: 'HH:mm',
            // debug: true,
            focusOnShow: false,
            keyBinds: getKeyBinds($(this))
        });
    });
}