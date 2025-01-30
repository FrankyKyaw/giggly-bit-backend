'''
Just trying to run laughter-detection end-to-end
'''

import dataclasses
import numpy as np
import os
import librosa
import scipy
import scipy.signal as signal 
import torch
from tqdm import tqdm

HOP_LENGTH = 186
N_FRAMES = 44
SAMPLE_RATE = 8000
BATCH_SIZE = 8
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
THRESHOLD = 0.5
MIN_LENGTH = 0.2
OUTPUT_DIR = './outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)


@dataclasses.dataclass
class LaughterDetectionOutput:
  wav_filename: str
  start_ts: float
  end_ts: float

def detect_laughter(audio_path: str, model: torch.nn.Module) -> list[LaughterDetectionOutput]:
  y, _ = librosa.load(audio_path, sr=SAMPLE_RATE)
  S = librosa.feature.melspectrogram(y=y, sr=SAMPLE_RATE, hop_length=HOP_LENGTH).T
  features = librosa.amplitude_to_db(S, ref=np.max)
  print('Features')
  print(features)

  probs = []
  for i in tqdm(range(0, len(features) - N_FRAMES - 1, BATCH_SIZE)):

    batch_inp = [features[j:j+N_FRAMES] for j in range(i, i+BATCH_SIZE) if (j+N_FRAMES) < len(features)]
    batch_inp = np.stack(batch_inp)
    batch_inp = torch.from_numpy(batch_inp).float().unsqueeze(1).to(DEVICE)

    with torch.no_grad(): preds = model(batch_inp).cpu().numpy().squeeze()
    preds = [float(preds)] if len(preds.shape) == 0 else list(preds)
    probs += preds

  probs = np.array(probs)

  # Apply butterworth lowpass filter
  B, A = signal.butter(2, 0.01, output='ba')
  probs = signal.filtfilt(B, A, probs)

  THRESHOLD = 0.5
  MIN_LENGTH = 0.2
  OUTPUT_DIR = ''
  audio_len = int(len(y)*100 / SAMPLE_RATE) / 100
  fps = len(probs) / audio_len

  # thresholding
  instances = []
  current_list = []
  for i in range(len(probs)):
      if np.min(probs[i:i+1]) > THRESHOLD:
          current_list.append(i)
      else:
          if len(current_list) > 0:
              instances.append(current_list)
              current_list = []

  if len(current_list) > 0: instances.append(current_list)

  def frame_span_to_time_span(frame_span, fps): return (frame_span[0] / fps, frame_span[1] / fps)
  def collapse_to_start_and_end_frame(instance_list): return (instance_list[0], instance_list[-1])

  instances = [frame_span_to_time_span(collapse_to_start_and_end_frame(i), fps) for i in instances]
  instances = [inst for inst in instances if inst[1]-inst[0] > MIN_LENGTH]

  full_res_y, full_res_sr = librosa.load(audio_path,sr=44100)
  maxv = np.iinfo(np.int16).max

  def seconds_to_samples(s,sr): return s*sr
  def cut_laughter_segments(instance_list,y,sr):
    new_audio = []
    for start, end in instance_list:
      sample_start = int(seconds_to_samples(start,sr))
      sample_end = int(seconds_to_samples(end,sr))
      clip = y[sample_start:sample_end]
      new_audio = np.concatenate([new_audio,clip])
    return new_audio

  ret = []
  for index, instance in enumerate(instances):
    laughs = cut_laughter_segments([instance],full_res_y,full_res_sr)
    output_dir = os.path.dirname(os.path.abspath(audio_path))
    wav_path = os.path.join(output_dir, f'laugh_{index}.wav')
    scipy.io.wavfile.write(wav_path, full_res_sr, (laughs * maxv).astype(np.int16))
    ret.append(LaughterDetectionOutput(wav_path, instance[0], instance[1]))

  return ret
