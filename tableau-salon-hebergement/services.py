"""Services météo et transports, cache partagé par processus."""
import json, os, threading, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
CACHE = {}
LOCK = threading.Lock()

def value(x):
    if isinstance(x, list): return value(x[0]) if x else ''
    if isinstance(x, dict): return value(x.get('value', ''))
    return x or ''

def fetch(url, headers=None):
    with urlopen(Request(url, headers=headers or {}), timeout=20) as response:
        return json.load(response)

def cached(key, ttl, loader):
    # Verrou partagé : plusieurs onglets ne multiplient pas les appels externes.
    with LOCK:
        old = CACHE.get(key, {})
        if time.time() < old.get('retry_at', 0): return old
        retry_delay = ttl
        try:
            result = dict(data=loader(), updated=time.time(), error=None)
        except Exception as exc:
            if isinstance(exc, HTTPError):
                if exc.code == 429:
                    retry_delay = max(ttl, 60)
                    try: retry_delay = max(retry_delay, float(exc.headers.get('Retry-After', '60')))
                    except (ValueError, TypeError): pass
                message = {401:'Clé PRIM refusée.',403:'Accès refusé : vérifier la clé et les droits PRIM.',429:'Quota dépassé : attendre ou augmenter le quota.'}.get(exc.code, f'Service indisponible (HTTP {exc.code}).')
            else: message = 'Connexion ou réponse du service indisponible.'
            result = dict(data=old.get('data'), updated=old.get('updated'), error=message)
        result['retry_at'] = time.time() + retry_delay
        CACHE[key] = result
        return result

def weather():
    c = CONFIG['weather']
    query = urlencode(dict(latitude=c['latitude'], longitude=c['longitude'], current='temperature_2m,apparent_temperature,weather_code,wind_speed_10m', daily='temperature_2m_max,temperature_2m_min,precipitation_probability_max', forecast_days=3, timezone='Europe/Paris'))
    return cached('weather', 1800, lambda: fetch('https://api.open-meteo.com/v1/forecast?' + query))

def parse_departures(payload):
    delivery = payload.get('Siri', {}).get('ServiceDelivery')
    if not isinstance(delivery, dict): raise ValueError('Réponse SIRI manquante')
    result = []
    for block in delivery.get('StopMonitoringDelivery', []):
        if block.get('Status') is False or block.get('ErrorCondition'): raise ValueError('Erreur SIRI')
        for visit in block.get('MonitoredStopVisit', []):
            j = visit.get('MonitoredVehicleJourney', {})
            c = j.get('MonitoredCall', {})
            expected = c.get('ExpectedDepartureTime') or c.get('ExpectedArrivalTime')
            scheduled = c.get('AimedDepartureTime') or c.get('AimedArrivalTime')
            result.append(dict(line=value(j.get('LineRef')), destination=value(j.get('DestinationName')) or value(j.get('DirectionName')), destination_ref=value(j.get('DestinationRef')), time=expected or scheduled, realtime=bool(expected), cancelled=c.get('DepartureStatus') == 'cancelled' or c.get('ArrivalStatus') == 'cancelled'))
    return result

def interval():
    return max(15, int(CONFIG.get('transport_refresh_seconds', 15)))


def transport():
    stops = CONFIG['stops']
    key = os.environ.get('PRIM_API_KEY', '').strip()
    if not key and (ROOT / 'prim-key.txt').exists(): key = (ROOT / 'prim-key.txt').read_text(encoding='utf-8-sig').strip()
    if not stops: return dict(stops=[], message='Ajoute tes arrêts dans config.json.', interval=interval())
    if not key: return dict(stops=[], message='Clé PRIM non configurée sur le serveur.', interval=interval())
    results = []
    for stop in stops:
        ref = stop.get('monitoring_ref', '')
        if not ref: continue
        def loader():
            # Moins de cinq requêtes par seconde, même au premier chargement.
            time.sleep(0.25)
            payload = fetch('https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring?' + urlencode({'MonitoringRef':ref}), {'apikey':key, 'Accept':'application/json'})
            return parse_departures(payload)
        r = cached('stop:' + ref, interval(), loader)
        rows = [d for d in (r.get('data') or []) if (not stop.get('line_ref') or d['line'] == stop['line_ref']) and (not stop.get('destination_ref') or d['destination_ref'] == stop['destination_ref'])]
        results.append(dict(label=stop['label'], updated=r.get('updated'), error=r.get('error'), departures=rows))
    return dict(stops=results, interval=interval())

