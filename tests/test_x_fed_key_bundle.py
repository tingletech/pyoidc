import os
from future.backports.urllib.parse import quote_plus

from oic.federation.operator import Operator
from oic.federation.bundle import JWKSBundle
from oic.federation.bundle import verify_signed_bundle
from oic.utils.keyio import build_keyjar
from oic.utils.keyio import KeyJar

BASE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "data/keys"))

KEYDEFS = [
    {"type": "RSA", "key": '', "use": ["sig"]},
    {"type": "EC", "crv": "P-256", "use": ["sig"]}
]

KEYS = {}
ISSUER = {}
OPERATOR = {}

for entity in ['fo0', 'fo1', 'fo2', 'fo3', 'sig']:
    fname = quote_plus(os.path.join(BASE_PATH, "{}.key".format(entity)))
    _keydef = KEYDEFS[:]
    _keydef[0]['key'] = fname

    _jwks, _keyjar, _kidd = build_keyjar(_keydef)
    KEYS[entity] = {'jwks': _jwks, 'keyjar': _keyjar, 'kidd': _kidd}
    ISSUER[entity] = 'https://{}.example.org'.format(entity)
    OPERATOR[entity] = Operator(keyjar=_keyjar, iss=ISSUER[entity])

SignKeyJar = OPERATOR['sig'].keyjar
del OPERATOR['sig']

def test_create():
    jb = JWKSBundle('iss')
    for iss, op in OPERATOR.items():
        jb[op.iss] = op.keyjar

    assert len(jb.keys()) == 4


def test_dumps():
    jb = JWKSBundle('iss')
    for iss, op in OPERATOR.items():
        jb[op.iss] = op.keyjar

    bs = jb.dumps()
    assert len(bs) > 2000


def test_dump_load():
    jb = JWKSBundle('iss')
    for iss, op in OPERATOR.items():
        jb[op.iss] = op.keyjar

    bs = jb.dumps()

    receiver = JWKSBundle('')
    receiver.loads(bs)

    assert len(receiver.keys()) == 4
    assert set(receiver.keys()) == set([op.iss for op in OPERATOR.values()])


def test_create_verify():
    jb = JWKSBundle('iss', SignKeyJar)
    for iss, op in OPERATOR.items():
        jb[op.iss] = op.keyjar

    _jws = jb.create_signed_bundle()
    _jwks = SignKeyJar.export_jwks()
    kj = KeyJar()
    kj.import_jwks(_jwks, 'iss')
    bundle = verify_signed_bundle(_jws, kj)

    assert bundle