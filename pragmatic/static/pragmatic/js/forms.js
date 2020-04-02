jQuery(document).ready(function ($) {
    'use strict';
    init_filters();

});

function init_filters() {
    /**
     * Don't submit empty form values
     */
    // Change 'form' to class or ID of your specific form
    $(document.body).on('submit', 'form:not([method="post"])', function () {
        $(this).find('input,select:not(:has(option:selected[value!=""]))').filter(function () {
            return !this.value;
        }).attr('name', '');

        $(this).find('input[data-slider]').filter(function () {
            var val = $(this).val().split(',');

            if (val.length === 2) {
                var valMin = parseFloat(val[0]);
                var valMax = parseFloat(val[1]);

                var max = $(this).data('slider-max');
                if (max) {
                    max = parseFloat(max);
                }

                var min = $(this).data('slider-min');
                if (min) {
                    min = parseFloat(min);
                }

                if (valMin === min && valMax === max) {
                    $(this).val('');
                    $(this).attr('name', '');
                }
            }
        });
        return true;
    });

    $(document).keyup(function (e) {
        if (e.key === 'Escape') { // escape key maps to keycode `27`
            $('#filter-modal').modal('hide');
        }
    });

    $('.filter-has-errors [data-toggle="modal"]').click();
}