img_dir='img'
sd_url='http://127.0.0.1:7860'

txt2image_payload = {
  'seed': -1,
  'sampler_name': 'DDIM',
  'batch_size': 1,
  'n_iter': 1,
  'steps': 20,
  'cfg_scale': 7,
  'width': 512,
  'height': 512,
}

options_payload = {
    'sd_model_checkpoint': 'chilloutmix_NiPrunedFp16Fix.safetensors [59ffe2243a]',
}

model_map = {
    'chilloutmix': 'chilloutmix_NiPrunedFp16Fix.safetensors [59ffe2243a]',
    'abyssorangemix': 'abyssorangemix3AOM3_aom3a3.safetensors [eb4099ba9c]',
    
}