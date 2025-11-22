Short summary — here's a compact, battle-tested list of cloud-native projects and products you can use **today** to run GPU-accelerated AI training and inference at production scale, plus a few production stack combinations tuned to common real-world needs.

# Production-ready cloud-native projects & products (GPU + AI)

| Project / Product                                   |                                                       Category | Production maturity / notes                                                                          | Why it’s battle-tested for GPU/AI                                                                                                                                                |
| --------------------------------------------------- | -------------------------------------------------------------: | ---------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Kubeflow (Trainer, Katib, MPIJob, Pipelines)**    |                              End-to-end ML platform / training | CNCF incubating; widely used in large orgs; installs via manifests / distributions. ([CNCF][1])      | Full Kubernetes-native training stack (MPI/Distributed jobs, hyperparameter tuning, pipelines). Good for orchestrating multi-node GPU training. ([Kubeflow][2])                  |
| **KServe**                                          |                                      Model inference / serving | Recently adopted into CNCF (incubating); focused on GenAI + predictive serving. ([CNCF][3])          | Standardized, Kubernetes-native model serving with explicit GPU optimizations and multi-framework support (LLMs, batching, autoscaling). ([KServe][4])                           |
| **Seldon Core**                                     |                                          Model serving / MLOps | Widely used in production; enterprise adopters; active releases. ([GitHub][5])                       | Kubernetes-native model serving with A/B, canary, monitoring hooks — integrates with GPU nodes for high-throughput inference. ([GitHub][5])                                      |
| **NVIDIA GPU Operator**                             | GPU lifecycle operator (drivers, device-plugin, toolkit, DCGM) | De-facto production operator for NVIDIA GPUs on K8s; well-maintained GitHub project. ([GitHub][6])   | Automates driver install, device plugin, container runtime and monitoring (DCGM) so GPUs are cluster-first-class resources. Essential for production GPU clusters. ([GitHub][6]) |
| **k8s-device-plugin (NVIDIA)**                      |                                       Kubernetes device plugin | Official community repo; device plugin framework is stable in K8s. ([GitHub][7])                     | Exposes `nvidia.com/gpu` resources to kubelet and scheduler; base primitive used by operators and schedulers. ([GitHub][7])                                                      |
| **NVIDIA Triton Inference Server**                  |                              High-performance inference engine | Production-grade, widely deployed (NGC containers + docs). ([NVIDIA Docs][8])                        | Optimized for NVIDIA GPUs: batching, multi-model, multi-framework support — used as the inference engine behind many production services. ([NVIDIA Docs][9])                     |
| **Ray + KubeRay (Ray Serve)**                       |                        Distributed compute, training & serving | Ray is production-used at scale; KubeRay operator integrates with Kubernetes. ([Ray][10])            | Great for actor-style scaling, multi-node LLM serving, autoscaling, and running elastic training workloads on GPU nodes. ([Ray][11])                                             |
| **Volcano**                                         |                              Batch / HPC scheduler (GPU aware) | CNCF project built for batch/HPC/AI scheduling; used in production at large clusters. ([GitHub][12]) | Advanced queueing, gang/group scheduling, topology-aware scheduling for efficient multi-GPU distributed training. ([volcano.sh][13])                                             |
| **DeepSpeed / Horovod / MPI (training frameworks)** |                                Distributed training frameworks | Battle-tested in large LLM training jobs (DeepSpeed, Horovod widely used). ([DeepSpeed][14])         | Provide optimized allreduce, pipeline/tensor parallelism, and scale-out primitives used by production LLM training pipelines. ([DeepSpeed][14])                                  |
| **NVIDIA DCGM Exporter (Prometheus)**               |                                     GPU telemetry / monitoring | Standard exporter for GPU telemetry (Prometheus integration, helm charts). ([GitHub][15])            | Exposes GPU-level metrics (util, mem, temp, ECC) for SRE/ML observability — essential in production to avoid silent GPU exhaustion. ([NVIDIA Docs][16])                          |
| **Argo Workflows / Kubeflow Pipelines / Tekton**    |                                          Pipelines & CI for ML | Production-used for orchestrating training/eval pipelines on K8s. ([Kubeflow][17])                   | Useful to build reproducible training workflows, data prep, and model CI/CD that schedule GPU jobs reliably. ([Kubeflow][17])                                                    |
| **Triton / BentoML / llm-d (serving alternatives)** |                                     Specialized serving stacks | Triton (NVIDIA) for GPU-centric inference; BentoML / llm-d for Pythonic LLM serving. ([GitHub][18])  | Choose per workload: Triton for raw GPU throughput; Ray Serve / KServe / Seldon for scale + routing + model lifecycle. ([NVIDIA Docs][9])                                        |

*Notes:* each row links to community / vendor docs (citations above). These projects are **used in production** by major cloud vendors and enterprises; many companies combine these pieces rather than relying on a single monolith.

# Common production stacks (battle-tested combos)

Each stack below is a pragmatic, real-world combination — pick one based on objective (LLM training, inference scale, research velocity).

1. **Large-scale LLM training (on-prem / bare metal / hybrid)**

   * Kubernetes + NVIDIA GPU Operator + Volcano (or dedicated scheduler)
   * Kubeflow Trainer / MPIJob or KubeRay + DeepSpeed / Horovod for distributed training
   * DCGM exporter → Prometheus + Grafana for GPU telemetry
   * Model artifacts to object store (S3) and Git for code + MLflow/registry
   * Why: deterministic node management, topology-aware scheduling, production monitoring. ([GitHub][6])

2. **Low-latency LLM / multimodal inference (public cloud / hybrid)**

   * Kubernetes (GKE/EKS/AKS) + NVIDIA GPU Operator + Triton or KServe backed by Triton
   * Horizontal autoscaling via KNative or Ray Serve for scale-to-zero and request autoscaling
   * Model-level routing with KServe / Seldon for A/B, canary, and multi-model pipelines
   * Why: Triton gives GPU throughput and model interop; KServe/Seldon add lifecycle + K8s integration. ([NVIDIA Docs][8])

3. **Interactive research & rapid iteration**

   * K8s dev cluster + KubeRay / Ray (for notebooks + serve) + small Kubeflow Pipelines / Argo for reproducible runs
   * Use GPU Operator or lightweight device-plugin for node provisioning; leverage Ray for quick scale-up. ([Ray][10])

4. **Batch HPC / mixed workloads (genomics, training, data prep)**

   * Kubernetes + Volcano (batch scheduler) + MPIJob / Kubeflow trainer + DCGM monitoring
   * Why: Volcano’s gang scheduling and queue management improve GPU utilization for bursty large jobs. ([GitHub][12])

# Quick practical advice (battle-tested rules)

* **Start with the GPU operator + device plugin** — without drivers/DCGM correctly installed you’ll fight flaky GPU nodes. (NVIDIA GPU Operator + k8s device plugin). ([GitHub][6])
* **Use a scheduler built for gang / multi-pod jobs** (Volcano, Kueue, YuniKorn) for distributed training to avoid partial allocations. ([volcano.sh][13])
* **Separate concerns:** use one tool for driver/node lifecycle (GPU Operator), one for job orchestration (Kubeflow/Ray/Volcano), and one for serving (Triton/KServe/Seldon).
* **Monitoring first:** DCGM → Prometheus is table stakes for production GPU fleets. ([NVIDIA Docs][16])

# Short recommended next steps (concrete)

1. Deploy a small Kubernetes cluster with NVIDIA GPU Operator and dcgm-exporter; verify `nvidia.com/gpu` is available to pods. ([GitHub][6])
2. Run a 1-node distributed training example (Kubeflow MPIJob or Ray on K8s) to validate networking/topology and GPU wiring. ([Kubeflow][19])
3. Try serving the trained model with Triton behind KServe (or Ray Serve) and measure tail latency / GPU utilization. ([NVIDIA Docs][8])

---

If you want, I can: (A) produce a one-page deployment checklist (helm commands + CR manifests) to install **NVIDIA GPU Operator → DCGM exporter → Kubeflow Trainer → Triton/KServe** in a test cluster, or (B) give a compact decision matrix that maps your expected scale (8–64–512 GPUs), latency requirements, and team skills to the specific stack above. Which would be more useful right now?

[1]: https://www.cncf.io/projects/kubeflow/?utm_source=chatgpt.com "Kubeflow | CNCF"
[2]: https://www.kubeflow.org/?utm_source=chatgpt.com "Kubeflow"
[3]: https://www.cncf.io/projects/kserve/?utm_source=chatgpt.com "KServe | CNCF"
[4]: https://kserve.github.io/website/?utm_source=chatgpt.com "KServe"
[5]: https://github.com/SeldonIO/seldon-core?utm_source=chatgpt.com "SeldonIO/seldon-core: An MLOps framework to package ..."
[6]: https://github.com/NVIDIA/gpu-operator?utm_source=chatgpt.com "NVIDIA/gpu-operator"
[7]: https://github.com/NVIDIA/k8s-device-plugin?utm_source=chatgpt.com "NVIDIA device plugin for Kubernetes"
[8]: https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/index.html?utm_source=chatgpt.com "NVIDIA Triton Inference Server"
[9]: https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/architecture.html?utm_source=chatgpt.com "Triton Architecture — NVIDIA Triton Inference Server"
[10]: https://docs.ray.io/en/latest/cluster/kubernetes/index.html?utm_source=chatgpt.com "Ray on Kubernetes — Ray 2.51.1 - Ray Docs"
[11]: https://docs.ray.io/en/latest/cluster/kubernetes/user-guides/gpu.html?utm_source=chatgpt.com "Using GPUs — Ray 2.51.1 - Ray Docs"
[12]: https://github.com/volcano-sh/volcano?utm_source=chatgpt.com "volcano-sh/volcano: A Cloud Native Batch System (Project ..."
[13]: https://volcano.sh/en/?utm_source=chatgpt.com "Volcano"
[14]: https://www.deepspeed.ai/getting-started/?utm_source=chatgpt.com "Getting Started - DeepSpeed"
[15]: https://github.com/NVIDIA/dcgm-exporter?utm_source=chatgpt.com "NVIDIA/dcgm-exporter: NVIDIA GPU metrics exporter for ..."
[16]: https://docs.nvidia.com/datacenter/dcgm/latest/gpu-telemetry/dcgm-exporter.html?utm_source=chatgpt.com "DCGM-Exporter"
[17]: https://www.kubeflow.org/docs/started/installing-kubeflow/?utm_source=chatgpt.com "Installing Kubeflow"
[18]: https://github.com/triton-inference-server/server?utm_source=chatgpt.com "The Triton Inference Server provides an optimized cloud ..."
[19]: https://www.kubeflow.org/docs/components/trainer/legacy-v1/user-guides/mpi/?utm_source=chatgpt.com "MPI Training (MPIJob)"

Short summary — companies across finance, telecom, adtech, search, and cloud-native AI platforms run the CNCF/AI stacks you care about (Kubeflow, Ray, KServe, Seldon, NVIDIA/Triton, DeepSpeed, etc.). Those companies hire roles like **MLOps / ML Platform Engineer, ML Infrastructure Engineer, SRE/Platform Engineer, GPU Systems Engineer, and Distributed Systems Engineer** — all of which are a very strong fit for your skills in **Rust, Go, Python, C/C++**.

Below I map projects → example companies using them (real production adopters), then the common job titles and the concrete skills each role expects, plus highly actionable next steps you can use to apply and get interviews.

# Who uses what (project → representative production users)

* **Kubeflow** — used across enterprises in finance, telco, automotive and more to run training pipelines and reproducible ML platforms. (Kubeflow success stories / adoption pages). ([Accelerate Models to Market with Arrikto][1])
* **KServe (KFServing)** — used to build production inference platforms (example: Bloomberg’s inference platform was built on KServe). ([Bloomberg][2])
* **Seldon Core** — enterprise model-serving adoption (customers include Ford, PayPal, Johnson & Johnson in production use-cases). ([OpenUK][3])
* **Ray / Ray Serve (Anyscale)** — used for distributed training and model serving at scale (LinkedIn, Klaviyo, Notion and many startups/enterprises run Ray in production). ([Anyscale][4])
* **NVIDIA Triton Inference Server** — widely used for high-throughput GPU inference in production (customer stories like Siemens Energy + many cloud customers). ([NVIDIA][5])
* **DeepSpeed / Horovod / MPI** — used for distributed large-model training (DeepSpeed case studies include production speedups on SageMaker). ([Amazon Web Services, Inc.][6])

(Those are representative production adopters — many more companies use combinations of these tools.)

# Jobs companies hire for these stacks (titles → what they actually do)

* **ML Platform / ML Infrastructure Engineer**

  * Focus: build the platform data scientists use (Kubeflow, Argo, KServe, model registry, object stores).
  * Tech fit for you: Go + Python (control plane + APIs); some infra in C++/Rust for performance-critical components.
  * Typical tasks: build autoscaling, multi-tenant model serving, CI/CD for models, RBAC/isolation, SLOs and observability. (See ML platform job templates / descriptions). ([Yardstick][7])

* **MLOps / MLops Engineer**

  * Focus: deploy/monitor models, pipelines (Kubeflow/Katib/Argo), set up reproducible training, drift detection, model CI.
  * Tech fit: Python + scripting; Kubernetes, Helm, Terraform; familiarity with GPU stacks. ([DevsData][8])

* **GPU/Accelerator Systems Engineer (GPU Infrastructure Engineer)**

  * Focus: node lifecycle (GPU Operator, drivers, DCGM), device-plugin, runtime integration, high-density GPU clusters.
  * Tech fit: C/C++ or Go for operators and runtime pieces; some vendors use Python for tooling; Rust is increasingly used for infra components if you want to stand out. ([NVIDIA][9])

* **Distributed Systems / Compute Engineer (Ray/DeepSpeed/Volcano)**

  * Focus: scheduler, gang scheduling, RPC frameworks, data parallel / tensor parallel orchestration.
  * Tech fit: Python for Ray frameworks + Go/C++/Rust for lower-level pieces; strong networking and HPC knowledge. ([DevsData][8])

* **Inference / Model Serving Engineer (Triton/KServe/Seldon/Ray Serve)**

  * Focus: optimize latency, batching, multi-model endpoints, canary rollouts, GPU memory management.
  * Tech fit: C++ (Triton internals), Python + Go for controllers and glue layers; knowledge of TensorRT/PyTorch/TorchScript. ([NVIDIA][5])

# How your languages map to roles (quick guidance)

* **Go** — operator/controller work, Kubernetes controllers, cloud-native control-plane services, schedulers. Very valuable for ML platform and infra roles.
* **Python** — glue code, ML pipelines, model serving frameworks (Ray, Kubeflow components, model wrappers). Essential for MLOps and ML engineer positions.
* **C/C++** — high-performance inference engines, runtime integrations, TensorRT, Triton, custom CUDA kernels. Good for GPU runtime/driver-adjacent roles.
* **Rust** — increasingly used for safe, high-performance infra (telemetry collectors, network services, sandboxed runtimes). Unique differentiator if you can show applied projects.

# What hiring teams look for (concrete skills & keywords to search)

Search/filter job boards and recruiter tooling with these keywords:

* “ML Platform Engineer”, “MLOps Engineer”, “Machine Learning Infrastructure”, “GPU Infrastructure Engineer”, “Distributed Systems Engineer”, “Inference Engineer”, “Model Ops”, “Ray Engineer”, “Kubeflow Engineer”, “Triton Engineer”.
  Also include technology filters: **Kubernetes, GPUs, CUDA, NVIDIA GPU Operator, Triton, Ray, DeepSpeed, Kubeflow, KServe, Seldon**. For enterprise roles add cloud providers: **AWS Sagemaker, GKE/EKS/AKS**. (See standard JD templates for MLOps / ML Platform). ([DevsData][8])

# Example resume bullets tailored to your skills (use these verbatim or adapt)

* “Built a Kubernetes operator in **Go** to manage lifecycle of custom GPU-backed workloads, integrating device-plugin and DCGM metrics for automated health checks.”
* “Implemented distributed training orchestration using **Python** (Ray / MPIJob) to scale experiments across 32 GPUs, reducing experiment turnaround by X%.”
* “Developed low-level GPU telemetry collectors in **Rust**/**C++**, supplying Prometheus metrics and alarm integration to reduce silent OOM incidents.”
* “Optimized model inference pipeline using NVIDIA Triton and TensorRT, achieving 2–4× throughput improvement for batch inference.”
  These bullets map tightly to the roles above and speak the language of hiring managers.

# Interview and take-home tasks you should prepare for

* **Systems design (30–60 min)**: design a multi-tenant model-serving platform on Kubernetes (scheduling, quotas, isolation, autoscale, rollout strategy). Expect diagrams and tradeoffs.
* **Coding/whiteboard**: implement a simple Kubernetes controller/operator stub (Go) or actor-service in Ray (Python) — show your test and CI approach.
* **Performance debugging**: given a training job with poor GPU utilization, identify likely causes (PCIe/NIC topology, NCCL allreduce, driver mismatch, CPU starvation) and remediation.
* **Take-home**: containerize and deploy a model with Triton or Ray Serve to a K8s cluster; include latency tests and Prometheus metrics.
  Brush up on: Kubernetes primitives, device-plugin behavior, NCCL/collectives, CUDA basics (memory, pinned memory), and Ray internals if you target Ray-heavy teams.

# Concrete next actions (high ROI, in order)

1. **Portfolio + OSS PRs (1–2 weeks):**

   * Create 2 small public projects: (A) a k8s operator skeleton in **Go** that schedules GPU jobs and exports DCGM metrics; (B) a Ray Serve demo that scales an LLM or embedding endpoint with a small benchmark.
   * Open issues / fix minor bugs in the projects above (Kubeflow, KServe, Ray, GPU Operator) — maintainers prioritize small, well-tested PRs. This gives you direct recruiter credibility. (Search repos for “good first issue”.)
2. **Targeted job search (apply + network):**

   * Filter jobs by keywords above; target companies I cited (companies that run these stacks are often hiring platform and infra engineers). Include LinkedIn and company career pages (look at Bloomberg, NVIDIA partners, large enterprises using Ray/KServe). ([Bloomberg][2])
3. **Interview prep (2–4 weeks):** implement the interview tasks above, write one pager architecture notes for a model-serving platform, and prepare 2–3 story-driven resume examples (incident debugging, end-to-end deployment, perf win).

# Quick checklist of signals that get you hired fast

* Public code (GitHub) showing: Kubernetes + Go operator or Ray + Python service.
* Measurable outcomes on those repos (benchmarks, latency numbers, CI).
* PRs to CNCF/Anyscale/NVIDIA repos or meaningful issues triaged.
* Short, crisp write-up (1 page) describing an architecture you built + tradeoffs.

# Want me to do any of these right away?

I can immediately (pick one):

* produce **3 tailored resume bullets + a one-page cover note** for a specific job title you pick, or
* draft **a 2–3 week learning & PR plan** with exact issues in Kubeflow/Ray/NVIDIA repos to target (I’ll include repo links and “good first issue” style tasks).

Say which one and I’ll generate it now (I’ll include the exact commands, repo links, and PR plan).

[1]: https://www.arrikto.com/kubeflow-and-mlops-success-stories/?utm_source=chatgpt.com "Kubeflow and MLOps Success Stories - Arrikto"
[2]: https://www.bloomberg.com/company/stories/the-journey-to-build-bloombergs-ml-inference-platform-using-kserve-formerly-kfserving/?utm_source=chatgpt.com "The journey to build Bloomberg's ML Inference Platform ..."
[3]: https://openuk.uk/case-studies/case-study-seldon/?utm_source=chatgpt.com "Seldon from State of Open: The UK in 2023, Phase Two ..."
[4]: https://www.anyscale.com/blog/inference-graphs-at-linkedin-using-ray-serve?utm_source=chatgpt.com "Inference Graphs at LinkedIn Using Ray-Serve"
[5]: https://www.nvidia.com/en-us/customer-stories/siemens-energy-simplifies-safety-inspections-with-nvidia-triton-inference-server/?utm_source=chatgpt.com "Siemens Energy Simplifies Safety Inspections With NVIDIA"
[6]: https://aws.amazon.com/solutions/case-studies/mazzuma/?utm_source=chatgpt.com "Mazzuma Reduces Training Time from 23 Hours to 30 ..."
[7]: https://yardstick.team/compare-roles/mlops-engineer-vs-ml-platform-engineer-decoding-critical-ai-roles?utm_source=chatgpt.com "MLOps Engineer vs. ML Platform Engineer"
[8]: https://devsdata.com/mlops-engineer-job-description-template/?utm_source=chatgpt.com "MLOps Engineer Job Description Template"
[9]: https://www.nvidia.com/en-us/customer-stories/?utm_source=chatgpt.com "Customer Stories and Case Studies Powered by NVIDIA"

Here you go — all the projects/products we talked about with **official sites, GitHub, and docs** so you can go straight to source.

---

## ML platforms & serving

**Kubeflow** ([Kubeflow][1])

* Official site/docs: [https://www.kubeflow.org/](https://www.kubeflow.org/)
* Docs root: [https://www.kubeflow.org/docs/](https://www.kubeflow.org/docs/)
* GitHub (org): [https://github.com/kubeflow](https://github.com/kubeflow)
* Main repo: [https://github.com/kubeflow/kubeflow](https://github.com/kubeflow/kubeflow)

**KServe** (model serving, ex-KFServing) ([kserve.github.io][2])

* Site/docs: [https://kserve.github.io/website/](https://kserve.github.io/website/)
* GitHub: [https://github.com/kserve/kserve](https://github.com/kserve/kserve)

**Seldon Core** ([docs.seldon.ai][3])

* Product page: [https://www.seldon.io/solutions/core/](https://www.seldon.io/solutions/core/)
* Docs (Core 2): [https://docs.seldon.ai/seldon-core-2](https://docs.seldon.ai/seldon-core-2)
* GitHub: [https://github.com/SeldonIO/seldon-core](https://github.com/SeldonIO/seldon-core)

**Ray** (runtime + Ray Serve etc.) ([GitHub][4])

* Main site/docs: [https://www.ray.io/](https://www.ray.io/)
* Docs: [https://docs.ray.io/](https://docs.ray.io/)
* GitHub: [https://github.com/ray-project/ray](https://github.com/ray-project/ray)

**KubeRay** (Ray on Kubernetes) ([GitHub][5])

* Docs entry (now in Ray docs): [https://docs.ray.io/en/latest/cluster/kubernetes/index.html](https://docs.ray.io/en/latest/cluster/kubernetes/index.html)
* Legacy KubeRay docs: [https://ray-project.github.io/kuberay/](https://ray-project.github.io/kuberay/)
* GitHub: [https://github.com/ray-project/kuberay](https://github.com/ray-project/kuberay)

**NVIDIA Triton Inference Server** ([GitHub][6])

* Docs: [https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/)
* GitHub: [https://github.com/triton-inference-server/server](https://github.com/triton-inference-server/server)
* NGC page: [https://catalog.ngc.nvidia.com/orgs/nvidia/containers/tritonserver](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/tritonserver)

**BentoML** (Pythonic serving) ([GitHub][7])

* Site: [https://www.bentoml.com/](https://www.bentoml.com/)
* Docs: [https://docs.bentoml.com/](https://docs.bentoml.com/)
* GitHub: [https://github.com/bentoml/BentoML](https://github.com/bentoml/BentoML)

---

## GPU infrastructure & telemetry

**NVIDIA GPU Operator** ([GitHub][8])

* GitHub: [https://github.com/NVIDIA/gpu-operator](https://github.com/NVIDIA/gpu-operator)
* Install docs: [https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/getting-started.html](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/getting-started.html)

**NVIDIA Kubernetes device plugin** ([GitHub][9])

* GitHub: [https://github.com/NVIDIA/k8s-device-plugin](https://github.com/NVIDIA/k8s-device-plugin)

**NVIDIA DCGM (Data Center GPU Manager)** ([GitHub][10])

* GitHub: [https://github.com/NVIDIA/DCGM](https://github.com/NVIDIA/DCGM)

**NVIDIA DCGM Exporter** (Prometheus metrics) ([GitHub][11])

* GitHub: [https://github.com/NVIDIA/dcgm-exporter](https://github.com/NVIDIA/dcgm-exporter)
* Docs: [https://docs.nvidia.com/datacenter/dcgm/latest/gpu-telemetry/dcgm-exporter.html](https://docs.nvidia.com/datacenter/dcgm/latest/gpu-telemetry/dcgm-exporter.html)

**Volcano** (batch/HPC/AI scheduler) ([GitHub][12])

* Site/docs: [https://volcano.sh/](https://volcano.sh/)
* Installation docs: [https://volcano.sh/en/docs/installation/](https://volcano.sh/en/docs/installation/)
* GitHub: [https://github.com/volcano-sh/volcano](https://github.com/volcano-sh/volcano)

---

## Distributed training frameworks

**DeepSpeed** ([GitHub][13])

* Site: [https://www.deepspeed.ai/](https://www.deepspeed.ai/)
* GitHub: [https://github.com/deepspeedai/DeepSpeed](https://github.com/deepspeedai/DeepSpeed)
* Examples: [https://github.com/deepspeedai/DeepSpeedExamples](https://github.com/deepspeedai/DeepSpeedExamples)

**Horovod** ([GitHub][14])

* Site: [https://horovod.ai/](https://horovod.ai/)
* GitHub: [https://github.com/horovod/horovod](https://github.com/horovod/horovod)

(For MPI you’ll usually rely on your distro’s OpenMPI / MPICH packages or vendor-provided builds rather than a single canonical repo.)

---

## Pipelines, workflows & CI/CD

**Argo Workflows** ([GitHub][15])

* Site/docs: [https://argoproj.github.io/workflows/](https://argoproj.github.io/workflows/)
* GitHub: [https://github.com/argoproj/argo-workflows](https://github.com/argoproj/argo-workflows)

**Kubeflow Pipelines** ([GitHub][16])

* GitHub: [https://github.com/kubeflow/pipelines](https://github.com/kubeflow/pipelines)
* Docs: [https://www.kubeflow.org/docs/components/pipelines/](https://www.kubeflow.org/docs/components/pipelines/)

**Tekton Pipelines** ([GitHub][17])

* Tekton org: [https://github.com/tektoncd](https://github.com/tektoncd)
* Pipelines repo: [https://github.com/tektoncd/pipeline](https://github.com/tektoncd/pipeline)
* Docs: [https://tekton.dev/docs/pipelines/](https://tekton.dev/docs/pipelines/)

---

If you want to turn this into a personal “AI infra roadmap”, the next move is usually to pick 2–3 of these (e.g. **Ray + KubeRay**, **GPU Operator + DCGM**, **Triton or KServe**) and wire them together in a small lab cluster, then start sending PRs to whichever repo feels most comfortable from the codebase.

[1]: https://www.kubeflow.org/?utm_source=chatgpt.com "Kubeflow"
[2]: https://kserve.github.io/website/?utm_source=chatgpt.com "KServe"
[3]: https://docs.seldon.ai/seldon-core-2?utm_source=chatgpt.com "Production-ready ML Serving Framework | Seldon Core 2"
[4]: https://github.com/ray-project/ray?utm_source=chatgpt.com "Ray is an AI compute engine. Ray consists of a core ..."
[5]: https://github.com/ray-project/kuberay?utm_source=chatgpt.com "ray-project/kuberay: A toolkit to run ..."
[6]: https://github.com/triton-inference-server/server?utm_source=chatgpt.com "The Triton Inference Server provides an optimized cloud ..."
[7]: https://github.com/bentoml/BentoML?utm_source=chatgpt.com "bentoml/BentoML: The easiest way to serve AI apps and ..."
[8]: https://github.com/NVIDIA/gpu-operator?utm_source=chatgpt.com "NVIDIA/gpu-operator"
[9]: https://github.com/NVIDIA/k8s-device-plugin?utm_source=chatgpt.com "NVIDIA device plugin for Kubernetes"
[10]: https://github.com/NVIDIA/DCGM?utm_source=chatgpt.com "NVIDIA Data Center GPU Manager (DCGM) is a project for ..."
[11]: https://github.com/NVIDIA/dcgm-exporter?utm_source=chatgpt.com "NVIDIA/dcgm-exporter: NVIDIA GPU metrics exporter for ..."
[12]: https://github.com/volcano-sh/volcano?utm_source=chatgpt.com "volcano-sh/volcano: A Cloud Native Batch System (Project ..."
[13]: https://github.com/deepspeedai/DeepSpeed?utm_source=chatgpt.com "deepspeedai/DeepSpeed"
[14]: https://github.com/horovod/horovod?utm_source=chatgpt.com "horovod/horovod: Distributed training framework for ..."
[15]: https://github.com/argoproj/argo-workflows?utm_source=chatgpt.com "argoproj/argo-workflows: Workflow Engine for Kubernetes"
[16]: https://github.com/kubeflow/pipelines?utm_source=chatgpt.com "Machine Learning Pipelines for Kubeflow"
[17]: https://github.com/tektoncd/pipeline?utm_source=chatgpt.com "tektoncd/pipeline: A cloud-native Pipeline resource."
