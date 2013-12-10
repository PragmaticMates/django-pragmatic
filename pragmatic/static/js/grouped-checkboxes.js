$(document).ready(function() {
    // GroupedCheckboxSelectMultiple
    $('.group').each(function() {
        if ($('.panel-heading input[type=checkbox]', this).is(':checked')) {
            $('.list-group', this).show();
        } else {
            $('.list-group', this).hide();
        }

        $('.panel-heading input[type=checkbox]', this).change(function() {
            if ($(this).is(':checked')) {
                $(this).closest('.group').find('.list-group').show();
            } else {
                $(this).closest('.group').find('.list-group').hide();
            }
        });
    });
});