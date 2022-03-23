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