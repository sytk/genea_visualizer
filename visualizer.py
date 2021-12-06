# Copyright 2020 by Patrik Jonell.
# All rights reserved.
# This file is part of the GENEA visualizer,
# and is released under the GPLv3 License. Please see the LICENSE
# file that should have been included as part of this package.

import requests
from pathlib import Path
import time
import re
import argparse
import glob
import os
from pathlib import Path
str_path = "my_path"


def makeMp4(bvh_file, output_path):

    server_url = "http://localhost:5001"
    output = output_path + '/' + os.path.basename(bvh_file) + '.mp4'

    headers = {"Authorization": "Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz"}

    bvh_file = Path(bvh_file)
    output = Path(output)

    render_request = requests.post(
        f"{server_url}/render",
        files={"file": (bvh_file.name, bvh_file.open())},
        headers=headers,
    )
    job_uri = render_request.text

    done = False
    while not done:
        resp = requests.get(server_url + job_uri, headers=headers)
        resp.raise_for_status()

        response = resp.json()

        if response["state"] == "PENDING":
            jobs_in_queue = response["result"]["jobs_in_queue"]
            print(f"pending.. {jobs_in_queue} jobs currently in queue")

        elif response["state"] == "PROCESSING":
            print("Processing the file (this can take a while depending on file size)")

        elif response["state"] == "RENDERING":
            current = response["result"]["current"]
            total = response["result"]["total"]
            print(f"currently rendering, {current}/{total} done")

        elif response["state"] == "SUCCESS":
            file_url = response["result"]
            done = True
            break

        elif response["state"] == "FAILURE":
            raise Exception(response["result"])
        else:
            print(response)
            raise Exception("should not happen..")
        time.sleep(10)

    video = requests.get(server_url + file_url, headers=headers).content
    output.write_bytes(video)

    return output


def concatenate_mp4_wav(mp4_file, wav_file, output_file):
    import ffmpeg
    instream_v = ffmpeg.input(mp4_file)
    instream_a = ffmpeg.input(wav_file)
    stream = ffmpeg.output(instream_v, instream_a,
                           output_file, vcodec="copy", acodec="aac")
    ffmpeg.run(stream)


def sort_bvh(files):
    nums = []
    for f in files:
        nums.append(int(re.findall('_0k_.', f)[-1][-1]))
    list = [[] for i in range(max(nums)+1)]
    for num, file in zip(nums, files):
        list[num].append(file)
    return list


def sort_files(files):
    nums = []
    for f in files:
        nums.append(int(f.split('_')[-1].split('.')[0]))
    zipped = zip(nums, files)
    zipped = sorted(zipped)
    nums, files = zip(*zipped)
    return files


def main(bvh_root, audio_root):
    output_path = bvh_root + '/body_mp4'

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    file_num = sum(os.path.isfile(os.path.join(output_path, name)) for name in os.listdir(output_path))

    if file_num != 0:
        return

    bvh_files = glob.glob(os.path.join(bvh_root, '*.bvh'))
    bvh_files = sort_bvh(bvh_files)

    audio_files = glob.glob(os.path.join(audio_root, '*.wav'))
    audio_files = sort_files(audio_files)

    for b, a in zip(bvh_files, audio_files):
        print(b, a)

    assert len(bvh_files) == len(audio_files), 'file length error'

    for i, (bvh_file, audio_file) in enumerate(zip(bvh_files, audio_files)):
        for bvh in bvh_file:
            video_path = makeMp4(bvh, output_path).name

            # concatenate_mp4_wav(video_path,
            #                     audio_file,
            #                     video_path+'.mp4'
            #                     )
            # os.remove(video_path)


if __name__ == "__main__":

    bvh_roots = glob.glob(os.path.join('./data.nosync', '*', 'test_generated*100*'))
    audio_root = './visualization_test'
    print(audio_root)
    for bvh_root in bvh_roots:
        print(bvh_root)
        main(bvh_root, audio_root)
