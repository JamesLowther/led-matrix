from PIL import Image
import cv2
import numpy as np
import os, shutil
import argparse
import json
import tarfile

def pixelate(img, w, h):
    return cv2.resize(img, (w, h), interpolation=cv2.INTER_LINEAR)

def main():
    """Entry point.
    """
    # Parse arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str,
                        help="path to video file to convert")
    parser.add_argument("output_dir", type=str, help="path to output dir")
    parser.add_argument("-x", "--width", type=int,
                        help="width (in pixels) of output. default 64", default=64)
    parser.add_argument("-y", "--height", type=int,
                        help="height (in pixels) of output. default 32", default=32)
    parser.add_argument("-n", "--num-frames", type=int,
                        help="number of frames to convert. -1 for all. default -1", default=-1)
    parser.add_argument("-f", "--fps", type=int,
                        help="fps of new video. default 24", default=24)
    parser.add_argument("-o", "--offset", type=int,
                        help="video offset. default 0", default=0)

    args = parser.parse_args()

    # Check if file exists.
    if not os.path.isfile(args.input_file) or not os.path.exists(args.input_file):
        print("File " + args.input_file + " not found")
        exit(1)

    # Open files.
    cap = cv2.VideoCapture(args.input_file)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    tar = tarfile.open(f"{args.output_dir}.tar.gz", "w:gz") 

    if args.num_frames != -1:
        frame_count = min(frame_count, args.num_frames)
    
    # Print configuration.
    print(f"Input:  {args.input_file}")
    print(f"Output: {args.output_dir}")
    print(f"Width:  {args.width}")
    print(f"Height: {args.height}")
    print(f"Frames: {frame_count}")
    print(f"FPS:    {args.fps}")
    print(f"Offset: {args.offset}")
    print()

    # Make output dir.
    if os.path.exists(args.output_dir) or os.path.exists(f"{args.output_dir}.tar.gz"):
        r = input(f"Files for {args.output_dir} already exist. Overwrite? [y/N]: ")
        if r.lower() != "y":
            exit(0)

    # Delete existing output path.
    if os.path.isfile(args.output_dir):
        os.remove(args.output_dir)
    elif os.path.isdir(args.output_dir):
        shutil.rmtree(args.output_dir)

    os.mkdir(args.output_dir)

    for i in range(args.offset):
        ret, _ = cap.read()
        if not ret:
            break

    print("Starting conversion...")
    current_frame = 1
    while args.num_frames == -1 or current_frame <= frame_count:
        print(f"Converting {current_frame}/{frame_count}", end="\r")
        ret, frame = cap.read()
        if ret == True:
            resized = pixelate(frame, args.width, args.height)

            file_name = str(current_frame-1).zfill(len(str(frame_count-1)))
            file_path = f"./{args.output_dir}/{file_name}.png"

            cv2.imwrite(file_path, resized)
            tar.add(file_path)
        else:
            break

        current_frame += 1

    cap.release()
    cv2.destroyAllWindows()

    # Write fps data.
    metadata = {
        "fps": args.fps
    }
    
    meta_path = os.path.join(args.output_dir, "metadata.json")
    with open(meta_path, "w") as of:
        json.dump(metadata, of)
        of.close()

    tar.add(meta_path)

    print("\nDone.")

if __name__ == "__main__":
    main()
