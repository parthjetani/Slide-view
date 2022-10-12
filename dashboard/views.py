from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from io import BytesIO
from threading import Lock
from os import path
from os import remove
from json import dumps
from django.http import HttpResponse, Http404, JsonResponse

from openslide import open_slide
from openslide import OpenSlide
from openslide.deepzoom import DeepZoomGenerator

from PIL import Image
from .models import Slide, Annotation, Folder
from .utils import get_folder_structure
import base64
import re
from .dicom_deepzoom import ImageCreator, get_PIL_image
import os
import pydicom


@login_required
def index(request):
    return render(request, "dashboard.html")


@login_required
def my_folders(request):

    if request.method == "POST":
        pageNum = int(request.POST["pageNum"])
        totalEntries = int(request.POST["totalEntries"])
        start = (int(request.POST["pageNum"]) - 1) * totalEntries
        end = start + totalEntries
        totalFolders = Folder.objects.all()
        folders = Folder.objects.all()[start:end:1]

        if int(len(totalFolders)) % totalEntries:
            totalPage = (int(len(totalFolders)) // totalEntries) + 1
        else:
            totalPage = int(len(totalFolders)) // totalEntries

    else:
        totalFolders = Folder.objects.all()
        folders = Folder.objects.all()[:10:1]
        totalEntries = 10
        folderStructure = get_folder_structure()

        if int(len(totalFolders)) % totalEntries:
            totalPage = (int(len(totalFolders)) // totalEntries) + 1
        else:
            totalPage = int(len(totalFolders)) // totalEntries
        start = 0

    data = {
        "javascripts": ["my_folder.js"],
        "totalEntries": totalEntries,
        "folders": folders,
        "totalPage": range(1, totalPage + 1),
        "start": start,
        "totalFolders": totalFolders,
        "folderStructure": folderStructure,
        "slides": Slide.objects.all(),
    }
    return render(request, "my_folders.html", data)


OUTPUT_PATH = os.path.join(settings.BASE_DIR, "static/dzi/")
MAX_THUMBNAIL_SIZE = 200, 200

regex = re.compile(
    r"^(?:http|ftp)s?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


class Openslides:
    _slides = {}
    _deepzooms = {}
    _dict_lock = Lock()

    def __init__(self):
        pass

    @classmethod
    def insertslide(cls, key, sl):
        opts = {
            "tile_size": settings.DEEPZOOM_TILE_SIZE,
            "overlap": settings.DEEPZOOM_OVERLAP,
        }
        with cls._dict_lock:
            cls._slides[key] = sl
            cls._deepzooms[key] = DeepZoomGenerator(sl, **opts)

    @classmethod
    def getslide(cls, key):
        with cls._dict_lock:
            return cls._slides[key]

    @classmethod
    def getdeepzoom(cls, key):
        with cls._dict_lock:
            return cls._deepzooms[key]


def slide(request, slide_id):

    try:
        s = Slide.objects.get(pk=slide_id)
    except Slide.DoesNotExist:
        raise Http404
    param = request.GET.get("url")
    back_url = None
    if s.SlideType == 1:
        if not os.path.exists(OUTPUT_PATH):
            os.mkdir(OUTPUT_PATH)

        if not os.path.exists(OUTPUT_PATH + "" + str(slide_id) + ".dzi"):
            SOURCE = os.path.join(settings.SLIDES_DIR, s.UrlPath)
            # Create Deep Zoom Image creator with weird parameters
            creator = ImageCreator(
                tile_size=128,
                tile_overlap=2,
                tile_format="jpg",
                image_quality=0.8,
                resize_filter="bicubic",
            )

            # Create Deep Zoom image pyramid from source
            creator.create_dicom(SOURCE, OUTPUT_PATH + "" + str(slide_id) + ".dzi")

    if param is not None:
        try:
            param_bytes = param.encode("ascii")
            enc = base64.urlsafe_b64decode(param_bytes)
            back_url = enc.decode("ascii")
        except:
            back_url = None

        if back_url is not None:
            if re.match(regex, back_url) is None:
                back_url = None

    return render(
        request,
        "slides/slide.html",
        {
            "Slide": s,
            "Label": request.build_absolute_uri(s.LabelUrlPath),
            "back_url": back_url,
            "annotations": s.Annotations,
        },
    )


def load_slide(slide_id, slidefile):
    sl = open_slide(slidefile)
    Openslides.insertslide(slide_id, sl)


def get_slide(slide_id):
    if slide_id not in Openslides._slides:
        s = Slide.objects.get(pk=slide_id)
        load_slide(s.pk, path.join(settings.SLIDES_DIR, s.UrlPath))
    return Openslides.getslide(slide_id)


def get_deepzoom(slide_id):
    if slide_id not in Openslides._slides:
        s = Slide.objects.get(pk=slide_id)
        load_slide(s.pk, path.join(settings.SLIDES_DIR, s.UrlPath))
    return Openslides.getdeepzoom(slide_id)


def dzi(request, slug):
    slideformat = settings.DEEPZOOM_FORMAT
    try:
        slug = int(slug)
        resp = HttpResponse(
            get_deepzoom(slug).get_dzi(slideformat), content_type="application/xml"
        )
        return resp
    except KeyError:
        # Unknown slug
        raise Http404


def properties(request, slug):
    # Get a JSON object with slide properties
    sl = get_slide(int(slug))
    response_data = {
        "width": sl.dimensions[0],
        "height": sl.dimensions[1],
        "mppx": float(sl.properties.get("openslide.mpp-x", "0.0")),
        "mppy": float(sl.properties.get("openslide.mpp-y", "0.0")),
        "vendor": sl.properties.get("openslide.vendor", ""),
    }
    return HttpResponse(dumps(response_data), content_type="application/json")


def dztile(request, slug, level, col, row, slideformat):
    slideformat = slideformat.lower()
    slug = int(slug)
    level = int(level)
    col = int(col)
    row = int(row)
    if slideformat != "jpeg" and slideformat != "png":
        # Not supported by Deep Zoom
        raise Http404
    try:
        tile = get_deepzoom(slug).get_tile(level, (col, row))
    except KeyError:
        # Unknown slug
        raise Http404
    except ValueError:
        # Invalid level or coordinates
        raise Http404
    buf = BytesIO()
    tile.save(buf, slideformat, quality=75)
    resp = HttpResponse(buf.getvalue(), content_type="image/%s" % slideformat)
    return resp


def gmtile(request, slug, level, col, row, slideformat):
    return dztile(request, slug, int(level) + 8, col, row, slideformat)


def gen_thumbnail_url(request, slide_id):
    try:
        s = Slide.objects.get(pk=slide_id)
    except Slide.DoesNotExist:
        raise Http404
    label_name = str(s.LabelUrlPath).split("/")[-1]
    if label_name != "placeholder.png":
        return JsonResponse(
            {
                "thumbnail": request.build_absolute_uri(str(s.LabelUrlPath)),
            }
        )
    else:
        if s.SlideType == 1:
            ds = pydicom.dcmread(os.path.join(settings.SLIDES_DIR, s.UrlPath))
            thumbnail = get_PIL_image(ds)
            response = HttpResponse(content_type="image/png")
            thumbnail.thumbnail(MAX_THUMBNAIL_SIZE)
            filename = str(s.UrlPath).split("/")[-1]
            fWithoutExt = filename.split(".")
            fWithoutExt.pop()
            fWithoutExt = "".join(fWithoutExt)
            thumbnailName = fWithoutExt + ".thumbnail"
            dirPath = settings.STATICFILES_DIRS[0] + "/images/thumbnail"
            thumbnail.save(dirPath + "/" + thumbnailName, "JPEG")
            return JsonResponse(
                {
                    "thumbnail": request.build_absolute_uri("/static/images/thumbnail/")
                    + thumbnailName,
                }
            )
        else:
            file = os.path.join(settings.SLIDES_DIR, s.UrlPath)
            slide = OpenSlide(file)
            thumbnail = slide.get_thumbnail((800, 600))
            filename = str(s.UrlPath).split("/")[-1]
            fWithoutExt = filename.split(".")
            fWithoutExt.pop()
            fWithoutExt = "".join(fWithoutExt)
            thumbnailName = fWithoutExt + ".thumbnail"
            dirPath = settings.STATICFILES_DIRS[0] + "/images/thumbnail"
            thumbnail.save(dirPath + "/" + thumbnailName, "JPEG")
            return JsonResponse(
                {
                    "thumbnail": request.build_absolute_uri("/static/images/thumbnail/")
                    + thumbnailName,
                }
            )


def gen_label(request, slide_id):
    try:
        s = Slide.objects.get(pk=slide_id)
    except Slide.DoesNotExist:
        raise Http404
    label_name = str(s.LabelUrlPath).split("/")[-1]

    if label_name != "placeholder.png":
        file_path = os.path.join(settings.LABELS_DIR, label_name)
        if path.exists(file_path):
            with open(file_path, "rb") as fh:
                response = HttpResponse(fh.read(), content_type="image/*")
                response["Content-Disposition"] = "inline; filename=" + path.basename(
                    file_path
                )
                return response
    if s.SlideType == 1:
        ds = pydicom.dcmread(os.path.join(settings.SLIDES_DIR, s.UrlPath))
        label = get_PIL_image(ds)
        response = HttpResponse(content_type="image/png")
        label.thumbnail(MAX_THUMBNAIL_SIZE)
        label.save(response, "PNG", optimize=True, quality=95)
        response["Content-Disposition"] = 'attachment; filename="label.png"'
        return response
    else:
        file = os.path.join(settings.SLIDES_DIR, s.UrlPath)
        slide = OpenSlide(file)
        if (
            "label" in slide.associated_images.keys()
            and slide.associated_images["label"] != None
        ):
            response = HttpResponse(content_type="image/png")
            label = slide.associated_images["label"]
            if label.size[0] < label.size[1]:
                label = label.transpose(Image.ROTATE_270)
            label.save(response, "PNG")
            response["Content-Disposition"] = 'attachment; filename="label.png"'
            return response
        elif (
            "macro" in slide.associated_images.keys()
            and slide.associated_images["macro"] != None
        ):
            response = HttpResponse(content_type="image/png")
            label = slide.associated_images["macro"]
            basewidth = 600
            wpercent = basewidth / float(label.size[0])
            hsize = int((float(label.size[1]) * float(wpercent)))
            label = label.resize((basewidth, hsize), Image.ANTIALIAS)
            if label.size[0] > label.size[1]:
                label = label.transpose(Image.ROTATE_270)
            label.save(response, "PNG")
            response["Content-Disposition"] = 'attachment; filename="label.png"'
            return response
        else:
            file_path = settings.STATICFILES_DIRS[0] + "/images/placeholder-image.png"
            if path.exists(file_path):
                with open(file_path, "rb") as fh:
                    response = HttpResponse(fh.read(), content_type="image/*")
                    response[
                        "Content-Disposition"
                    ] = "inline; filename=" + path.basename(file_path)
                    return response
            raise Http404


def get_thumbnail(request, slide_id):
    try:
        s = Slide.objects.get(pk=slide_id)
    except Slide.DoesNotExist:
        raise Http404
    label_name = str(s.LabelUrlPath).split("/")[-1]
    if label_name != "placeholder.png":
        file_path = os.path.join(settings.LABELS_DIR, label_name)
        if path.exists(file_path):
            with open(file_path, "rb") as fh:
                response = HttpResponse(fh.read(), content_type="image/*")
                response["Content-Disposition"] = "inline; filename=" + path.basename(
                    file_path
                )
                return response
    if s.SlideType == 1:
        ds = pydicom.dcmread(os.path.join(settings.SLIDES_DIR, s.UrlPath))
        label = get_PIL_image(ds)
        response = HttpResponse(content_type="image/png")
        label.thumbnail(MAX_THUMBNAIL_SIZE)
        label.save(response, "PNG", optimize=True, quality=95)
        response["Content-Disposition"] = 'attachment; filename="label.png"'
        return response
    else:
        file = os.path.join(settings.SLIDES_DIR, s.UrlPath)
        slide = OpenSlide(file)
        if (
            "macro" in slide.associated_images.keys()
            and slide.associated_images["macro"] != None
        ):
            response = HttpResponse(content_type="image/png")
            label = slide.associated_images["macro"]
            if label.size[0] > label.size[1]:
                label = label.transpose(Image.ROTATE_270)
            basewidth = 200
            wpercent = basewidth / float(label.size[0])
            hsize = int((float(label.size[1]) * float(wpercent)))
            label = label.resize((basewidth, hsize), Image.ANTIALIAS)
            if label.size[1] > 620:
                label = label.crop((0, 120, label.size[0], label.size[1]))

            if (
                "label" in slide.associated_images.keys()
                and slide.associated_images["label"] != None
            ):
                barcode = slide.associated_images["label"]
                if barcode.size[0] < barcode.size[1]:
                    barcode = barcode.transpose(Image.ROTATE_270)
                bw = 200
                wp = bw / float(barcode.size[0])
                hs = int((float(barcode.size[1]) * float(wp)))
                barcode = barcode.resize((bw, hs), Image.ANTIALIAS)
                new_image = Image.new(
                    "RGB", (200, barcode.size[1] + label.size[1]), (250, 250, 250)
                )
                new_image.paste(barcode, (0, 0))
                new_image.paste(label, (0, barcode.size[1]))
                label = new_image

            label.save(response, "PNG")
            response["Content-Disposition"] = 'attachment; filename="label.png"'
            return response
        else:
            file_path = settings.STATICFILES_DIRS[0] + "/images/placeholder-image.png"
            if path.exists(file_path):
                with open(file_path, "rb") as fh:
                    response = HttpResponse(fh.read(), content_type="image/*")
                    response[
                        "Content-Disposition"
                    ] = "inline; filename=" + path.basename(file_path)
                    return response
            raise Http404


def get_barcode(request, slide_id):
    try:
        s = Slide.objects.get(pk=slide_id)
    except Slide.DoesNotExist:
        raise Http404
    if s.SlideType == 1:
        ds = pydicom.dcmread(os.path.join(settings.SLIDES_DIR, s.UrlPath))
        label = get_PIL_image(ds)
        response = HttpResponse(content_type="image/png")
        label.thumbnail(MAX_THUMBNAIL_SIZE)
        label.save(response, "PNG")
        response["Content-Disposition"] = 'attachment; filename="label.png"'
        return response
    else:
        file = os.path.join(settings.SLIDES_DIR, s.UrlPath)
        print(file, "\n\n\n")
        slide = OpenSlide(file)
        if (
            "label" in slide.associated_images.keys()
            and slide.associated_images["label"] != None
        ):
            response = HttpResponse(content_type="image/png")
            label = slide.associated_images["label"]
            if label.size[0] < label.size[1]:
                label = label.transpose(Image.ROTATE_270)
            basewidth = 200
            wpercent = basewidth / float(label.size[0])
            hsize = int((float(label.size[1]) * float(wpercent)))
            label = label.resize((basewidth, hsize), Image.ANTIALIAS)
            label.save(response, "PNG")
            response["Content-Disposition"] = 'attachment; filename="barcode.png"'
            return response
        elif (
            "macro" in slide.associated_images.keys()
            and slide.associated_images["macro"] != None
        ):
            response = HttpResponse(content_type="image/png")
            label = slide.associated_images["macro"]
            if label.size[0] > label.size[1]:
                label = label.transpose(Image.ROTATE_270)
            basewidth = 200
            wpercent = basewidth / float(label.size[0])
            hsize = int((float(label.size[1]) * float(wpercent)))
            label = label.resize((basewidth, hsize), Image.ANTIALIAS)
            label = label.crop((0, 0, 200, 200))
            label.save(response, "PNG")
            response["Content-Disposition"] = 'attachment; filename="barcode.png"'
            return response
        else:
            file_path = settings.STATICFILES_DIRS[0] + "/images/placeholder-image.png"
            if path.exists(file_path):
                with open(file_path, "rb") as fh:
                    response = HttpResponse(fh.read(), content_type="image/*")
                    response[
                        "Content-Disposition"
                    ] = "inline; filename=" + path.basename(file_path)
                    return response
            raise Http404


def get_group_list(request, slide_id):
    try:
        s = Slide.objects.get(pk=slide_id)
    except Slide.DoesNotExist:
        raise Http404
    parent = s.Folder
    listSlide = Slide.objects.filter(Folder=parent).order_by("Name")

    return JsonResponse(
        {
            "status": "success",
            "slides": [{"id": l.id, "name": l.Name} for l in listSlide],
        }
    )


def get_property(request, slide_id):
    try:
        s = Slide.objects.get(pk=slide_id)
    except Slide.DoesNotExist:
        raise Http404

    if s.SlideType == 2:
        file = os.path.join(settings.SLIDES_DIR, s.UrlPath)
        slide = OpenSlide(file)
        return JsonResponse({"status": "success", "data": dict(slide.properties)})
    else:
        return JsonResponse({"status": "success", "data": dict()})


def get_name(request, slide_id):
    try:
        s = Slide.objects.get(pk=slide_id)
    except Slide.DoesNotExist:
        raise Http404
    return JsonResponse({"status": "success", "name": s.Name})


def download_slide(request, slide_id):
    try:
        s = Slide.objects.get(pk=slide_id)
    except Slide.DoesNotExist:
        raise Http404
    file_path = os.path.join(settings.SLIDES_DIR, s.UrlPath)
    if path.exists(file_path):
        with open(file_path, "rb") as fh:
            response = HttpResponse(fh.read(), content_type="application/octet-stream")
            response["Content-Disposition"] = "inline; filename=" + path.basename(
                file_path
            )
            return response
    raise Http404


def delete_slide(request, slide_id):
    try:
        s = Slide.objects.get(pk=slide_id)
    except Slide.DoesNotExist:
        raise Http404
    return render(
        request,
        "deleteConfirm.html",
        {
            "name": s.Name,
            "filename": path.basename(str(s.UrlPath)),
            "url": request.build_absolute_uri() + "confirm",
        },
    )


def delete_confirm_slide(request, slide_id):
    if request.method == "POST":
        key = request.POST["key"]
        if key == "~$A=+V_SR3[jsRd<":
            try:
                s = Slide.objects.get(pk=slide_id)
                file = os.path.join(settings.SLIDES_DIR, s.UrlPath)
                remove(file)
                s.delete()
                return JsonResponse({"status": "success"})
            except Slide.DoesNotExist:
                raise Http404
        else:
            raise Http404
    else:
        raise Http404


def add_annotation(request):
    if request.method == "POST":
        data = request.POST
        slide = Slide.objects.get(pk=int(data["slideId"]))
        annotation = Annotation(
            Slide_Id=slide,
            Json=data["Json"],
            AnnotationText=data["text"],
            Type=data["type"],
        )

        annotation.save()
        return JsonResponse({"id": annotation.id})


def delete_annotation(request, id):
    if request.method == "POST":
        toBeDeleted = Annotation.objects.get(pk=(int(id)))

        toBeDeleted.delete()
        return JsonResponse({"success": True})


def edit_annotation(request, id):
    if request.method == "POST":
        annotation = Annotation.objects.get(pk=(int(id)))
        data = request.POST
        try:
            annotation.Json = data["json"]
        except (KeyError):
            pass
        try:
            annotation.AnnotationText = data["text"]
        except (KeyError):
            pass
        annotation.save()

        return JsonResponse({"success": True})


def get_annotation(request, slide_id):
    if request.method == "GET":
        annotations = Annotation.objects.filter(Slide_Id=slide_id)

        return JsonResponse(
            {
                "annotations": [
                    {
                        "id": annotation.id,
                        "json": annotation.Json,
                        "text": annotation.AnnotationText,
                        "type": annotation.Type,
                    }
                    for annotation in annotations
                ]
            }
        )


def my_slides(request, *args):
    ctx = {"slides": Slide.objects.all()}
    return render(request, "my_slides.html", ctx)
