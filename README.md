# Drowsy Detection System (ROS 2 Workspace)

> 전공 학점 인정 프로젝트 (2025.01 – 2025.06) · 프로젝트 팀장 (2인 팀)

카메라 영상에서 **EAR(Eye Aspect Ratio) 기반**으로 운전자 졸음을 실시간 감지하는 ROS 2 기반 인식 시스템입니다. iOS 앱과는 Firebase Firestore + FastAPI를 통해 4계층으로 통합됩니다.

---

## 프로젝트 목적

- 운전자 졸음 사고를 줄이기 위한 **실시간 감지 시스템** 구현
- **4계층 환경 통합**: Firebase Firestore ↔ FastAPI ↔ ROS 2 ↔ iOS
- 사용자 맞춤 **동적 캘리브레이션 + 이중 임계값** 기반 정확한 졸음 판단

---

## 사용 기술 스택

| 영역 | 기술 |
|---|---|
| **언어** | Python (99.6%) |
| **프레임워크** | ROS 2 Humble |
| **컴퓨터 비전** | OpenCV, MediaPipe (얼굴 랜드마크 추출) |
| **알고리즘** | EAR (Eye Aspect Ratio) + 동적 캘리브레이션 |
| **통신** | HTTP REST API (FastAPI), Firebase Firestore |
| **운영체제** | Ubuntu 22.04 |

---

## 시스템 통신 흐름

```
[iOS App] ⇄ [Firebase Firestore]
              ↑
              │ (실시간 상태/세션 저장)
              │
[FastAPI Server] ← HTTP POST ← [iOS App]
        │ (rclpy Service Client)
        ↓
[ROS 2 System]
   └── Drowsy Detector → Status Publisher → Firebase Bridge
```

**핵심 통신 흐름**:
- `iOS → FastAPI`: `/start_drowsiness`, `/end_drowsiness` (HTTP POST)
- `FastAPI → ROS 2`: rclpy 기반 Service Client
- `ROS 2 → Firebase`: `/users/{uid}/CurrentStatus` (실시간), `/users/{uid}/DrowsyData/{date}/{session}` (세션 저장)
<img width="1112" height="723" alt="image" src="https://github.com/user-attachments/assets/f29edcd3-b3fe-4c91-8f69-a1b3607a4c74" />

