import torch
from ..common.utils import get_total_sample_num
from .defense_base import BaseDefenseMethod

"""
defense @ server, added by Shanshan, 07/09/2022
To defense backdoor attack.

"Defending against backdoors in federated learning with robust learning rate. "
https://github.com/TinfoilHat0/Defending-Against-Backdoors-with-Robust-Learning-Rate

This ``learning rate'' in this paper indicates a weight at the server side when aggregating weights from clients. 
Normally, the learning rate is 1.
If backdoor attack is detected, e.g., exceed a robust threshold, the learning rate is set to -1.

Steps: 
1) compute client_update sign for each client, which can be 1 or -1
2) sum up the client update signs and compute learning rates for each client, which can be 1 or -1.
3) use the learning rate for each client to compute a new model.
"""


class RobustLearningRateDefense(BaseDefenseMethod):
    def __init__(self, robust_threshold):
        self.robust_threshold = robust_threshold  # e.g., robust threshold = 4
        self.server_learning_rate = 1

    def defend(self, model_list, global_w=None, refs=None):
        total_sample_num = get_total_sample_num(model_list)
        (num0, avg_params) = model_list[0]
        for k in avg_params.keys():
            client_update_sign = []  # self._compute_robust_learning_rates(model_list)
            for i in range(0, len(model_list)):
                local_sample_number, local_model_params = model_list[i]
                client_update_sign.append(torch.sign(local_model_params[k]))
                w = local_sample_number / total_sample_num
                if i == 0:
                    avg_params[k] = local_model_params[k] * w
                else:
                    avg_params[k] += local_model_params[k] * w
            if self.robust_threshold > 0:
                client_lr = self._compute_robust_learning_rates(client_update_sign)
                avg_params[k] = client_lr * avg_params[k]
        return avg_params

    def _compute_robust_learning_rates(self, client_update_sign):
        client_lr = torch.abs(sum(client_update_sign))
        client_lr[client_lr < self.robust_threshold] = -self.server_learning_rate
        client_lr[client_lr >= self.robust_threshold] = self.server_learning_rate
        return client_lr
