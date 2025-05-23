import json
from datetime import datetime, timedelta
from flask.json.provider import JSONProvider

class CustomJSONEncoder(json.JSONEncoder):
    """Encoder personalizado para manejar objetos datetime y timedelta"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, timedelta):
            return str(obj)
        return super().default(obj)

class CustomJSONProvider(JSONProvider):
    """Provider JSON personalizado para Flask"""
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)
    
    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)