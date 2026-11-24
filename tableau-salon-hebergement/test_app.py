import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
import services as s
from server import app

class AppTests(unittest.TestCase):
    def setUp(self):
        s.CACHE.clear()
        self.client = app.test_client()

    def test_routes_and_secret_paths(self):
        for path in ['/', '/app.js', '/style.css', '/healthz']:
            r = self.client.get(path, base_url='https://salon.example.com')
            self.assertEqual(r.status_code, 200)
            r.close()
        for path in ['/prim-key.txt', '/config.json', '/services.py', '/.env', '/static/../prim-key.txt']:
            self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.get('/healthz').headers['Cache-Control'], 'no-store')

    def test_cache_refresh_at_15_seconds(self):
        self.assertEqual(s.interval(), 15)
        with patch.object(s.time, 'time', return_value=100):
            self.assertEqual(s.cached('x', 15, lambda: 1)['data'], 1)
        with patch.object(s.time, 'time', return_value=114.9):
            self.assertEqual(s.cached('x', 15, lambda: 2)['data'], 1)
        with patch.object(s.time, 'time', return_value=115):
            self.assertEqual(s.cached('x', 15, lambda: 2)['data'], 2)

    def test_error_preserves_data_and_backs_off(self):
        with patch.object(s.time, 'time', return_value=100): s.cached('x',15,lambda:[1])
        def fail(): raise HTTPError('test',429,'quota',{'Retry-After':'120'},None)
        with patch.object(s.time, 'time', return_value=116):
            r=s.cached('x',15,fail)
        self.assertEqual(r['data'],[1])
        self.assertEqual(r['retry_at'],236)
        self.assertIsNotNone(r['error'])

    def test_both_lines_share_one_request_and_keep_directions(self):
        visits=[]
        for line in ['C01073','C01100','OTHER']:
            for dest in ['aller','retour']:
                visits.append({'MonitoredVehicleJourney':{'LineRef':{'value':f'STIF:Line::{line}:'},'DestinationName':[{'value':dest}], 'MonitoredCall':{'ExpectedDepartureTime':'2030-01-01T12:00:00Z'}}})
        payload={'Siri':{'ServiceDelivery':{'StopMonitoringDelivery':[{'MonitoredStopVisit':visits}]}}}
        with patch.dict(os.environ,{'PRIM_API_KEY':'test-secret'}),patch.object(s,'fetch',return_value=payload) as f,patch.object(s.time,'sleep'):
            r=self.client.get('/api/transport')
            data=r.get_json()
            self.assertEqual(f.call_count,1)
            self.assertEqual([len(x['departures']) for x in data['stops']],[2,2])
            self.assertNotIn('test-secret',r.get_data(as_text=True))
            self.assertEqual(data['interval'],15)

    def test_key_file_and_environment_priority(self):
        payload={'Siri':{'ServiceDelivery':{'StopMonitoringDelivery':[]}}}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'prim-key.txt').write_text('file-key',encoding='utf-8-sig')
            with patch.object(s,'ROOT',root),patch.dict(os.environ,{'PRIM_API_KEY':''}),patch.object(s,'fetch',return_value=payload) as f,patch.object(s.time,'sleep'):
                s.transport();self.assertEqual(f.call_args.args[1]['apikey'],'file-key')
            s.CACHE.clear()
            with patch.object(s,'ROOT',root),patch.dict(os.environ,{'PRIM_API_KEY':'env-key'}),patch.object(s,'fetch',return_value=payload) as f,patch.object(s.time,'sleep'):
                s.transport();self.assertEqual(f.call_args.args[1]['apikey'],'env-key')

if __name__ == '__main__': unittest.main()
