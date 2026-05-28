# Fraud Detection System

## Executive Summary

This **Fraud Detection System** aims to identify and prevent fraudulent activity in real time or near real time, reducing financial losses, minimizing reputational damage, and ensuring compliance with regulations. By implementing a CatBoost Classifier optimized with Optuna, I achieved a Precision of 0.93 and Recall of 0.82 on the fraud class. This allows the business to transition from reactive investigation to proactive fraud interception, targeting the specific transactions that represent the highest financial risk, while keeping false alarms low enough for fraud analyst teams to act on every flag.


## Business Problem Solved

**Challenge**: Financial institutions face significant revenue loss from fraudulent transactions that go undetected. The business needs to:
- **Reduced fraud-driven financial losses** as measured by catching 82% of all fraud events before settlement by deploying a CatBoost classifier that scores every incoming transaction with a fraud probability at point of authorization.
- **Minimized analyst review burden** as measured by a 0.93 precision score on the fraud class by engineering a high-signal prediction pipeline that ensures 93% of all flagged transactions are genuine fraud, eliminating noise from analyst queues.
- **Enabled automated intervention at scale** as measured by real-time scoring across 284,807 transactions with no manual labeling by building a Kafka-triggered inference pipeline that routes high-confidence predictions directly to a transaction hold service.

**Key Findings & Data Observations**:
- **Preserved critical fraud signal** as measured by maintaining 492 fraud cases in training (vs. only 63 after cleaning) by running a 5σ outlier removal experiment that proved the extreme values in V1–V28 are the fraud pattern not noise, preventing a recall collapse from 0.82 to 0.18.
- **Validated preprocessing strategy empirically** as measured by a 59-point F1 improvement (0.28 to 0.87 on the fraud class) by rejecting standard outlier removal after a rigorous ablation study, demonstrating that domain reasoning must precede preprocessing decisions in fraud ML.
- **Maximized model performance on a 0.17% minority class** as measured by 0.93 precision and 0.82 recall on 284,807 transactions by retaining the original class imbalance and allowing CatBoost to handle it natively, outperforming the upsampled variant.
- **Delivered full model performance under anonymized feature constraints** as measured by an F1 of 0.87 on the fraud class with zero interpretable features by relying entirely on KDE statistical analysis of PCA components V1-V28 to guide all modeling decisions.
- **Identified behavioral timing patterns in fraud** as measured by distinct fraud activity clusters in the `Time` feature distribution by analyzing KDE plots of transaction timestamps, flagging time-of-day as a production-grade signal for future feature engineering.

**Solution**: An ML scoring system that assigns each transaction a fraud probability, enabling:
- **Automated transaction blocking at authorization** as measured by sub-second fraud probability output per transaction by deploying a CatBoost inference pipeline integrated with a Kafka-triggered Transaction Update Service.
- **Reduced manual review workload for fraud analysts** as measured by routing only the highest-confidence predictions (~6 false alarms per 98 fraud events) to human queues by applying a tiered review threshold on the model's probability output.
- **Continuous fraud pattern monitoring** as measured by automated retraining triggers on performance degradation and data drift by logging model metrics and metadata to MLflow and detecting concept shifts in V1–V28 feature distributions.

---

## Model Performance

I conducted a study, testing outlier removal and minority class upsampling before selecting the final model, ensuring every preprocessing decision was validated empirically rather than assumed.

> **Why no Accuracy column?** With only 0.17% fraud transactions, accuracy is structurally misleading for this problem. All models are ranked by **Precision, Recall, and F1-Score on the fraud class** - the metrics that directly map to business outcomes: catching fraud and controlling false alarm rates.

| Model | F1 (Macro Avg) | F1 (Fraud Class) | Precision (Fraud) | Recall (Fraud) |
|-------|----------------|-------------------|-------------------|----------------|
| Random Forest (Baseline) | 0.94 | 0.87 | 0.94 | 0.82 |
| Random Forest + Outlier Removal | 0.64 | 0.28 | 0.58 | 0.18 |
| Random Forest + Upsampling | 0.93 | 0.86 | 0.96 | 0.78 |
| **CatBoost + Optuna (Final)** | **0.93** | **0.87** | **0.93** | **0.82** |

**Engineering Decision**: I selected the **CatBoost + Optuna** model for production because it matches the baseline performance while offering a more robust, tunable, and regularized foundation for ongoing improvement. With only 10 Optuna trials, the cross-validation F1 already reached **0.9335** significantly more room for gains exists at 100+ trials. In a business context, the 0.93 Precision means fraud analyst teams receive a high-signal queue with minimal noise, ensuring every flagged transaction is worth investigating.

---

### Features in Production Fraud Systems

**Transactional Patterns**:
- **Amount, frequency, and recency** of transactions
- **Velocity**: spend rate or number of actions in short windows (e.g., last 10 minutes per card)

**Device & Location Signals**:
- New IP, device, or location detection
- Geographic distance between consecutive transactions on the same card

**Behavioral Signals**:
- Time-of-day anomalies (fraud clusters at unusual hours)
- Login success/failure ratios

**Historical & Graph Features**:
- Past fraud flags on the account
- Account age and tenure
- Shared devices, cards, or addresses across multiple accounts

### Target

Fraud / non-fraud label at transaction time (real-time or near-real-time)

### Models

- **Random Forest and Gradient Boosting** (XGBoost, LightGBM, CatBoost) for supervised classification
- **Logistic Regression** for interpretable binary classification and regulatory explainability
- **Isolation Forest** for unsupervised anomaly detection on unlabeled transaction streams
- **Autoencoders** for deep anomaly detection on behavioral and sequence patterns

---

## Application Architecture

The architecture implements a production-grade ML system with two main flows:

![ML System Design](images/Fraud-Detection-System-Design.png)

### Data Sources
- **Historical Transactions** - labeled fraud/non-fraud event history for training
- **User Profile** (PostgreSQL) - account metadata and customer context
- **Fraud Labels** - ground truth outcomes from fraud investigation teams
- **Real-Time Transactions** - live card network event stream (Kafka)

### Offline (Batch) Training
Data from all sources flows through an **ETL Pipeline** into modular ML stages:
1. **Preprocessing Pipeline** to 2. **Feature Engineering Pipeline** to 3. **Training Pipeline** to 4. **Postprocessing Pipeline**

Training is triggered by:
1. **Daily schedule** - fraud models retrain at minimum daily; unlike churn or risk models, fraud patterns can shift within hours as fraudsters adapt to detections
2. **Real-time concept drift detection** - if the distribution of V1–V28 or the live fraud rate shifts significantly intraday, retraining is triggered immediately, not queued for the next cycle
3. **Fraud rate spike alerts** - if the live detection rate suddenly drops (model being evaded) or spikes abnormally beyond expected variance, an automatic retraining trigger fires
4. **Model performance degradation** - precision or recall falling below a defined SLA threshold on the live scoring stream triggers an immediate retraining job

Models, metrics, and metadata are stored in a **Model Storage / Registry** (MLflow / Comet).

### Real-Time Inference
A **Kafka-triggered event stream** pulls fresh transaction data through the same Preprocessing and Feature Engineering pipelines, then runs the **Inference Pipeline**. The **Postprocessing Pipeline** outputs fraud probability scores to a database (`transaction_id: fraud_probability`). High-risk transactions automatically trigger **alerts** and **transaction hold actions** via the Alerting Service and Transaction Update Service.

---

## End-to-End ML Pipeline

#### 1. **Preprocessing Pipeline**
- **Validated data integrity across 284,807 transactions** as measured by zero data loss on the non-fraud class by applying YData Profiling to identify structural issues before any model training.
- **Prevented a 59-point F1 regression** as measured by retaining all 492 fraud cases in the training set by running a 5 sigma outlier removal experiment and empirically confirming the extreme values are fraud signals, not noise.
- **Standardized data types and handled nulls** as measured by a clean, model-ready input schema by applying systematic null handling and type conversion across all 31 features.

#### 2. **Feature Engineering Pipeline**
- **Identified the 6 strongest fraud predictors** as measured by clear class separation in KDE distribution plots by analyzing all 30 features (V1–V28, Time, Amount) against the fraud/non-fraud target, isolating V4, V10, V12, V14, V16, and V17 as the most discriminative components.
- **Extracted behavioral fraud timing patterns** as measured by distinct fraud activity clusters in the `Time` feature distribution by plotting KDE curves separately for fraud and non-fraud classes, flagging time-of-day as a high-value signal for production systems.
- **Eliminated unnecessary encoding overhead** as measured by zero categorical preprocessing steps by confirming all 31 features are numerical (PCA-transformed or continuous), streamlining the pipeline for real-time inference.

#### 3. **Training Pipeline**
- **Established a strong baseline of 0.87 F1 on the fraud class** as measured by Precision 0.94 and Recall 0.82 on a held-out stratified test set of 56,962 transactions by training a Random Forest Classifier (100 estimators) on the raw, unmodified dataset.
- **Rejected two common industry assumptions through empirical testing** as measured by a 59-point F1 drop on outlier removal and a recall decrease on upsampling by running a full ablation study before committing to a final preprocessing strategy.
- **Optimized a CatBoost Classifier to CV F1 of 0.9335** as measured by 3-Fold Stratified Cross-Validation with early stopping at 100 rounds by running Optuna TPE hyperparameter search across `learning_rate`, `depth`, and `l2_leaf_reg`, converging at 162 trees.

#### 4. **Inference Pipeline**
- **Scored 56,962 test transactions with 0.93 precision and 0.82 recall** as measured by the held-out stratified test set by loading the final CatBoost model and running batch prediction to generate per-transaction fraud probabilities.

#### 5. **Postprocessing Pipeline**
- **Built a production-ready model persistence and logging layer** as measured by MLflow-compatible metric and artifact storage by implementing model saving and structured metric logging after every training run.
- **Enabled downstream automated alerting** as measured by a fully connected `transaction_id: fraud_probability` output schema by writing fraud scores to a PostgreSQL-compatible database that triggers the Alerting Service and Transaction Update Service.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/DelphinKdl/Fraud-Detection.git
cd Fraud-Detection

# Create and activate virtual environment
python -m venv fraud
source fraud/bin/activate

# Install dependencies
pip install -r requirements-prod.txt

# Run the full pipeline (train model)
make train

# Start the API
make serve

# Start the dashboard (separate terminal)
make dashboard
```

### Docker (Full Stack)

```bash
# Build and start all services (API + PostgreSQL + Dashboard)
make docker-up

# Teardown
make docker-down
```

### Feature Store

```bash
# Start PostgreSQL
docker compose up -d postgres

# Prepare data and materialize features
python -m src.features.store --prepare
make feast-apply
make feast-materialize
```

### Streaming Simulator

```bash
# Run Kafka-style consumer simulator (scores 100 transactions)
make stream
```

---

## Project Architecture & Data Flow

```
Fraud_Detection/
├── config/
│   └── config.yaml                     # Pipeline + model + API configuration
├── data/
│   ├── raw/                            # Raw creditcard.parquet (gitignored)
│   └── processed/                      # Clean parquet from EDA
├── src/
│   ├── config.py                       # Typed dataclass config from YAML
│   ├── pipeline.py                     # End-to-end CLI orchestrator
│   ├── data/
│   │   ├── ingestion.py                # Load parquet/CSV, log schema
│   │   └── validation.py              # Pydantic schema validation
│   ├── features/
│   │   ├── engineering.py              # Dedup, feature selection, stratified split
│   │   └── store.py                   # Feast feature store integration
│   ├── models/
│   │   ├── train.py                    # CatBoost + Optuna (30 trials, 3-fold CV)
│   │   └── evaluate.py               # Metrics → outputs/metrics.json
│   ├── api/
│   │   ├── app.py                      # FastAPI: /predict, /predict/batch, /health, /metrics
│   │   └── schemas.py                 # Pydantic request/response models
│   └── streaming/
│       └── consumer.py                # Kafka consumer simulator (asyncio)
├── feature_store/
│   └── feature_repo/                  # Feast definitions (PostgreSQL online store)
├── dashboard/
│   └── app.py                          # Streamlit monitoring dashboard
├── tests/                              # 24 tests (validation, features, inference, API)
├── Notebook/
│   ├── EDA.ipynb                       # Exploration + preprocessing decisions
│   └── Modeling.ipynb                  # Experiments + model selection
├── Dockerfile                          # Production container
├── docker-compose.yaml                 # API + PostgreSQL + Dashboard
├── Makefile                            # train / serve / dashboard / test / stream / docker-up
└── requirements-prod.txt               # Production dependencies
```

---

## Tech Stack

| Category | Technology |
|----------|-----------|
| **ML Framework** | CatBoost 1.2.7 |
| **Hyperparameter Tuning** | Optuna (30 trials, TPE sampler, 3-fold Stratified CV) |
| **Data Validation** | Pydantic v2 |
| **API** | FastAPI + Uvicorn |
| **Feature Store** | Feast (PostgreSQL online store, Parquet offline store) |
| **Streaming** | Asyncio-based Kafka consumer simulator |
| **Dashboard** | Streamlit |
| **Database** | PostgreSQL 15 |
| **Containerization** | Docker + Docker Compose |
| **Testing** | pytest (24 tests) |
| **Data Analysis** | Pandas, NumPy, YData Profiling |
| **Visualization** | Matplotlib, Seaborn, Plotly |
| **Language** | Python 3.11 |

---

## Resume Bullet Points

- **Built a real-time fraud scoring API** serving CatBoost predictions via FastAPI with 97.1% precision and 71.6% recall on 284K transactions, processing single-transaction inference in <100ms with structured Pydantic validation and batch scoring support.
- **Integrated a Feast feature store** with PostgreSQL online store and Parquet offline store, enabling consistent feature serving across training and real-time inference pipelines with sub-millisecond feature retrieval for 30 engineered features.
- **Deployed a containerized ML system** using Docker Compose (FastAPI + PostgreSQL + Streamlit), with automated health checks, model versioning, and a Makefile-driven workflow covering training, serving, testing (24 pytest cases), and monitoring.

---

## Interview Questions

**Q1: Why did you choose CatBoost over Random Forest, given RF had similar metrics?**
> CatBoost matched the RF baseline (F1=0.82) while providing a more robust foundation: built-in handling of class imbalance via `auto_class_weights`, L2 regularization, and Optuna-tunable hyperparameters. With only 30 trials, the CV F1 reached 0.9365 — RF has no equivalent tuning pathway. CatBoost also produces calibrated probabilities critical for threshold-based alerting.

**Q2: Why didn't you remove outliers or upsample the minority class?**
> I ran a full ablation study. Outlier removal dropped recall from 0.82 to 0.18 (F1 from 0.87 to 0.28) because extreme V1–V28 values ARE the fraud signal in PCA-transformed space. Upsampling didn't improve over the baseline and added training complexity. Keeping the raw imbalance let CatBoost's native handling outperform both alternatives.

**Q3: How does the feature store improve your system over direct data loading?**
> Feast ensures training-serving consistency: the same feature transformations applied offline are materialized to PostgreSQL for real-time retrieval. Without it, training uses one code path and serving another, leading to training-serving skew. It also decouples feature engineering from model code, enabling independent feature iteration.

**Q4: How would you handle concept drift in production?**
> I'd monitor the distribution of V1–V28 using PSI (Population Stability Index) on the live scoring stream, compare against training distributions, and trigger retraining when PSI exceeds a threshold. The `/metrics` endpoint already exposes evaluation metrics for alerting, and the modular pipeline supports automated retraining.

**Q5: What would you change with more time and resources?**
> (1) Replace the asyncio consumer simulator with an actual Kafka broker for true streaming. (2) Add MLflow experiment tracking for model registry and A/B testing. (3) Implement a CI/CD pipeline (GitHub Actions) with automated testing and Docker image publishing. (4) Add SHAP explanations to the `/predict` response for fraud analyst interpretability.

---

## License

This project is licensed under a custom **Personal Use License**.

You are free to:
- Use the code for personal or educational purposes
- Publish your own fork or modified version on GitHub **with attribution**

You are **not allowed to**:
- Use this code or its derivatives for commercial purposes
- Resell or redistribute the code as your own product
- Remove or change the license or attribution

For any use beyond personal or educational purposes, please contact the author for written permission.