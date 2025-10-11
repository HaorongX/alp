from flask import Response, request

images = {}

def upload_image(id, image):
    global images
    if id in images:
        images[id].append(image)
    else:
        images[id] = [image]
    print(f"Image {id} uploaded successfully.")

def get_image():
    global images
    return Response(images[request.args.get('id')], mimetype="image/png")