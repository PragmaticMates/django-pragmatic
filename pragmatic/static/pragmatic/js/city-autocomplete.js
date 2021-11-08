(function ($) {
    jQuery(document).ready(function ($) {
        'use strict';

        var widgets = $('.autocompletecitywidget');

        if (widgets.length > 0) {
            var widget = widgets[0];
            var key = $(widget).data('google-key');
            var url = "https://maps.googleapis.com/maps/api/js?libraries=places,geometry&language=en&key=" + key;

            var script = $('script[src="' + url + '"]');
            var google_api_already_loaded = script.length > 0;

            if (google_api_already_loaded) {
                init_city_autocomplete(widgets);
                $(window).trigger($.Event('googleapiLoaded'));
            } else {
                $.getScript(url, function () {
                    init_city_autocomplete(widgets);
                    $(window).trigger($.Event('googleapiLoaded'));
                });
            }
        }
    });

    init_city_autocomplete = function (widgets) {
        var options = {
            types: ['(cities)'],
            // types: ['(regions)'],
            // fields: ['name', 'vicinity']
            fields: ['address_components', 'name']
        };

        widgets.each(function () {
            var parent = $(this).closest('.waypoint');
            var input = $(this)[0];
            var rel = $(this).attr('rel');
            var rel_input = parent.find('[name$=' + rel + ']');
            var $input = $(this);
            var autocomplete = new google.maps.places.Autocomplete(input, options);

            // disable click on country
            if (rel_input.length) {
                rel_input.addClass('opacity-50p');
                rel_input.on('mousedown', function (e) {
                    e.preventDefault();
                    this.blur();
                    window.focus();
                });
            }

            // return city and update country
            function updateCityAndCountry() {
                console.log('city_input ' + $input.val());
                $.ajax({
                    type: 'GET',
                    url: '/api/city-autocomplete/',
                    dataType: 'json',
                    data: {city_input: $input.val()},
                    success: function (data) {
                        $(input).val(data.result.name);
                        var address_components = data.result.address_components;

                        // update country
                        if (rel_input.length) {
                            for (var i = 0; i < address_components.length; i += 1) {
                                var addressObj = address_components[i];
                                for (var j = 0; j < addressObj.types.length; j += 1) {
                                    if (addressObj.types[j] === 'country') {
                                        var country = addressObj.short_name;
                                        rel_input.val(country);
                                        rel_input.trigger('change');
                                    }
                                }
                            }
                        }
                    },
                    error: function (data) {
                        console.log('Get city autocomplete failed!');
                    }
                });
            }

            google.maps.event.addListener(autocomplete, 'place_changed', function () {
                updateCityAndCountry();
            });

            // $input.on('change', function (e) {
            //     updateCityAndCountry();
            // });

            $(this).keypress(function (event) {
                if (13 === event.keyCode) {
                    // prevent form from submitting
                    event.preventDefault();
                }
            });
        });
    }

})(jQuery || django.jQuery);
