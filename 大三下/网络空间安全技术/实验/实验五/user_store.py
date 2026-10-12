from copy import deepcopy

from common import b64e, normalize_user_id


def add_user_record(record: dict, db: dict) -> None:
    """添加用户记录。"""
    db[normalize_user_id(record["id"])] = record


def get_user_record(user_id: str, db: dict) -> dict | None:
    """读取用户记录。"""
    return db.get(normalize_user_id(user_id))


def update_user_counter(user_id: str, new_counter: int, db: dict) -> None:
    """更新 OTP 计数器。"""
    record = get_user_record(user_id, db)
    if record is not None:
        record["counter"] = new_counter


def mark_nonce_used(user_id: str, nonce: bytes, db: dict, bucket: str = "issued_nonces") -> None:
    """标记 challenge/MAC/签名 nonce 已消费。"""
    record = get_user_record(user_id, db)
    if record is not None:
        key = b64e(nonce)
        record.setdefault(bucket, {})[key] = {
            **record.setdefault(bucket, {}).get(key, {}),
            "consumed": True,
        }


def clone_db(db: dict) -> dict:
    """为测试用例复制服务端状态，避免互相污染。"""
    return deepcopy(db)

