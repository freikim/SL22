from utils import crop, resize

IMG_SIZE = 256

frame_proportion = 0.9
frame_offset_x = 0
frame_offset_y = 0


def update(predictor, frame):
    frame = frame[..., ::-1]
    frame_orig = frame.copy()

    frame, (frame_offset_x, frame_offset_y) = crop(frame, p=frame_proportion, offset_x=frame_offset_x,
                                                   offset_y=frame_offset_y)

    frame = resize(frame, (IMG_SIZE, IMG_SIZE))[..., :3]

    out = predictor.predict(frame)