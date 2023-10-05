import os
import sys
import logging
import torch

MATPLOTLIB_FLAG = False

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging


def load_checkpoint(checkpoint_path, model, optimizer=None, skip_optimizer=False, legacy_version=None):
    assert os.path.isfile(checkpoint_path)
    checkpoint_dict = torch.load(checkpoint_path, map_location='cpu')
    iteration = checkpoint_dict['iteration']
    learning_rate = checkpoint_dict['learning_rate']
    if optimizer is not None and not skip_optimizer and checkpoint_dict['optimizer'] is not None:
        optimizer.load_state_dict(checkpoint_dict['optimizer'])
    elif optimizer is None and not skip_optimizer:
        # else: #Disable this line if Infer ,and enable the line upper
        new_opt_dict = optimizer.state_dict()
        new_opt_dict_params = new_opt_dict['param_groups'][0]['params']
        new_opt_dict['param_groups'] = checkpoint_dict['optimizer']['param_groups']
        new_opt_dict['param_groups'][0]['params'] = new_opt_dict_params
        optimizer.load_state_dict(new_opt_dict)
    saved_state_dict = checkpoint_dict['model']
    if hasattr(model, 'module'):
        state_dict = model.module.state_dict()
    else:
        state_dict = model.state_dict()
    new_state_dict = {}
    for k, v in state_dict.items():
        try:
            # assert "emb_g" not in k
            # print("load", k)
            new_state_dict[k] = saved_state_dict[k]
            assert saved_state_dict[k].shape == v.shape, (saved_state_dict[k].shape, v.shape)
        except:
            # For upgrading from the old version
            if "ja_bert_proj" in k:
                v = torch.zeros_like(v)
                if legacy_version is None:
                    logger.error(f"{k} is not in the checkpoint")
                    logger.warning(
                        f"If you are using an older version of the model, you should add the parameter \"legacy_version\" "
                        f"to the parameter \"data\" of the model's config.json. For example: \"legacy_version\": \"1.0.1\"")
            else:
                logger.error(f"{k} is not in the checkpoint")

            new_state_dict[k] = v
    if hasattr(model, 'module'):
        model.module.load_state_dict(new_state_dict, strict=False)
    else:
        model.load_state_dict(new_state_dict, strict=False)
    # print("load ")
    logger.info("Loaded checkpoint '{}' (iteration {})".format(
        checkpoint_path, iteration))
    return model, optimizer, learning_rate, iteration


def process_legacy_versions(hps):
    legacy_version = getattr(hps.data, "legacy", getattr(hps.data, "legacy_version", None))
    if legacy_version:
        prefix = legacy_version[0].lower()
        if prefix == "v":
            legacy_version = legacy_version[1:]
    return legacy_version
