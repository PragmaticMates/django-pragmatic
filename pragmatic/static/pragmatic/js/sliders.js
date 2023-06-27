jQuery(document).ready(function ($) {
    'use strict';
    init_sliders();
});

function init_sliders() {
    $('[data-slider]').each(function () {
        init_slider($(this));
    });
}

function init_slider(slider_element) {
    var min = slider_element.attr('data-slider-min');
    var max = slider_element.attr('data-slider-max');
    var useInput = slider_element.attr('data-slider-input');
    useInput = typeof useInput === typeof undefined || useInput === 'true';

    var slider = slider_element.slider({
        formatter: function (val) {
            if (Array.isArray(val)) {
                return ((val[0] <= min) ? min : val[0]) + " : " + val[1];
            } else {
                return (val <= min) ? min : val;
            }
        }
    });

    function initLabels(value) {
        if (useInput === true) {
            var inputAfterWrapper = $('<div class="input-group input-group-sm"><input type="text" class="form-control slider-after"></div>');
            inputAfterWrapper.insertAfter(sliderElement);
            var inputAfter = inputAfterWrapper.find('input');

            if (valueAfter) {
                var afterValueWrapper = $('<div class="input-group-append"><span class="input-group-text">' + valueAfter + '</span></div>');
                inputAfterWrapper.append(afterValueWrapper)
            }

            if (value.length > 1) {
                var inputBeforeWrapper = $('<div class="input-group input-group-sm"><input type="text" class="form-control slider-before"></div>');
                inputBeforeWrapper.insertBefore(sliderElement);
                var inputBefore = inputBeforeWrapper.find('input');

                if (valueAfter) {
                    inputBeforeWrapper.append(afterValueWrapper.clone())
                }

                inputBefore.keyup(function () {
                    setValueByInput(inputBefore, inputAfter);
                });

                inputAfter.keyup(function () {
                    setValueByInput(inputBefore, inputAfter);
                });

                inputBefore.change(function () {
                    updateValidInputValueOnChange(inputBefore, inputAfter);
                });

                inputAfter.change(function () {
                    updateValidInputValueOnChange(inputBefore, inputAfter);
                });
            } else {
                inputAfter.keyup(function () {
                    setValueByInput(null, inputAfter);
                });

                inputAfter.change(function () {
                    updateValidInputValueOnChange(null, inputAfter)
                });
            }
        } else {
            $('<div class="label slider-after"></div>').insertAfter(sliderElement);

            if (value.length > 1) {
                $('<div class="label slider-before"></div>').insertBefore(sliderElement);
            }
        }
    }

    function getValidValue(value) {
        if (isNaN(value) || Number(value) < Number(min)) {
            return min;
        }

        if (Number(value) > Number(max)) {
            return max;
        }

        return value;
    }

    function updateLabels() {
        var values = slider.slider('getValue');

        if (values.length > 1) {
            if (values[0] <= min) {
                values[0] = min
            }

            if (useInput === true){
                parent.find('.slider-before').val(values[0]);
                parent.find('.slider-after').val(values[1]);
            } else {
                parent.find('.slider-before').html(values[0] + ' ' + valueAfter);
                parent.find('.slider-after').html(values[1] + ' ' + valueAfter);
            }
        } else {
            if (values <= min) {
                values = min
            }

            if (useInput === true) {
                parent.find('.slider-after').val(values);
            } else {
                parent.find('.slider-after').html(values + ' ' + valueAfter);
            }
        }
    }

    function updateValidInputValueOnChange(inputBefore, inputAfter) {
        var afterValue = getValidValue(inputAfter.val());
        if (inputBefore) {
            var beforeValue = getValidValue(inputBefore.val());
            if (Number(beforeValue) > Number(afterValue)) {
                inputAfter.val(beforeValue);
                inputBefore.val(afterValue);
            } else {
                inputAfter.val(afterValue);
                inputBefore.val(beforeValue);
            }
        } else {
            inputAfter.val(afterValue);
        }
    }

    function setValueByInput(inputBefore, inputAfter) {
        var afterValue = getValidValue(inputAfter.val());
        if (inputBefore) {
            var beforeValue = getValidValue(inputBefore.val());
            try {
                var val = JSON.parse("[" + beforeValue + ',' + afterValue + "]");
                slider.slider('setValue', val, false, true);
            } catch (e) {
                // silently ignore
            }

        } else {
            slider.slider('setValue', getValidValue(inputAfter.val()), false, true);
        }
    }

    if (slider_element && slider_element.attr('data-slider-show-value')) {
        var parent = slider_element.parent();
        var valueAfter = slider_element.attr('data-slider-value-after');
        var sliderElement = slider_element.slider('getElement');
        var value = slider_element.slider('getValue');

        parent.addClass('slider-wrapper');

        if (valueAfter == null) {
            valueAfter = '';
        }

        initLabels(value);
        updateLabels();

        slider_element.on('change', function () {
            updateLabels();
        });
    }
}