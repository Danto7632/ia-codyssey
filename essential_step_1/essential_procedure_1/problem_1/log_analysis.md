# 미션 컴퓨터 로그 분석 보고서

## 1. 개요

- 파일명: `mission_computer_main.log`
- 총 로그 줄 수: 36줄
- 문제 의심 로그 수: 3줄

## 2. 분석 방법

- 전체 로그를 UTF-8 인코딩으로 읽어 화면에 출력하였다.
- 로그를 시간 역순으로 재정렬하여 별도 파일에 저장하였다.
- 미리 정의한 키워드를 기준으로 이상 징후가 의심되는 로그를 1차 추출하였다.
- 각 의심 로그에 대해 원본 파일의 행 번호를 함께 기록하여, 해당 위치의 전후 문맥을 직접 다시 확인할 수 있도록 하였다.
- 최종 원인 추정은 키워드 빈도만으로 단정하지 않고, 문제 의심 로그의 전후 문맥을 함께 검토하는 방식으로 수행하였다.

## 3. 주요 키워드 집계

- `oxygen` : 2회
- `pressure` : 1회
- `explosion` : 1회

## 4. 사고 원인 추정

로그 키워드 기준으로는 압력 또는 산소 계통 이상 가능성이 가장 먼저 의심된다. 다만 최종 결론은 해당 구간의 원문 로그와 전후 문맥을 함께 확인해야 한다.

## 5. 문제 의심 로그와 원본 위치

### 의심 로그 1

- 원본 행 번호: 16
- 검출 키워드: pressure
- 원본 로그: `2023-08-27 10:35:00,INFO,Approaching max-Q. Aerodynamic pressure increasing.`

- 주변 문맥

```text
  line 15: 2023-08-27 10:32:00,INFO,Initial telemetry received. Rocket is on its trajectory.
* line 16: 2023-08-27 10:35:00,INFO,Approaching max-Q. Aerodynamic pressure increasing.
  line 17: 2023-08-27 10:37:00,INFO,Max-Q passed. Vehicle is stable.
```

### 의심 로그 2

- 원본 행 번호: 34
- 검출 키워드: oxygen
- 원본 로그: `2023-08-27 11:35:00,INFO,Oxygen tank unstable.`

- 주변 문맥

```text
  line 33: 2023-08-27 11:30:00,INFO,Mission completed successfully. Recovery team dispatched.
* line 34: 2023-08-27 11:35:00,INFO,Oxygen tank unstable.
  line 35: 2023-08-27 11:40:00,INFO,Oxygen tank explosion.
```

### 의심 로그 3

- 원본 행 번호: 35
- 검출 키워드: explosion, oxygen
- 원본 로그: `2023-08-27 11:40:00,INFO,Oxygen tank explosion.`

- 주변 문맥

```text
  line 34: 2023-08-27 11:35:00,INFO,Oxygen tank unstable.
* line 35: 2023-08-27 11:40:00,INFO,Oxygen tank explosion.
  line 36: 2023-08-27 12:00:00,INFO,Center and mission control systems powered down.
```

## 6. 1차 분석 결과

로그 내에서 이상 징후로 해석될 수 있는 항목들을 1차적으로 추출하였다. 각 항목에 대해 원본 파일의 행 번호와 주변 문맥을 함께 제시하였으며, 이를 바탕으로 이후 최종 결론을 도출할 수 있도록 정리하였다.

## 7. 결론

의심로그1에서 max-Q에 가까워져 압력이 상승했지만, 바로 다음행에 max-Q가 통과되고, 안정적으로 변했다는것을 확인했습니다. 이후 의심로그2에서 1차적으로 Oxygen tank가 불안정한 상태임을 확인할 수 있었고, 바로 다음 의심로그3에서 Oxygen tank가 폭발했다는 사실을 발견할 수 있었습니다. 따라서 화성기지가 폭발한 원인은 산소탱크에 있었음을 알 수 있습니다.