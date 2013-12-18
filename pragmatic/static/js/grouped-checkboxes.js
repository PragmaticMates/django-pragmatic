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

                $(this).closest('.group').find('.list-group input[type=checkbox]').each(function() {
                    if ($(this).attr('on_open') == 'checked') {
                        $(this).prop('checked', true).change();
                    }
                });
            } else {
                $(this).closest('.group').find('.list-group').hide();

                $(this).closest('.group').find('.list-group input[type=checkbox]').each(function() {
//                    if ($(this).attr('on_open') == 'checked') {
                        $(this).prop('checked', false).change();
//                    }
                });
            }
        });

        $('input[type=checkbox]', this).change(function() {
            var is_checked = $(this).prop('checked');
            var with_same_value = $('input[type=checkbox][value='+$(this).val()+']');
            with_same_value.prop('checked', is_checked);
            if(is_checked) {
                with_same_value.closest('div').addClass('ez-checked');
            } else {
                with_same_value.closest('div').removeClass('ez-checked');
            }
        });
    });
});