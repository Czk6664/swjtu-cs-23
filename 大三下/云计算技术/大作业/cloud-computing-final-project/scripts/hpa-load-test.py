import argparse
import concurrent.futures
import time
from urllib.request import urlopen


def hit(url: str, timeout: float) -> tuple[bool, float]:
    start = time.perf_counter()
    try:
        with urlopen(url, timeout=timeout) as response:
            response.read()
            return 200 <= response.status < 500, time.perf_counter() - start
    except Exception:
        return False, time.perf_counter() - start


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple concurrent HTTP load generator for HPA verification.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--requests", type=int, default=10000)
    parser.add_argument("--concurrency", type=int, default=200)
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()

    start = time.perf_counter()
    ok = 0
    total_latency = 0.0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(hit, args.url, args.timeout) for _ in range(args.requests)]
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            success, latency = future.result()
            ok += int(success)
            total_latency += latency
            if i % 500 == 0:
                print(f"completed={i} success={ok}")

    elapsed = time.perf_counter() - start
    print(f"requests={args.requests}")
    print(f"success={ok}")
    print(f"elapsed_seconds={elapsed:.2f}")
    print(f"requests_per_second={args.requests / elapsed:.2f}")
    print(f"avg_latency_seconds={total_latency / args.requests:.4f}")


if __name__ == "__main__":
    main()
