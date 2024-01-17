import pycurl
import json
import zlib
import logging

class Client:
    def __init__(self):
        self.headers = [
            "accept: application/json",
            "accept-encoding: gzip",
            "accept-language: en-US",
            "connection: Keep-Alive",
            "content-type: application/json; charset=UTF-8",
            "host: grindr.mobi",
            "l-device-info: 2938f76cff50af57;GLOBAL;2;2069590016;2277x1080;a9ffffa4-2b0e-479d-b3db-ae117c0a9686",
            "l-locale: en_US",
            "l-time-zone: Europe/London",
            "requirerealdeviceinfo: true",
            "user-agent: grindr3/9.17.3.118538;118538;Free;Android 14;sdk_gphone64_x86_64;Google",
        ]
        self.basePath = "https://grindr.mobi"


    def get(self, path, data, auth_token = None):
        response_data = []
        request_data = data

        c = pycurl.Curl()

        c.setopt(
            c.URL,
            self.basePath
            + path
            + "?"
            + "&".join([key + "=" + request_data[key] for key in request_data]),
        )
        c.setopt(c.CUSTOMREQUEST, "GET")

        if auth_token is not None:
            self.headers.append("authorization: Grindr3 " + auth_token)

        c.setopt(c.HTTPHEADER, self.headers)

        def handle_response(data):
            response_data.append(data)

        c.setopt(c.WRITEFUNCTION, handle_response)
        c.perform()
        c.close()

        response_data = b"".join(response_data)

        decompressed_response = zlib.decompress(response_data, zlib.MAX_WBITS | 16)
        return json.loads(decompressed_response)


    def uploadImage(self, path, img, auth_token = None):
        self.headers.remove("content-type: application/json; charset=UTF-8")

        self.headers.append("content-type: image/jpeg")
        self.post(path, img, auth_token)
        self.headers.remove("content-type: image/jpeg")

        self.headers.append("content-type: application/json; charset=UTF-8")


    def post(self, path, data, auth_token = None):
        response_data = []
        request_data = data
        data_json = json.dumps(request_data)

        c = pycurl.Curl()
        c.setopt(c.URL, self.basePath + path)
        c.setopt(c.CUSTOMREQUEST, "POST")

        if auth_token is not None:
            self.headers.append("authorization: Grindr3 " + auth_token)

        c.setopt(c.HTTPHEADER, self.headers)
        c.setopt(c.POSTFIELDS, data_json)

        def handle_response(data):
            response_data.append(data)

        c.setopt(c.WRITEFUNCTION, handle_response)

        try:
            c.perform()
            response_code = c.getinfo(pycurl.RESPONSE_CODE)

            if response_code != 200 and response_code != 201:
                logging.error(f"HTTP Error: {response_code}")
                exit(-1)
            
            response_data = b"".join(response_data)
            decompressed_response = zlib.decompress(response_data, zlib.MAX_WBITS | 16)
            return json.loads(decompressed_response)

        except pycurl.error as e:
            logging.error(f"Pycurl error: {e}")
            exit(-1)

        finally:
            c.close()
