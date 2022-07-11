import logging

import torch
from fedml.constants import FEDML_CROSS_SILO_SCENARIO_HIERARCHICAL, FEDML_TRAINING_PLATFORM_CROSS_SILO

def get_device(args):
    if args.training_type == "simulation" and args.backend == "sp":
        if args.using_gpu:
            device = torch.device(
                "cuda:" + str(args.gpu_id)
                if torch.cuda.is_available()
                else "cpu"
            )
        else:
            device = torch.device("cpu")
        logging.info("device = {}".format(device))
        return device
    elif args.training_type == "simulation" and args.backend == "MPI":
        from .gpu_mapping_mpi import (
            mapping_processes_to_gpu_device_from_yaml_file_mpi,
        )

        device = mapping_processes_to_gpu_device_from_yaml_file_mpi(
            args.process_id,
            args.worker_num,
            args.gpu_mapping_file if args.using_gpu else None,
            args.gpu_mapping_key,
        )
        return device
    elif args.training_type == "simulation" and args.backend == "NCCL":
        from .gpu_mapping_mpi import (
            mapping_processes_to_gpu_device_from_yaml_file_mpi,
        )

        device = mapping_processes_to_gpu_device_from_yaml_file_mpi(
            args.process_id,
            args.worker_num,
            args.gpu_mapping_file if args.using_gpu else None,
            args.gpu_mapping_key,
        )
        return device
    elif args.training_type == FEDML_TRAINING_PLATFORM_CROSS_SILO:

        if args.scenario == FEDML_CROSS_SILO_SCENARIO_HIERARCHICAL:
            from .gpu_mapping_cross_silo import (
                mapping_processes_to_gpu_device_from_yaml_file_cross_silo,
            )

            device = mapping_processes_to_gpu_device_from_yaml_file_cross_silo(
                args.proc_rank_in_silo,
                args.n_proc_in_silo,
                args.gpu_mapping_file if args.using_gpu else None,
                args.gpu_mapping_key if args.using_gpu else None,
                FEDML_CROSS_SILO_SCENARIO_HIERARCHICAL
            )
        else:
            from .gpu_mapping_cross_silo import (
                mapping_single_process_to_gpu_device_cross_silo,
            )

            device_type = (
                "gpu" if not hasattr(args, "device_type") else args.device_type
            )

            gpu_id = 0 if not hasattr(args, "gpu_id") else args.gpu_id

            device = mapping_single_process_to_gpu_device_cross_silo(
                args.using_gpu, device_type, gpu_id
            )


        logging.info("device = {}".format(device))

        # Flag indicating the process will communicate with other clients
        is_master_process = (args.scenario == "horizontal") or (
            args.scenario == "hierarchical" and args.proc_rank_in_silo == 0
        )

        if args.enable_cuda_rpc and is_master_process:
            assert (
                device.index == args.cuda_rpc_gpu_mapping[args.rank]
            ), f"GPU assignemnt inconsistent with cuda_rpc_gpu_mapping. Assigned to GPU {device.index} while expecting {args.cuda_rpc_gpu_mapping[args.rank]}"

        return device
    elif args.training_type == "cross_device":
        if args.using_gpu:
            device = torch.device(
                "cuda:" + args.gpu_id if torch.cuda.is_available() else "cpu"
            )
        else:
            device = torch.device("cpu")
        logging.info("device = {}".format(device))
        return device
    else:
        raise Exception(
            "the training type {} is not defined!".format(args.training_type)
        )
