import os
import torch
from diffusers import DiffusionPipeline
from evolutionary_prompt_embedding.image_creation import SDXLPromptEmbeddingImageCreator

# Optional imports for enhanced performance
try:
    from xformers import is_available as _xformers_available
    _HAS_XFORMERS = True
except ImportError:
    _HAS_XFORMERS = False

# Optional dynamic quantization support
try:
    import torchao
    _HAS_TORCHAO = True
except ImportError:
    _HAS_TORCHAO = False

class SDXLPromptEmbeddingGeneratorTuned(SDXLPromptEmbeddingImageCreator):
    """Custom class with tunable parameters for the pipeline to improve generation speed."""
    def __init__(self, inference_steps: int, batch_size: int, deterministic: bool = True):
        super().__init__(inference_steps, batch_size, deterministic)

    def _setup_diffusers_pipeline(self) -> DiffusionPipeline:
        print("Setting up the pipeline with tuned parameters...")
        # Bypass CUDA optimizations on MPS
        if torch.backends.mps.is_available():
            return super()._setup_diffusers_pipeline()

        model_id = self._model_id
        # 1) Mixed precision: default FP16, optional BF16
        use_bf16 = os.getenv("PERF_USE_BF16", "False") == "True"
        dtype = torch.bfloat16 if use_bf16 else torch.float16
        print(f"Using {'BF16' if use_bf16 else 'FP16'} precision")

        # 2) Load pipeline and move to CUDA
        pipe = DiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=dtype,
            use_safetensors=True,
            safety_checker=None if os.getenv("PERF_DISABLE_SAFETY", "False") == "True" else None
        ).to("cuda")

        # 3) Channels-last memory format (optional)
        if os.getenv("PERF_USE_CHANNELS_LAST", "False") == "True":
            pipe.unet.to(memory_format=torch.channels_last)
            pipe.vae.to(memory_format=torch.channels_last)
            print("Channels-last memory format enabled")

        # 4) Memory-efficient attention (optional)
        if os.getenv("PERF_USE_XFORMERS", "False") == "True":
            if _HAS_XFORMERS and _xformers_available():
                pipe.enable_xformers_memory_efficient_attention()
                print("xFormers memory-efficient attention enabled")
            else:
                print("xFormers not available; skipping memory-efficient attention")

        # 5) Attention slicing (optional)
        if os.getenv("PERF_USE_ATTENTION_SLICING", "False") == "True":
            pipe.enable_attention_slicing()
            print("Attention slicing enabled")

        # 6) VAE slicing (optional)
        if os.getenv("PERF_USE_VAE_SLICING", "False") == "True":
            pipe.enable_vae_slicing()
            print("VAE slicing enabled")

        # 7) Model CPU offload (optional)
        if os.getenv("PERF_USE_CPU_OFFLOAD", "False") == "True":
            pipe.enable_model_cpu_offload()
            print("Model CPU offload enabled")

        # 8) Fuse QKV projections (optional, experimental)
        if os.getenv("PERF_USE_FUSE_QKV", "False") == "True" and hasattr(pipe, "fuse_qkv_projections"):
            pipe.fuse_qkv_projections()
            print("Fused QKV projections enabled")

        # 9) Torch 2.0 compile + SDPA (optional)
        if os.getenv("PERF_USE_TORCH_COMPILE", "False") == "True":
            try:
                from diffusers.models.attention_processor import FusedAttnProcessor2_0
                pipe.unet.set_attn_processor(FusedAttnProcessor2_0())
                print("Native PyTorch 2.0 attention processor enabled")
            except ImportError:
                pass
            pipe.unet = torch.compile(pipe.unet, mode="max-autotune", fullgraph=True)
            print("UNet compiled with torch.compile()")

        # 10) cuDNN autotuner & TF32
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.allow_tf32 = True
        print("cuDNN benchmark and TF32 enabled")

        # 11) MHA fastpath (optional)
        if hasattr(torch.backends, "mha") and hasattr(torch.backends.mha, "set_fastpath_enabled"):
            torch.backends.mha.set_fastpath_enabled(True)
            print("Multi-Head Attention fastpath enabled")

        # 12) Dynamic quantization (optional)
        if os.getenv("PERF_USE_DYNAMIC_QUANT", "False") == "True" and _HAS_TORCHAO:
            from torchao import apply_dynamic_quant, swap_conv2d_1x1_to_linear
            # Filter functions would be defined elsewhere
            pipe.unet = apply_dynamic_quant(pipe.unet)
            pipe.vae = apply_dynamic_quant(pipe.vae)
            print("Dynamic quantization enabled")

        # 13) Disable progress bar
        pipe.set_progress_bar_config(disable=True)
        return pipe
