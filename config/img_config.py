import numpy as np

img_dir='img'
sd_url='http://127.0.0.1:7860'

txt2img_payload = {
    'sd_model_checkpoint': 'chilloutmix_NiPrunedFp16Fix.safetensors [59ffe2243a]',
    'seed': -1,
    'sampler_name': 'DPM++ 2M Karras',
    'batch_size': 1,
    'n_iter': 1,
    'steps': 20,
    'cfg_scale': 7,
    'height': 768,
    'width': 768,
}

model_map = {
    'abyssorangemix2': 'abyssorangemix2_Hard.safetensors [e714ee20aa]',
    'abyssorangemix3': 'abyssorangemix3AOM3_aom3a3.safetensors [eb4099ba9c]',
    'aoaoko': 'aoaokoPVCStyleModel_pvcAOAOKO.safetensors [cf64507cef]',
    'chilloutmix': 'chilloutmix_NiPrunedFp16Fix.safetensors [59ffe2243a]',
    'counterfeitv2.5': 'CounterfeitV25_25.safetensors [a074b8864e]',
    'dreamshaper': 'dreamshaper_4BakedVae.safetensors [7f16bbcd80]',
    'grapefruit': 'grapefruitHentaiModel_grapefruitv41.safetensors [c590550ea5]',
    'orangechillmix': 'orangechillmix_v70.safetensors [a92311f07a]',
    'pastelmix': 'pastelMixStylizedAnime_pastelMixPrunedFP16.safetensors [d01a68ae76]',
    'perfectworld': 'perfectWorld_v2Baked.safetensors [79e42fb744]',
    'revanimated': 'revAnimated_v11.safetensors [d725be5d18]',
}

sfw_models = ['counterfeitv2.5', 'dreamshaper', 'pastelmix', 'revanimated']

nsfw_models = [key for key in model_map.keys() if key not in sfw_models]

txt2img_keys = {'sampler_name', 'steps', 'cfg_scale', 'height', 'width'}

valid_options = {
    'sampler_name': ['DPM++ SDE Karras', 'DPM++ 2M Karras', 'DDIM', 'Euler a', 'Euler'],
    'steps': list(range(1, 151)),
    'cfg_scale': list(np.arange(1, 30.5, 0.5)),
    'height': [512, 768],
    'width': [512, 768],
}