import os
import googlemaps
import geopy.distance

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
    
    def get_latlong_from_address(self, address) -> (str, str):
        """Takes an address string and returns a str tuple of latitude and longitude."""

        response = self._client.geocode(address)
        if response == []:
            return (None, None)

        coordinates = response[0]['geometry']['location']
        return (coordinates['lat'], coordinates['lng'])
    
    def get_feet_between_address_and_latlong(self, address: str, latitude: str, longitude: str) -> int|str:
        (address_lat, address_long) = self.get_latlong_from_address(address=address)
        if address_lat == None:
            return 'Address could not be converted to lat/long'

        try:
            feet = geopy.distance.distance((address_lat, address_long), (latitude, longitude)).feet
            feet = round(float(feet))
        except Exception as error:
            return 'Distance could not be calculated: ' + str(error)
        return feet
    
    def _get_map_safe_str(str: str) -> str:
        return str.replace('+', '%2B').replace(' ', "+")
    
    def get_address_url(address: str) -> str:
        safeAddress = Map._get_map_safe_str(address)
        
        return 'https://www.google.com/maps/search/?api=1&query=' + safeAddress
    
    def get_directions_url(origin: str, destination: str) -> str:
        safeOrigin = Map._get_map_safe_str(origin)
        safeDestination = Map._get_map_safe_str(destination)
        
        return 'https://www.google.com/maps/dir/?api=1&origin=' + safeOrigin + '&destination=' + safeDestination