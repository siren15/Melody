import requests

class CatBox():
    def url_upload(url=None):
        """
            Upload a file to catbox.moe and returns the url

            Args:
                url: the url of the file to upload
            """
        with requests.Session() as session:
            if url is None:
                return None
            response = session.post('https://catbox.moe/user/api.php', data={'reqtype':'urlupload', 'url':url})
            return response.text
        
    def file_upload(name:str=None, file=None, mimetype:str=None):
        """
        Upload a file to catbox.moe and returns the url

        Args:
            name: the name of the file to upload
            file: the file to upload
            mimetype: the mimetype of the file
        """
        if file is None:
            return None
        with requests.Session() as session:
            resp = session.post('https://catbox.moe/user/api.php',
            data={'reqtype': 'fileupload', 'userhash': ''},
            files={'fileToUpload': (name, file, mimetype)
            })
        response = resp.text
        if response == 'No files given.':
            return None
        return response