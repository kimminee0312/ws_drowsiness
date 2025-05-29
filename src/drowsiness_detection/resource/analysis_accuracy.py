"""
정답 csv 파일과 예측 csv 파일 비교 및 정확도 분석 스크립트 
"""

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import argparse
from sklearn.metrics import classification_report
import os

# 베이스 경로를 코드 상단에 지정
BASE_PATH = "/home/kml/workspace/ws_drowsiness/performance_evaluation"

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ground_truth", required=True)
    parser.add_argument("--prediction", required=True)
    return parser.parse_args()

# 상태별 허용 오차 (초 단위)
TOLERANCES = {
    "closed": 2.0,
    "opened": 1.3,
    "yawn": 4.0
}

def normalize_status(s):
    s = s.strip().lower()
    if s in ["open", "opened"]:
        return "opened"
    elif s in ["close", "closed"]:
        return "closed"
    elif "yawn" in s:
        return "yawn"
    return s

# 시간 파싱 함수 (초단위 통일 가정)
def parse_time(t):
    if isinstance(t, (float, int, np.float64)):
        return datetime.fromtimestamp(t)
    if isinstance(t, str):
        return datetime.fromtimestamp(float(t))
    return t

def match_both_ways(gt_df, pred_df):
    gt_df["timestamp"] = gt_df["timestamp"].apply(parse_time)
    pred_df["timestamp"] = pred_df["timestamp"].apply(parse_time)
    gt_df["status"] = gt_df["status"].apply(normalize_status)
    pred_df["status"] = pred_df["status"].apply(normalize_status)

    matched_records = []

    # 예측 기준 → 정답 매칭 (뒤에서 정답-예측 순으로 바꿔줌)
    for _, pred in pred_df.iterrows():
        pred_time = pred["timestamp"]
        pred_status = pred["status"]
        tolerance = timedelta(seconds=TOLERANCES.get(pred_status, 2.0))
        diff = abs(gt_df["timestamp"] - pred_time)
        in_window = gt_df[(diff <= tolerance) & (gt_df["status"] == pred_status)]
        if not in_window.empty:
            closest_idx = diff[in_window.index].idxmin()
            gt_time = gt_df.loc[closest_idx, "timestamp"]
            time_gap = (pred_time - gt_time).total_seconds()
            matched_records.append((gt_time, pred_status, pred_status, time_gap, False))  # from_gt=False
        else:
            matched_records.append((pred_time, "none", pred_status, None, False))

    # 정답 기준 → 예측 매칭
    for _, gt in gt_df.iterrows():
        gt_time = gt["timestamp"]
        gt_status = gt["status"]
        tolerance = timedelta(seconds=TOLERANCES.get(gt_status, 2.0))
        diff = abs(pred_df["timestamp"] - gt_time)
        in_window = pred_df[(diff <= tolerance) & (pred_df["status"] == gt_status)]
        if not in_window.empty:
            closest_idx = diff[in_window.index].idxmin()
            pred_time = pred_df.loc[closest_idx, "timestamp"]
            time_gap = (pred_time - gt_time).total_seconds()
            matched_records.append((gt_time, gt_status, gt_status, time_gap, True))  # from_gt=True
        else:
            matched_records.append((gt_time, gt_status, "none", None, True))

    return pd.DataFrame(matched_records, columns=["timestamp", "true_status", "pred_status", "time_gap", "from_gt"])

def main():
    args = parse_args()
    gt_path = os.path.join(BASE_PATH, args.ground_truth)
    pred_path = os.path.join(BASE_PATH, args.prediction)
    result_dir = os.path.dirname(pred_path)

    # CSV 불러오기
    gt_df = pd.read_csv(gt_path)
    pred_df = pd.read_csv(pred_path)

    # 양방향 매칭 수행
    result_df = match_both_ways(gt_df, pred_df)

    # 중복 제거: 예측 기준 기반으로 정답=예측인 경우 제거
    pred_based = result_df[(result_df["from_gt"] == False) & (result_df["true_status"] == result_df["pred_status"])]
    gt_based = result_df[(result_df["from_gt"] == True)]

    duplicate_keys = set(zip(gt_based["timestamp"], gt_based["true_status"]))
    before_dedup_count = len(pred_based)
    filtered_pred_based = pred_based[~pred_based.set_index(["timestamp", "true_status"]).index.isin(duplicate_keys)]
    after_dedup_count = len(filtered_pred_based)
    removed_duplicates = before_dedup_count - after_dedup_count
    print(f"\n🧹 중복 제거된 항목 수: {removed_duplicates}")

    # 합치기
    result_df = pd.concat([gt_based, filtered_pred_based], ignore_index=True)

    # 평가 제외: opened=none 또는 none=opened
    exclude_mask = (
        ((result_df["true_status"] == "opened") & (result_df["pred_status"] == "none")) |
        ((result_df["true_status"] == "none") & (result_df["pred_status"] == "opened")) |
        ((result_df["true_status"] == "none") & (result_df["pred_status"] == "none") & (result_df["from_gt"] == "False")) # 
    )

    # 상태 플래그 설정
    result_df["status_flag"] = np.where(exclude_mask, "-", "active")

    # 정확도 계산용 필터: 상태 플래그가 active 인 것만 사용
    eval_df = result_df[result_df["status_flag"] == "active"]

    print("\n=== 정답 비교 결과 (status_flag=active 항목만 평가) ===")
    print(classification_report(eval_df["true_status"], eval_df["pred_status"], zero_division=0))

    # 수동 TP, FP, FN 계산
    TP = ((eval_df["true_status"] == eval_df["pred_status"]) & (eval_df["true_status"] != "none")).sum()
    FP = ((eval_df["true_status"] == "none") & (eval_df["pred_status"] != "none")).sum()
    FN = ((eval_df["true_status"] != "none") & (eval_df["pred_status"] == "none")).sum()

    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print("\n=== 수동 계산 ===")
    print(f"TP: {TP}, FP: {FP}, FN: {FN}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1 Score: {f1_score:.4f}")

    result_file = os.path.join(result_dir, "comparison_result.csv")
    result_df.to_csv(result_file, index=False)
    print(f"\n 결과 저장 완료: {result_file}")

if __name__ == "__main__":
    main()