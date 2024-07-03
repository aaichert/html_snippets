import io
import base64
from PIL import Image

def html_thumbnail_link(path, common_path='', prefix_path='', size=[64, 64]):
    image = Image.open(path) 
    image.thumbnail(size)
    if path.startswith(common_path):
        path = path[len(common_path):]
    return f"<a href='{prefix_path+path}'>"+html_image(image)+"</a>"


def html_image(image, scale=None):
    buffer = io.BytesIO()
    image.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    data_uri = base64.b64encode(buffer.read()).decode('ascii')
    if scale is not None:
        w, h = round(scale*image.size[0]), round(scale*image.size[1])
        return f'<img width="{w}" height="{h}" src="data:image/png;base64,{data_uri}"/>'        
    else:
        return f'<img src="data:image/png;base64,{data_uri}"/>'

def html_image_src(image_path):
    return f'<img src="{image_path}"/>'
