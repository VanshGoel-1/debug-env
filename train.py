"""
RL Training: debug-env + TRL GRPOTrainer + Unsloth

Prerequisites:
    pip install -e ".[training]"
    pip install "unsloth[cu124-torch240] @ git+https://github.com/unslothai/unsloth.git"
    # OR: pip install unsloth --torch-backend=auto

    # Server must be running in a separate terminal:
    uv run server

Usage:
    python train.py                                  # all tasks, curriculum order
    TASK_FILTER=easy python train.py                 # only easy tasks (start here)
    MODEL=Qwen/Qwen2.5-1.5B-Instruct python train.py  # smaller model for low VRAM
    TRAIN_STEPS=50 TASK_FILTER=easy python train.py  # quick sanity check

Environment variables:
    MODEL          HuggingFace model ID (default: Qwen/Qwen2.5-7B-Instruct)
    MAX_SEQ_LEN    Max token length (default: 2048)
    OUTPUT_DIR     Where to save the trained model (default: debug-env-grpo)
    TRAIN_STEPS    Number of gradient steps (default: 600)
    BATCH_SIZE     Per-device train batch size (default: 1)
    NUM_GEN        GRPO group size — completions per prompt (default: 4)
    LR             Learning rate (default: 2e-4)
    TASK_FILTER    "easy" | "medium" | "hard" | unset (all tasks)

VRAM reference (Unsloth 4-bit QLoRA):
    Qwen2.5-1.5B  →  ~2 GB   (any modern GPU)
    Qwen2.5-7B    →  ~6 GB   (RTX 3060+)
    Qwen2.5-14B   →  ~10 GB  (RTX 3080+)
"""

import os

from trl import GRPOConfig, GRPOTrainer
from unsloth import FastLanguageModel

from debug_env.rl.dataset import build_dataset
from debug_env.rl.rollout import debug_reward

# ── Config ────────────────────────────────────────────────────────────────────

MODEL_NAME      = os.getenv("MODEL", "Qwen/Qwen2.5-7B-Instruct")
MAX_SEQ_LEN     = int(os.getenv("MAX_SEQ_LEN", "2048"))
OUTPUT_DIR      = os.getenv("OUTPUT_DIR", "debug-env-grpo")
MAX_STEPS       = int(os.getenv("TRAIN_STEPS", "600"))
BATCH_SIZE      = int(os.getenv("BATCH_SIZE", "1"))
NUM_GENERATIONS = int(os.getenv("NUM_GEN", "4"))   # GRPO group size
LR              = float(os.getenv("LR", "2e-4"))
TASK_FILTER     = os.getenv("TASK_FILTER")          # "easy" | "medium" | "hard" | None

# ── Model ─────────────────────────────────────────────────────────────────────

model, tokenizer = FastLanguageModel.from_pretrained(
    MODEL_NAME,
    max_seq_length=MAX_SEQ_LEN,
    load_in_4bit=True,   # QLoRA — halves VRAM vs full precision
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=[
        "q_proj", "v_proj", "k_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_alpha=16,
    lora_dropout=0.0,
    bias="none",
    use_gradient_checkpointing="unsloth",  # Unsloth's custom checkpointing (saves ~30% VRAM)
)

# ── Dataset ───────────────────────────────────────────────────────────────────

dataset = build_dataset()
if TASK_FILTER:
    dataset = dataset.filter(lambda x: x["difficulty"] == TASK_FILTER)

print(f"Dataset: {len(dataset)} prompts")
print(f"Difficulty breakdown: {dataset.to_pandas()['difficulty'].value_counts().to_dict()}")

# ── Trainer ───────────────────────────────────────────────────────────────────

trainer = GRPOTrainer(
    model=model,
    reward_funcs=debug_reward,   # calls debug-env server at http://127.0.0.1:8000
    train_dataset=dataset,
    args=GRPOConfig(
        output_dir=OUTPUT_DIR,
        max_steps=MAX_STEPS,
        per_device_train_batch_size=BATCH_SIZE,
        num_generations=NUM_GENERATIONS,
        learning_rate=LR,
        lr_scheduler_type="linear",
        warmup_ratio=0.1,
        logging_steps=10,
        save_steps=100,
        bf16=True,
        report_to="none",   # set to "wandb" if you have Weights & Biases configured
    ),
)

trainer.train()

# ── Save ──────────────────────────────────────────────────────────────────────

model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"Model saved to {OUTPUT_DIR}/")

# Push to HF Hub (optional — uncomment and set your username):
# model.push_to_hub("your-username/debug-env-grpo")
# tokenizer.push_to_hub("your-username/debug-env-grpo")
