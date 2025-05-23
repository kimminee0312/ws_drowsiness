#!/usr/bin/env python3
"""
ear_logger_node.py 사용해서 raw, kal ear 값 저장 한거 
표준편차랑 변화량 같은거 자동 계산해서 터미널에 출력해주는 스크립트 
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate


def analyze_ear_csv(csv_path):
    df = pd.read_csv(csv_path)

    # 표준편차 및 변화량 계산
    std_raw = np.std(df['ear_raw'])
    std_kalman = np.std(df['ear_kalman'])
    tv_raw = np.sum(np.abs(np.diff(df['ear_raw'])))
    tv_kalman = np.sum(np.abs(np.diff(df['ear_kalman'])))
    mad = np.mean(np.abs(df['ear_raw'] - df['ear_kalman']))

    # 표 출력
    table = [
        ["표준편차 (Standard Deviation)", f"{std_raw:.5f}", f"{std_kalman:.5f}"],
        ["총 변화량 (Total Variation)", f"{tv_raw:.5f}", f"{tv_kalman:.5f}"],
        ["평균 차이 (Mean Abs Diff)", f"{mad:.5f}", "-"]
    ]


    headers = ["지표", "Raw", "Kalman"]
    print("\n===== EAR 수치 비교 결과 =====")
    print(tabulate(table, headers=headers, tablefmt="grid"))
    print("================================\n")

    # 그래프 시각화
    plt.figure(figsize=(12, 5))
    plt.plot(df['frame'].values, df['ear_raw'].values, label='EAR Raw', alpha=0.6)
    plt.plot(df['frame'].values, df['ear_kalman'].values, label='EAR Kalman', linewidth=2)
    plt.title("EAR 값 비교 (Raw vs Kalman Filter)")
    plt.xlabel("Frame")
    plt.ylabel("EAR")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("사용법: python3 analyze_ear_log.py <csv 파일 경로>")
    else:
        analyze_ear_csv(sys.argv[1])
