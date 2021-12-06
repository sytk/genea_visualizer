# Copyright 2020 by Patrik Jonell.
# All rights reserved.
# This file is part of the GENEA visualizer,
# and is released under the GPLv3 License. Please see the LICENSE
# file that should have been included as part of this package.

import requests
from pathlib import Path
import time

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("bvh_file", type=Path)
parser.add_argument("--server_url", default="http://localhost:5001")
parser.add_argument("--output", type=Path)

args = parser.parse_args()

server_url = args.server_url
bvh_file = args.bvh_file
output = args.output if args.output else bvh_file.with_suffix(".mp4")

headers = {"Authorization": "Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz"}


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


# def main(bvh_root, audio_root, bvh_NT_root):
#     output_path = bvh_root + '/mp4'
#
#     if not os.path.exists(output_path):
#         os.makedirs(output_path)
#
#     # for name in os.listdir(output_path):
#     #     os.remove(os.path.join(output_path, name))
#
#     file_num = sum(os.path.isfile(os.path.join(output_path, name)) for name in os.listdir(output_path))
#     if file_num != 0:
#         return
#
#     bvh_files = glob.glob(os.path.join(bvh_root, '*.bvh'))
#     bvh_files = sort_bvh(bvh_files)
#
#     audio_files = glob.glob(os.path.join(audio_root, '*.wav'))
#     audio_files = sort_files(audio_files)
#     NT_files = glob.glob(os.path.join(bvh_NT_root, '*.bvh'))
#     NT_files = sort_files(NT_files)
#
#     for NT, files in zip(NT_files, bvh_files):
#         files.insert(0, NT)
#
#     # for b, a in zip(bvh_files, audio_files):
#     #     print(b, a)
#
#     assert len(bvh_files) == len(audio_files), 'file length error'
#     assert len(bvh_files) == len(NT_files), 'file length error'
#
#     for i, (bvh_file, audio_file) in enumerate(zip(bvh_files, audio_files)):
#         name_tag = [re.findall('sampled_.', file)[0][-1] for file in bvh_file[1:]]
#         name_tag.insert(0, "NT")
#
#         name = str(i) + '_' + '_'.join(name_tag) + '_' + '_'.join(bvh_root.split('\\')[-2:])
#         video_path = output_path + '/' + name + '_motion' + '.mp4'
#         audio_video_path = output_path + '/' + name + '_video' + '.mp4'
#
#         n = len(name_tag)
#         gap = 80
#         scale = n*gap/2
#
#         plot_animation_pymo(bvh_file,
#                             annotation=True,
#                             fps=20,
#                             output_filename=video_path,
#                             name_tag=name_tag,
#                             axis_scale=scale,
#                             title=None,
#                             figsize=(max(5, gap*n/100*4), 5)
#                             )
#
#         concatenate_mp4_wav(video_path,
#                             audio_file,
#                             audio_video_path
#                             )
#         os.remove(video_path)
#
#
# if __name__ == "__main__":
#
#     bvh_roots = glob.glob(os.path.join('../../results/GENEA', 'log*', 'test_generated*'))
#     audio_root = '../../data/GENEA/processed/visualization_test'
#     bvh_NT_root = '../../results/GENEA/NT_test'
#
#     for bvh_root in bvh_roots:
#         print(bvh_root)
#         main(bvh_root, audio_root, bvh_NT_root)
#
