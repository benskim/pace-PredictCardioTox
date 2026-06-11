# Technical Architecture: QTc Measurement Uncertainty Identification

본 문서는 QTc 신뢰도 엔진(Confidence Engine)에서 측정 불확실성의 원인(Signal Quality, Delineation Ambiguity 등)을 정량적으로 식별하기 위해 핵심 알고리즘 및 생체 신호처리(Biosignal Processing) 기법의 구현 상세를 다룹니다.

---

## 1. Signal Quality (신호 품질 평가) 기법
ECG 신호에 섞인 노이즈(근전도, 동잡음, 기선 흔들림 등)를 정량화하여 분석 가능 여부를 판단합니다.

* **SQI (Signal Quality Indices) 다중 지표 산출:**
  * **통계적 지표:** 신호의 왜도(Skewness)와 첨도(Kurtosis)를 계산합니다. 깨끗한 ECG는 특정 피크(R파) 때문에 첨도가 높지만, 백색 잡음이 섞이면 가우시안 분포에 가까워져 지표가 변합니다.
  * **주파수 도메인 지표:** 파워 스펙트럼 밀도(PSD)를 분석하여 QRS 에너지가 집중되는 5~15Hz 영역과, 노이즈(근전도 잡음)가 끼는 고주파 영역의 비율을 계산합니다.
* **Deep Learning 기반의 기선 왜곡(Baseline Wander) 및 Artifact 탐지:**
  * **1D Convolutional Autoencoder (CAE):** 깨끗한 ECG 데이터로 학습된 오토인코더에 입력 신호를 넣었을 때, 재구성 오차(Reconstruction Error)가 크다면 해당 구간에 정상적이지 않은 전극 탈락이나 강한 동잡음이 포함된 것으로 판단하여 신뢰도를 낮춤니다.

---

## 2. Beat Selection (분석 대상 맥박 선택) 기법
임상시험 중 발생하는 부정맥, 조기수축(PVC), 혹은 일시적 노이즈로 인해 왜곡된 맥박(Beat)을 걸러내고 가장 안정적인 맥박을 선별합니다.

* **Template Matching 및 Clustering (상관관계 분석):**
  * **피어슨 상관계수(Pearson Correlation):** 10초~1분 간의 전체 ECG에서 각 맥박(Beat)을 잘라낸 뒤, 평균 템플릿과의 상관계수를 구합니다. 동형성(Morphology)이 90% 이상 일치하는 '정상 맥박' 집단만 통과시키고, 혼자 튀는 맥박은 제외합니다.
* **DTW (Dynamic Time Warping):**
  * 환자의 심박수(HR)가 변하더라도 시간축을 유연하게 늘려가며 맥박 간의 유사도를 측정합니다. 이를 통해 신약 투여로 맥박 모양이 서서히 변하는 것과, 일시적 노이즈로 오염된 맥박을 정밀하게 구분합니다.

---

## 3. Delineation Ambiguity (파형 경계 모호성 해소) 기법
T파의 끝점(T-offset)을 찾을 때, 평평한 T파(Flat T)나 이중 피크(Bifid T)로 인한 모호성을 정량화합니다.

* **Continuous Wavelet Transform (CWT, 연속 웨이블릿 변환):**
  * 특정 스케일(Scale)의 웨이블릿(예: Mexican Hat)을 적용하여 신호의 변곡점과 기울기 변화를 극대화합니다. 만약 T-offset 부근에서 신호 기울기의 영점 교차(Zero-crossing)가 명확하지 않고 여러 개가 나타난다면 모호성 점수를 높게 책정합니다.
* **베이지안 딥러닝 (Bayesian Neural Networks, BNN):**
  * MC Dropout(Monte Carlo Dropout) 기법을 사용하여 T파 끝점의 위치를 확률 분포(예: 가우시안 분포)로 산출합니다. 예측치 분포의 표준편차(Variance)가 크다면 "AI 스스로도 이 위치가 모호하다고 판단"하는 것이므로, 이를 측정 불확실성(Uncertainty) 점수로 직결시킵니다.

---

## 4. Correction Methodology (심박수 보정 방법론 검증) 기법
급격한 심박수 변화가 있을 때 잘못된 보정 공식(Bazett, Fridericia 등) 사용으로 인한 오차를 방지합니다.

* **RR Interval Volatility Analysis (RR 간격 변동성 분석):**
  * QT 간격을 측정하는 시점 직전 10~30초 동안의 RR 간격 변화율(안정도)을 측정합니다. 심박수가 급격히 요동치는 구간(Hysteresis 효과 발생 구간)이라면 보정 공식 자체의 불확실성이 높다고 판단하여 감점 요인으로 반영합니다.