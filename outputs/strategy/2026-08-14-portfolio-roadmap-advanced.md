# Portfolio Roadmap — Advanced Engineering Projects (No API Fees)
**Date:** 2026-08-14
**Status:** reference
**Note:** These are the "top engineer" signal projects. Pure algorithms, custom models, statistical depth.
Zero external API costs — uses open source models, free compute (Colab/Kaggle), free public datasets.

---

## MACHINE LEARNING / STATISTICAL

### Fraud Detection Engine
Custom anomaly detection + graph-based fraud ring detection.
Algorithms: Isolation Forest, XGBoost, behavioral baselines, transaction graph (NetworkX).
Real-time scoring under 50ms. Production REST API.
Dataset: IEEE-CIS Fraud Detection (Kaggle, free).
Who pays: Fintech, payment processors, e-commerce. $50K-$200K.
Signal: Every bank and payment company needs this.

### Demand Forecasting System
Ensemble model: Prophet + custom LSTM + XGBoost on public retail data.
Multi-granularity (daily, weekly, SKU-level, store-level).
Uncertainty quantification with confidence intervals.
Dataset: M5 Forecasting Competition (Kaggle, free).
Who pays: Retail, supply chain, manufacturing, logistics. $30K-$100K.

### Predictive Maintenance Engine
IoT sensor data + survival analysis (Kaplan-Meier, Cox Proportional Hazards) + LSTM for failure sequence prediction.
Detects machine failure before it happens. Visualized on a dashboard.
Dataset: NASA CMAPSS turbofan degradation dataset (free).
Who pays: Manufacturing, oil and gas, aviation. Massive enterprise market.

### Bayesian A/B Testing Framework
Not just "run an experiment." Proper Bayesian vs. Frequentist testing framework.
Features: sequential testing, multiple comparison correction, power analysis, decision rules, visualization.
Built as Python library + web dashboard.
Dataset: Self-generated simulation data.
Who pays: Product teams, marketing orgs, growth teams at any scale.

### Causal Inference Engine
Difference-in-differences, instrumental variables, propensity score matching, synthetic control.
Measures the real effect of business decisions, not just correlation.
Dataset: Lalonde (Job Training, public), or simulated panel data.
Who pays: Marketing mix modeling, policy evaluation, growth analytics. Frontier applied stats.

---

## COMPUTER VISION (CUSTOM TRAINED, NO API)

### Document Intelligence Model
Fine-tune LayoutLM or ViT on DocVQA/FUNSD datasets. Extracts structured data from invoices, contracts, forms.
No OCR API, no Google Vision. Your own trained model hosted on HuggingFace Spaces.
Dataset: DocVQA, FUNSD, RVL-CDIP (all free, HuggingFace).
Who pays: Legal, finance, insurance, healthcare. $30K-$100K+.

### Real-Time Object Detection Pipeline
Fine-tune YOLOv9 or RT-DETR on a specific domain (construction safety, shelf monitoring, defect detection).
Custom dataset (label with Label Studio, free), production inference API with FastAPI.
Who pays: Manufacturing QC, construction safety, retail analytics.

---

## NLP (FINE-TUNED MODELS, NOT WRAPPERS)

### Domain-Specific LLM Fine-Tuning
Fine-tune Mistral-7B or LLaMA-3 on legal, medical, or financial domain data.
Method: LoRA/QLoRA (runs on free Colab GPU). Deployed on HuggingFace Spaces (free).
Dataset: Free Pile subsets, PubMed, SEC filings (all public).
Who pays: Legal tech, medtech, fintech. Not ChatGPT. A specialized domain model.

### Named Entity Recognition System
Custom NER model (fine-tuned BERT or spaCy transformer) for domain-specific entities.
Examples: medical conditions + medications, legal clause types, financial instruments.
Dataset: MIMIC-III (medical, free for researchers), LEDGAR (legal, free), FiNER (financial, free).
Who pays: Healthcare data, legal research platforms, compliance teams.

---

## OPTIMIZATION / ALGORITHMS

### Constraint Satisfaction Solver
Vehicle routing (TSP variants), employee shift scheduling, portfolio allocation.
Methods: Genetic algorithms, simulated annealing, linear programming (PuLP/OR-Tools).
Benchmarked against naive approaches. Shows your math works.
Who pays: Logistics, workforce management, operations research. $40K-$150K.

### Graph Analytics Platform
Social network analysis, fraud ring detection, supply chain optimization.
Algorithms: PageRank, community detection (Louvain), centrality measures, max-flow.
Custom implementations (not just NetworkX calls). Large-graph performance benchmarks.
Dataset: SNAP social networks, OpenStreetMap (both free).
Who pays: Fintech fraud teams, telcos, supply chain consultants.

### Custom Search and Ranking Engine
Inverted index from scratch, BM25 scoring, query optimization, learning-to-rank.
Benchmarked on BEIR or MS MARCO public datasets.
Shows information retrieval depth — this is Google-level problem solving at smaller scale.
Who pays: Any company with a search problem. Medical literature, legal case law, product catalogs.

---

## QUANTITATIVE FINANCE

### Portfolio Optimization Engine
Mean-variance optimization (Markowitz), Black-Litterman model, Fama-French factor models.
Monte Carlo simulation, CVaR (Conditional Value at Risk), backtesting framework.
Dataset: Yahoo Finance (free via yfinance).
Who pays: Wealth management, fintech, family offices. Extremely well paid.

### Options Pricing and Risk Model
Black-Scholes, binomial trees, Monte Carlo for exotic options.
Greeks calculation, volatility surface construction, P&L attribution.
Dataset: CBOE historical options data (free subset available).
Who pays: Trading desks, quant funds, derivatives platforms. $100K-$500K projects.

---

## SYSTEMS / ARCHITECTURE

### Real-Time Anomaly Detection Platform
Streaming ingestion (Kafka or NATS) + multiple simultaneous detectors:
ARIMA-based, LSTM-based, statistical process control (CUSUM, EWMA).
Alerting system. Benchmarked on public SMAP/MSL datasets.
Who pays: Cybersecurity, infrastructure monitoring, financial surveillance. $50K-$200K.

### Time Series Database Engine
Simplified TimescaleDB-style system. Custom storage format optimized for temporal data.
Specialized query language subset, compression. Shows systems programming depth.
Who pays: IoT platforms, trading systems, any high-frequency data pipeline.

---

## Free Compute and Data Resources

Free GPU compute:
- Google Colab (T4, free tier)
- Kaggle Notebooks (P100, free tier, 30hr/week)
- Vast.ai (cheap spot GPU rental, ~$0.20/hr for RTX 3090)

Free datasets:
- Kaggle Datasets (hundreds of ML-ready datasets)
- HuggingFace Datasets (NLP, vision, everything)
- UCI ML Repository (classic ML benchmarks)
- Papers With Code (dataset + benchmark links for every domain)

Free model hosting:
- HuggingFace Spaces (Gradio or Streamlit, free)
- Railway (FastAPI, free tier)
- Render (free tier for API hosting)

---

## Priority Order for Emmanuel Specifically

Given his n8n + Python + AI automation positioning:

1. Fraud Detection Engine (highest enterprise ROI signal)
2. Demand Forecasting System (direct supply chain / retail market)
3. Domain-Specific LLM Fine-Tuning (separates API-users from engineers)
4. Document Intelligence Model (legal + medical = highest rates)
5. Portfolio Optimization Engine (finance = highest pay per hour)

---
