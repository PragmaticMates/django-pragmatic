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

    const commonSettings = {
        debug: false,
        focusOnShow: false,
        keyBinds: getKeyBinds($(this)),
        icons: {
            time: 'fa fa-clock-o',
            date: 'fa fa-calendar',
            up: 'fa fa-chevron-up',
            down: 'fa fa-chevron-down',
            previous: 'fa fa-chevron-left',
            next: 'fa fa-chevron-right',
            today: 'fa fa-dot-circle-o',
            clear: 'fa fa-trash',
            close: 'fa fa-times'
        }
    }

    $('.datetime-picker, [name$="datetime"], .datetimeinput').each(function () {
        $(this).attr('autocomplete', 'off');
        $(this).datetimepicker({
            format: 'DD.MM.YYYY HH:mm',
            ...commonSettings
        });
    });

    $('.date-picker, .dateinput').each(function () {
        $(this).attr('autocomplete', 'off');
        $(this).datetimepicker({
            format: 'DD.MM.YYYY',
            ...commonSettings
        });
    });

    $('.time-picker').each(function () {
        $(this).attr('autocomplete', 'off');
        $(this).datetimepicker({
            format: 'HH:mm',
            ...commonSettings
        });
    });
}