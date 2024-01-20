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
    
    def get_feet_between_address_and_latlong(self, address: str, latitude: str, longitude: str) -> float:
        directions = self._client.directions(origin=address, destination=latitude + ',' + longitude, mode='walking')

        if len(directions) == 0:
            return "Could not find walkable path."
        
        distance = directions[0]['legs'][0]['distance']['text']
        distancePieces = distance.split(' ')
        distanceValue = round(float(distancePieces[0]))
        distanceUnits = distancePieces[1]
        if  distanceUnits == 'mi':
            distanceValue = '{0:,.0f}'.format(distanceValue * 5280)
            distanceUnits = 'ft'
        
        return distanceValue
    
    def _get_map_safe_str(str: str) -> str:
        return str.replace('+', '%2B').replace(' ', "+")
    
    def get_address_url(address: str) -> str:
        safeAddress = Map._get_map_safe_str(address)
        
        return 'https://www.google.com/maps/search/?api=1&query=' + safeAddress
    
    def get_directions_url(origin: str, destination: str) -> str:
        safeOrigin = Map._get_map_safe_str(origin)
        safeDestination = Map._get_map_safe_str(destination)
        
        return 'https://www.google.com/maps/dir/?api=1&origin=' + safeOrigin + '&destination=' + safeDestination