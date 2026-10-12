"""DeepSeek-R1-Distill-Qwen-7B QLoRA training entrypoint.

Default mode is a local dry-run. Pass --run explicitly on the AutoDL host to
download/load the configured model and start training.
"""
from __future__ import annotations

import argparse
import inspect
import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_cfg() -> dict:
    try:
        import yaml
    except ModuleNotFoundError:
        print("[train] 未安装 pyyaml，无法读取配置。")
        sys.exit(1)
    return yaml.safe_load((ROOT / "lora_config.yaml").read_text(encoding="utf-8"))


def check_dataset(path: Path) -> int:
    if not path.exists():
        print(f"[train] 缺少数据集 {path}")
        sys.exit(1)
    count = 0
    with path.open(encoding="utf-8") as file:
        for line_no, line in enumerate(file, start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"[train] JSONL 格式错误: {path}:{line_no}: {exc}")
                sys.exit(1)
            missing = [key for key in ("instruction", "input", "output") if key not in row]
            if missing:
                print(f"[train] 数据集缺少字段 {missing}: {path}:{line_no}")
                sys.exit(1)
            count += 1
    return count


def resolve_model(cfg: dict, override: str = "") -> str:
    return override or os.getenv("TRAVELQA_BASE_MODEL", "") or cfg["base_model"]


def dry_run(cfg: dict, n: int, val_n: int, base_model: str) -> None:
    train = cfg["train"]
    print("=== DRY-RUN（未下载模型、未训练）===")
    print(f"基座模型 : {base_model}")
    print(f"训练样本 : {n} 条")
    print(f"验证样本 : {val_n} 条")
    print(
        f"LoRA     : r={cfg['lora']['r']} alpha={cfg['lora']['alpha']} "
        f"targets={cfg['lora']['target_modules']}"
    )
    print(
        f"训练设置 : epochs={train['epochs']} lr={train['learning_rate']} "
        f"4bit={train['load_in_4bit']} max_len={train['max_seq_len']}"
    )
    print(f"SwanLab  : {train.get('report_to_swanlab', True)}")
    print(f"输出目录 : {cfg['output_dir']}")
    print("真正训练 : python finetune/train_lora.py --run")


def render_prompt(example: dict) -> str:
    prompt = f"### 指令:\n{example['instruction']}\n"
    if example.get("input"):
        prompt += f"### 输入:\n{example['input']}\n"
    return prompt + "### 回答:\n"


def run(cfg: dict, data_path: Path, val_path: Path, base_model: str, run_name: str) -> None:
    try:
        import torch
        from datasets import load_dataset
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            DataCollatorForSeq2Seq,
            Trainer,
            TrainingArguments,
        )
    except ModuleNotFoundError as exc:
        print(f"[train] 缺少训练依赖: {exc.name}")
        print("[train] 请运行 autodl/train_autodl.sh 安装依赖。")
        sys.exit(1)

    train = cfg["train"]
    seed = int(train.get("seed", 20260602))
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    use_bf16 = bool(train.get("bf16", False) and torch.cuda.is_available()
                    and torch.cuda.is_bf16_supported())
    compute_dtype = torch.bfloat16 if use_bf16 else torch.float16
    use_4bit = bool(train.get("load_in_4bit", False))
    quantization_config = None
    if use_4bit:
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=True,
        )

    print(f"[train] 加载基座模型: {base_model}")
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        trust_remote_code=True,
        device_map="auto",
        dtype=compute_dtype,
        quantization_config=quantization_config,
    )
    if use_4bit:
        model = prepare_model_for_kbit_training(
            model,
            use_gradient_checkpointing=train.get("gradient_checkpointing", False),
        )
    model.config.use_cache = False
    model = get_peft_model(model, LoraConfig(
        r=cfg["lora"]["r"],
        lora_alpha=cfg["lora"]["alpha"],
        lora_dropout=cfg["lora"]["dropout"],
        target_modules=cfg["lora"]["target_modules"],
        task_type="CAUSAL_LM",
    ))
    model.print_trainable_parameters()

    max_length = int(train["max_seq_len"])

    def tokenize(example: dict) -> dict:
        prompt_ids = tokenizer(render_prompt(example), add_special_tokens=True)["input_ids"]
        answer_ids = tokenizer(
            example["output"] + tokenizer.eos_token,
            add_special_tokens=False,
        )["input_ids"]
        if len(answer_ids) >= max_length:
            answer_ids = answer_ids[:max_length - 1] + [tokenizer.eos_token_id]
            prompt_ids = []
        else:
            prompt_ids = prompt_ids[-(max_length - len(answer_ids)):]
        input_ids = prompt_ids + answer_ids
        return {
            "input_ids": input_ids,
            "attention_mask": [1] * len(input_ids),
            "labels": [-100] * len(prompt_ids) + answer_ids,
        }

    dataset = load_dataset("json", data_files=str(data_path), split="train")
    validation = load_dataset("json", data_files=str(val_path), split="train")
    dataset = dataset.map(tokenize, remove_columns=dataset.column_names)
    validation = validation.map(tokenize, remove_columns=validation.column_names)

    output_dir = str(ROOT / cfg["output_dir"])
    kwargs = {
        "output_dir": output_dir,
        "num_train_epochs": train["epochs"],
        "per_device_train_batch_size": train["per_device_batch_size"],
        "per_device_eval_batch_size": train.get("per_device_eval_batch_size", 1),
        "gradient_accumulation_steps": train["gradient_accumulation_steps"],
        "learning_rate": train["learning_rate"],
        "bf16": use_bf16,
        "fp16": not use_bf16,
        "gradient_checkpointing": train.get("gradient_checkpointing", False),
        "logging_steps": train.get("logging_steps", 5),
        "save_strategy": "epoch",
        "save_total_limit": train.get("save_total_limit", 2),
        "load_best_model_at_end": True,
        "metric_for_best_model": "eval_loss",
        "greater_is_better": False,
        "report_to": "swanlab" if train.get("report_to_swanlab", True) else "none",
        "run_name": run_name,
        "optim": train.get("optim", "paged_adamw_8bit"),
        "seed": seed,
        "data_seed": seed,
        "remove_unused_columns": False,
    }
    eval_arg = (
        "eval_strategy"
        if "eval_strategy" in inspect.signature(TrainingArguments).parameters
        else "evaluation_strategy"
    )
    kwargs[eval_arg] = "epoch"
    args = TrainingArguments(**kwargs)
    collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        padding=True,
        label_pad_token_id=-100,
        return_tensors="pt",
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=dataset,
        eval_dataset=validation,
        data_collator=collator,
    )
    metrics = trainer.train().metrics
    trainer.save_metrics("train", metrics)
    eval_metrics = trainer.evaluate()
    trainer.save_metrics("eval", eval_metrics)
    trainer.save_state()
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"[train] 完成，LoRA 适配器已保存到 {output_dir}")
    print(f"[train] 验证指标: {json.dumps(eval_metrics, ensure_ascii=False)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="真正训练，会占用 GPU")
    parser.add_argument("--base-model", default="", help="本地模型目录")
    parser.add_argument("--run-name", default=os.getenv("SWANLAB_RUN_NAME", "travelqa-qlora"))
    args = parser.parse_args()

    cfg = load_cfg()
    data_path = ROOT / cfg["dataset"]
    val_path = ROOT / cfg["validation_dataset"]
    n = check_dataset(data_path)
    val_n = check_dataset(val_path)
    base_model = resolve_model(cfg, args.base_model)
    if args.run:
        run(cfg, data_path, val_path, base_model, args.run_name)
    else:
        dry_run(cfg, n, val_n, base_model)


if __name__ == "__main__":
    main()
