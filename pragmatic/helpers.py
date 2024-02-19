from googlemaps import Client


def method_overridden(object, method_name):
    return getattr(type(object), method_name) is not getattr(type(object).__bases__[0], method_name)


class GetBestRouteHelper:
    """
        Helper for getting the route without Switzerland for a given origin and destination.
        Parameters:
            api_key: str
                Api-Key for the Google Maps API
    """
    _INNSBRUCK = ["via:Innsbruck, Austria"]
    _LION = ["via:Lion, France"]
    _BEAUNE = ["via:Beaune, France"]

    def __init__(
        self,
        api_key: str
    ):
        self._alternatives: bool = True
        self._waypoints: list[str] | None = None
        self._avoidable_country: str = "Switzerland"
        self._routes: list[dict] | dict | None = None
        self._client: Client = Client(key=api_key)

    def find_best_route(
        self,
        origin: str | dict,
        destination: str | dict,
        waypoints: list[str] | None = None,
    ) -> dict:
        """
            Implemented algorithm trying to find the route avoiding Switzerland.
            If it doesn't exist with one request with alternatives from Google Maps,
            adding alternative waypoints and trying to recalculate the route.
            Parameters:
                origin: str | dict
                destination: str | dict
                waypoints: list[str] | None
            Returns:
                dict
                    Keys, values:
                        distance: str, duration: str, polyline: str
        """
        self._get_routes(origin, destination, waypoints)
        self._routes = self._check_if_country_exists()

        if self._routes:
            best_route = min(
                self._routes, key=lambda route: route["legs"][0]["duration"]["value"]
            )
            # route_info = best_route["legs"][0] # summary about route

            result = {
                "via": self._waypoints,
                "polyline": best_route["overview_polyline"]["points"],
            }

            return result
        else:
            return self.find_best_route(
                origin=origin,
                destination=destination,
                waypoints=(
                    GetBestRouteHelper._BEAUNE
                    if "France" in destination or "France" in origin
                    else GetBestRouteHelper._INNSBRUCK
                ),
            )

    def _get_routes(
        self, origin: str | dict, destination: str | dict, waypoints: list[str] | None
    ) -> None:
        """Getting routes from Google Routes API"""
        self._routes = self._client.directions(
            origin=origin,
            destination=destination,
            waypoints=waypoints,
            alternatives=self._alternatives,
            mode="driving",
        )

    def _check_if_country_exists(self) -> list[dict]:
        """Check all the routes"""
        routes_without_country = []
        for route in self._routes:
            country_exists = self._check_one_route(route)
            if country_exists:
                continue
            routes_without_country.append(route)

        return routes_without_country

    def _check_one_route(self, route: dict):
        """Check if Switzerland in route"""
        steps = route["legs"][0]["steps"]

        for location in steps:
            if self._avoidable_country in location["html_instructions"]:
                return True
        return False
