(function ($) {
    map_widget_autofill = function (widget) {
        var locationInput = widget.locationInput;
        var form = $(locationInput).closest('form');
        var prefix = '';
        var waypoint = $(locationInput).closest('.waypoint');

        if (waypoint.length > 0) {
            var relVal = waypoint.attr('rel');
            prefix = (relVal.endsWith('_')) ? 'waypoint_' + relVal : 'waypoint_' + relVal+ '-';
        }

        var street = form.find('[name="' + prefix + 'street"]');
        var postcode = form.find('[name="' + prefix + 'postcode"]');
        var city = form.find('[name="' + prefix + 'city"]');
        var country = form.find('[name="' + prefix + 'country"]');
        var company = form.find('[name="' + prefix + 'company"]');
        var address = form.find('[name="' + prefix + 'address"]');
        var name = form.find('[name="' + prefix + 'name"]');

        // update every time the text inputs change
        $([street, postcode, city, country]).each(function () {
            $(this).change(function () {
                autofillAndUpdateMap();
            });
        });

        // update every time the select changes
        $(country).change(function () {
            autofillAndUpdateMap();
            onCountryChanged();
        });

        // update company
        $(company).change(function () {
            var companyId = company.val();
            if (companyId) {
                $.ajax({
                    type: 'GET',
                    url: '/api/companies/' + companyId + '/',
                    dataType: "json",
                    success: function (data) {
                        name.val(data.name);
                        street.val(data.address.street);
                        postcode.val(data.address.postcode);
                        city.val(data.address.city);
                        country.val(data.address.country);
                        country.trigger('change.select2');
                        if (data.address.point) {
                            widget.updateLocation(data.address.point.latitude, data.address.point.longitude);
                            widget.fitBoundMarker();
                        } else {
                            callUpdateMap();
                        }
                        onPostCodeChanged();
                    },
                    error: function (data) {
                        console.log('Get company failed!');
                    }
                });
            }
        });

        // update address
        $(address).change(function () {
            var addressId = address.val();
            if (addressId) {
                $.ajax({
                    type: 'GET',
                    url: '/api/v1/directory/addresses/' + addressId + '/',  // TODO: replace with variable
                    dataType: "json",
                    success: function (data) {
                        name.val(data.name);
                        street.val(data.street);
                        postcode.val(data.postcode);
                        city.val(data.city);
                        country.val(data.country);
                        country.trigger('change.select2')

                        if (data.point) {
                            // TODO: fix map refresh
                            widget.updateLocation(data.point.latitude, data.point.longitude);
                            widget.fitBoundMarker();
                        } else {
                            callUpdateMap();
                        }

                        onPostCodeChanged();
                    },
                    error: function (data) {
                        console.log('Get address failed!');
                    }
                });
            }
        });

        function autofillAndUpdateMap() {
            if (city.val()) {
                var url = '/api/address-autocomplete/?city=' + city.val();
                if (country.val()) {
                    url += '&country=' + country.val();
                }
                if (street.val()) {
                    url += '&street=' + street.val();
                }

                $.ajax({
                    type: 'GET',
                    url: url,
                    dataType: "json",
                    success: function (data) {
                        if (!postcode.val()) {
                            postcode.val(data.postcode);
                            onPostCodeChanged();
                        }
                        city.val(data.city);
                        if (!country.val()) {
                            country.val(data.country);
                            country.trigger('change.select2');
                        }
                        if (data.street && street.val().toUpperCase() === data.street.toUpperCase()) {
                            street.val(data.street);
                            postcode.val(data.postcode);
                            onPostCodeChanged();
                        }
                        callUpdateMap();
                    },
                    error: function (data) {
                        console.log(data);
                        console.log('Get address-autocomplete failed!');
                        callUpdateMap();
                    }
                });
            } else {
                callUpdateMap();
            }
        }

        function callUpdateMap() {
            if (postcode.val() && city.val() && country.val()) {
                updateMap();
            }
        }

        function onPostCodeChanged() {
            $(window).trigger($.Event('postcodechange'));
        }

        function onCountryChanged() {
            $(window).trigger($.Event('countrychange'));
        }

        // update map point by external event
        $(window).on('updatemappoint', function (e) {
            widget.updateLocation(e.point.latitude, e.point.longitude);
            widget.fitBoundMarker();
        });

        function updateMap() {
            // join all address parts values into single string
            var address = street.val() + ', ' + postcode.val() + ' ' + city.val() + ', ' + country.val();

            // initialize autocomplete service API
            var autocomplete_service = new google.maps.places.AutocompleteService();

            // try to find address prediction using autocomplete service API
            autocomplete_service.getPlacePredictions({input: address}, function (predictions, status) {
                // if status is incorrect, clear search value
                if (status != google.maps.places.PlacesServiceStatus.OK) {
                    $(widget.addressAutoCompleteInput).val('');
                    widget.removeMarker();
                    widget.map.setCenter({lat: widget.mapCenterLocation[0], lng: widget.mapCenterLocation[1]});
                    widget.map.setZoom(widget.zoom);
                    console.log("Address was not found: " + address);
                } else if (predictions.length >= 1) {
                    // otherwise if there is at least 1 prediction available, pick the very first one
                    var address_by_prediction = predictions[0].description;

                    // set the address as search value
                    $(widget.addressAutoCompleteInput).val(address_by_prediction);

                    // try to find the GPS coordinates of the predicted address
                    widget.geocoder.geocode({'address': address_by_prediction}, function (results, status) {
                        if (status === google.maps.GeocoderStatus.OK) {
                            // check the successful result
                            var geo_location = results[0].geometry.location;
                            var latitude = geo_location.lat();
                            var longitude = geo_location.lng();

                            // add marker to map
                            widget.addMarkerToMap(latitude, longitude);
                            widget.updateLocationInput(latitude, longitude);

                            // set center position (or fit bounds)
                            widget.map.setCenter({lat: latitude, lng: longitude});
                            // widget.fitBoundMarker();

                            // set zoom (change according your needs or use bounds if you wish)
                            widget.map.setZoom(15);

                        } else {
                            // geocoder couldn't find a GPS...
                            widget.removeMarker();
                            console.warn('Cannot find ' + address_by_prediction + ' on google geo service.');
                        }
                    });
                }
            });
        }
    };
})(jQuery || django.jQuery);
