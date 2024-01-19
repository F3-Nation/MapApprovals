import os
import googlemaps

class Map:
    _KEY = os.getenv('GOOGLE_MAP_KEY')
    _client = googlemaps.Client(key=_KEY)

    def get_address_from_latlong(self, latitude: str, longitude: str) -> str:
        """Takes lat and long and returns an address.
        Will return error strings if lat/long is invalid or does not produce an address.
        """

        try:
            addresses = self._client.reverse_geocode(latitude + ',' + longitude)
        except:
            return 'Invalid lat/long'

        address = addresses[0]
        if address['types'][0] == 'plus_code':
            return 'No address found'

        return address['formatted_address']
    
    def get_distance_between_address_and_latlong(self, address: str, latitude: str, longitude: str) -> str:
        directions = self._client.directions(origin=address, destination=latitude + ',' + longitude, mode='walking')

        if len(directions) == 0:
            return "Could not find walkable path."
        
        return directions[0]['legs'][0]['distance']['text']
    
    def get_directions_url(origin: str, destination: str) -> str:
        safeOrigin = origin.replace(' ', '+')
        safeDestination = destination.replace(' ', '+')
        
        return 'https://www.google.com/maps/dir/?api=1&origin=' + safeOrigin + '&destination=' + safeDestination