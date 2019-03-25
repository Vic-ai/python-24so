import suds
import base64
import six
from io import BytesIO


def binary_type(data):
    args = [data]
    if six.PY3:
        args.append('ascii')

    return six.binary_type(*args)


class Attachment:
    def __init__(self, client=None):
        self._client = client
        self._service = 'Attachment'

    def upload_file(self, path, location='Journal', stamp_no=None):
        api = self._client._get_client(self._service)

        if path.lower().endswith('.jpeg') or path.lower().endswith('.jpg'):
            filetype = 'Jpeg'
        elif path.lower().endswith('.png'):
            filetype = 'Png'
        elif path.lower().endswith('.tif') or path.lower().endswith('.tiff'):
            filetype = 'Tiff'
        else:
            raise AttributeError('Filetype not supported')

        types = api.factory.create('ImageType')
        if not hasattr(types, filetype):
            raise AttributeError('Filetype not supported')
        loc = api.factory.create('AttachmentLocation')
        if not hasattr(loc, location):
            raise AttributeError('Location not supported')

        # load file from disk
        with open(path, 'rb') as f:
            content = f.read()

        file_obj = api.service.Create(filetype)
        file_obj.FrameInfo = api.factory.create('ArrayOfImageFrameInfo')

        # create one frame per image
        frame = api.factory.create('ImageFrameInfo')
        frame.Id = 1  # PAGE_NO = always 1
        frame.Status = 0
        if stamp_no:
            frame.StampNo = stamp_no
        else:
            frame.StampNo = api.service.GetStampNo()

        # add the frame/image to the file object via the array of image frame info
        file_obj.FrameInfo.ImageFrameInfo.append(frame)

        # max chunk size
        # max_length = api.service.GetMaxRequestLength()
        max_length = 2000 * 1024

        # upload the files
        offset = 0
        while offset <= len(content):
            # extract next part of the content
            part = content[offset:offset + max_length]
            # part = part.encode('base64')
            part = base64.b64encode(part)
            if isinstance(part, bytes):
                part = part.decode()
            # print('uploading offset = {}, bytes = {}'.format(offset, len(part)))

            api.service.AppendChunk(file_obj, part, offset)

            offset += max_length

        # print('All chunks uploaded OK')
        api.service.Save(file_obj, location)

        return dict(
            Id=file_obj.Id,
            Type=file_obj.Type,
            StampNo=frame.StampNo,
            Location=location,
        )
        # return self._client._get_collection(method, None)

    def upload_files(self, images, location='Journal', stamp_no=None):
        api = self._client._get_client(self._service)

        loc = api.factory.create('AttachmentLocation')
        if not hasattr(loc, location):
            raise AttributeError('Location not supported')

        if not stamp_no:
            stamp_no = api.service.GetStampNo()

        files = []

        for frame_no, path in enumerate(images):
            if path.lower().endswith('.jpeg') or path.lower().endswith('.jpg'):
                filetype = 'Jpeg'
            elif path.lower().endswith('.png'):
                filetype = 'Png'
            elif path.lower().endswith('.tif') or path.lower().endswith('.tiff'):
                filetype = 'Tiff'
            else:
                raise AttributeError('Filetype not supported')

            types = api.factory.create('ImageType')
            if not hasattr(types, filetype):
                raise AttributeError('Filetype not supported')

            # load file from disk
            with open(path, 'rb') as f:
                content = f.read()

            file_obj = api.service.Create(filetype)
            file_obj.FrameInfo = api.factory.create('ArrayOfImageFrameInfo')

            # create one frame per image
            frame = api.factory.create('ImageFrameInfo')
            frame.Id = 1
            frame.Status = 0
            frame.StampNo = stamp_no

            # add the frame/image to the file object via the array of image frame info
            file_obj.FrameInfo.ImageFrameInfo.append(frame)

            # max chunk size
            # max_length = api.service.GetMaxRequestLength()
            max_length = 2000 * 1024

            # upload the files
            offset = 0
            while offset <= len(content):
                # extract next part of the content
                part = content[offset:offset + max_length]
                # part = part.encode('base64')
                part = base64.b64encode(part)
                # print('uploading offset = {}, bytes = {}'.format(offset, len(part)))

                api.service.AppendChunk(file_obj, part, offset)

                offset += max_length

            # print('All chunks uploaded OK')
            api.service.Save(file_obj, location)

            files.append(file_obj)

        return dict(
            # Id=file_obj.Id,
            # Type=file_obj.Type,
            StampNo=stamp_no,
            Location=location,
        )
        # return self._client._get_collection(method, None)

    def download_stamp_no(self, stamp_no):
        api = self._client._get_client(self._service)

        # maxlength = api.service.GetMaxRequestLength()
        max_length = 2000 * 1024

        fsp = api.factory.create('FileSearchParameters')
        fsp.StampNo.int.append(stamp_no)

        fileinfo = api.service.GetFileInfo(fsp)

        results = []

        if isinstance(fileinfo, suds.sax.text.Text):
            return results

        for imagefile in fileinfo.ImageFile:
            filesize = api.service.GetSize(imagefile)

            content = binary_type('')
            for offset in range(0, filesize, max_length):
                data = api.service.DownloadChunk(imagefile, offset, max_length)
                content += base64.b64decode(binary_type(data))
            data = api.service.DownloadChunk(imagefile, offset, filesize - offset)
            content += base64.b64decode(binary_type(data))

            buf = BytesIO(content)

            fileframe = None
            for frame in imagefile.FrameInfo.ImageFrameInfo:
                fileframe = frame.Id

                results.append(dict(
                    FileId=imagefile.Id,
                    FileFrame=fileframe,
                    Type=imagefile.Type,
                    StampNo=imagefile.StampNo,
                    Size=filesize,
                    buffer=buf
                ))
        return results
