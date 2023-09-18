import flask
import binascii
import store

def create_app():
    app = flask.Flask(__name__)
    s = store.Store()

    def json_proof(p):
        res = {
            'siblings': [binascii.hexlify(s).decode('ascii') for s in p.siblings],
        }
        if p.key is not None:
            res['key'] = binascii.hexlify(p.key).decode('ascii')
            res['val'] = binascii.hexlify(p.val).decode('ascii')
        return flask.jsonify(res)

    @app.route("/<hexkey>", methods=["GET"])
    def lookup(hexkey):
        key = binascii.unhexlify(hexkey)
        return json_proof(s.lookup(key))

    @app.route("/<hexkey>", methods=["PUT"])
    def insert(hexkey):
        key = binascii.unhexlify(hexkey)
        val = flask.request.data
        return json_proof(s.insert(key, val))

    @app.route("/reset", methods=["POST"])
    def reset():
        s.reset()
        return ('', 204)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=6160)
