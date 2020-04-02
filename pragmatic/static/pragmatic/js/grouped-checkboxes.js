$(document).ready(function() {
    // GroupedCheckboxSelectMultiple
    $('.group').each(function() {
        // toggler click
        $('.panel-heading .toggler', this).click(function() {
            if($(this).hasClass('open')) {
                // hide only if no checkbox is checked
                if(!$(this).closest('.group').find('.list-group input[type=checkbox]').is(':checked')) {
                    $(this).closest('.group').find('.list-group').hide();
                    $(this).removeClass('open');
                }
            } else {
                // open
                $(this).closest('.group').find('.list-group').show();
                $(this).addClass('open');
            }
        });

        // heading checkbox init
        if ($('.panel-heading input[type=checkbox]', this).is(':checked')) {
            // open
            $('.list-group', this).show();
            $('.toggler', this).addClass('open');
            $('.toggler', this).hide();
        } else {
            // closed
            $('.list-group', this).hide();
            $('.toggler', this).removeClass('open');
        }

        // heading checkbox clicked
        $('.panel-heading input[type=checkbox]', this).change(function() {
            if ($(this).is(':checked')) {
                // checked
                $(this).closest('.group').find('.list-group').show();
                $(this).closest('.group').find('.toggler').addClass('open');

                $(this).closest('.group').find('.list-group input[type=checkbox]').each(function() {
                    if ($(this).attr('on_check') == 'checked') {
                        $(this).prop('checked', true);
                        $(this).closest('div').addClass('ez-checked');
                        $(this).closest('.group').find('.toggler').hide();
                    }
                });
            } else {
                // unchecked
                $(this).closest('.group').find('.list-group').hide();
                $(this).closest('.group').find('.toggler').removeClass('open');
                $(this).closest('.group').find('.toggler').show();

                $(this).closest('.group').find('.list-group input[type=checkbox]').each(function() {
                    $(this).prop('checked', false);
                    $(this).closest('div').removeClass('ez-checked');
                });
            }
        });

        // list checkbox clicked
        $('.list-group input[type=checkbox]', this).change(function() {
            var is_checked = $(this).prop('checked');

            // toggle other checkboxes with same value
            var with_same_value = $('input[type=checkbox][value='+$(this).val()+']');
            with_same_value.prop('checked', is_checked);
            if(is_checked) {
                with_same_value.closest('div').addClass('ez-checked');
            } else {
                with_same_value.closest('div').removeClass('ez-checked');
            }

            // show/hide toggler
            if($(this).closest('.group').find('.list-group input[type=checkbox]').is(':checked')) {
                $(this).closest('.group').find('.panel-heading .toggler').hide();
            } else {
                $(this).closest('.group').find('.panel-heading .toggler').show();
            }
        });
    });
});