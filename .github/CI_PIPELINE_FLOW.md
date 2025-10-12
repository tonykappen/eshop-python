# CI/CD Pipeline Flow Visualization

This document visualizes the complete CI/CD pipeline flow.

## 🔄 Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                    GitHub Push / Pull Request                       │
│                                                                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                   Trigger GitHub Actions Workflows                  │
│                                                                     │
└─────┬───────────────┬───────────────┬──────────────┬────────────────┘
      │               │               │              │
      ▼               ▼               ▼              ▼
┌───────────┐   ┌───────────┐   ┌──────────┐   ┌──────────┐
│   Code    │   │ Security  │   │   Type   │   │  Tests   │
│  Quality  │   │  Checks   │   │ Checking │   │   with   │
│           │   │           │   │          │   │ Coverage │
└─────┬─────┘   └─────┬─────┘   └────┬─────┘   └────┬─────┘
      │               │               │              │
      │ ✅ Pass       │ ✅ Pass       │ ✅ Pass      │ ✅ Pass
      │               │               │              │
      └───────────────┴───────────────┴──────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  Quality Gate  │
                    │   All Checks   │
                    │   Must Pass    │
                    └────────┬───────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
          ✅ Success                  ❌ Failure
        (Can Merge)              (Cannot Merge)
```

## 📊 Detailed Job Flow

### Main CI Pipeline (`ci.yml`)

```
                        ┌─────────────────────┐
                        │  Trigger: Push/PR   │
                        └──────────┬──────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    │    Parallel Execution       │
                    │              │              │
        ┌───────────▼─────┐   ┌───▼────────┐   ┌▼──────────────┐
        │                 │   │            │   │               │
┌───────▼─────────┐  ┌────▼────────┐  ┌───▼──────────┐  ┌─────▼─────────┐
│  lint-and-      │  │  security   │  │  type-check  │  │     test      │
│    format       │  │             │  │              │  │               │
│                 │  │             │  │              │  │               │
│ • Ruff lint     │  │ • Bandit    │  │ • MyPy       │  │ • pytest      │
│ • Ruff format   │  │ • Report    │  │ • Types      │  │ • Coverage    │
│ • Black check   │  │ • Upload    │  │ • Warnings   │  │ • Services    │
│ • isort check   │  │   artifact  │  │              │  │   - PostgreSQL│
│                 │  │             │  │              │  │   - Redis     │
│ ⚠️ MUST PASS    │  │ ℹ️ Info     │  │ ⚠️ Warning   │  │   - RabbitMQ  │
│                 │  │             │  │              │  │               │
└────────┬────────┘  └──────┬──────┘  └───────┬──────┘  │ ⚠️ MUST PASS  │
         │                  │                 │         │ ✅ 80% MIN    │
         │ ✅ Pass          │ ✅ Pass         │ ✅ Pass │               │
         │                  │                 │         └───────┬───────┘
         │                  │                 │                 │
         └──────────────────┴─────────────────┴─────────────────┘
                                   │
                                   │ All Jobs Complete
                                   │
                          ┌────────▼─────────┐
                          │  quality-gate    │
                          │                  │
                          │ Validates:       │
                          │ • All jobs pass  │
                          │ • No failures    │
                          │ • Coverage ≥80%  │
                          │                  │
                          └────────┬─────────┘
                                   │
                      ┌────────────┴──────────────┐
                      │                           │
                      ▼                           ▼
              ✅ All Checks Pass          ❌ Some Checks Failed
              ┌──────────────┐            ┌─────────────────┐
              │  Ready to    │            │  Fix Required   │
              │    Merge!    │            │  Cannot Merge   │
              └──────────────┘            └─────────────────┘
```

## 🎯 Quality Gate Details

### Coverage Enforcement Flow

```
┌──────────────────────┐
│   Run Test Suite    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Calculate Coverage   │
│   (pytest-cov)       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Coverage >= 80%?    │
└──────────┬───────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌───────┐     ┌───────┐
│  YES  │     │  NO   │
└───┬───┘     └───┬───┘
    │             │
    ▼             ▼
┌───────┐     ┌─────────────┐
│ PASS  │     │    FAIL     │
│  ✅   │     │     ❌      │
└───────┘     │ Block Merge │
              └─────────────┘
```

## 🔍 Pre-Commit Hook Flow

```
┌──────────────────┐
│  git commit      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Pre-commit      │
│  Hook Trigger    │
└────────┬─────────┘
         │
         ├─────► trailing-whitespace ──► ✅ Pass ──┐
         ├─────► end-of-file-fixer ───► ✅ Pass ──┤
         ├─────► check-yaml ─────────► ✅ Pass ──┤
         ├─────► black ──────────────► ✅ Pass ──┤
         ├─────► isort ──────────────► ✅ Pass ──┤
         ├─────► ruff ───────────────► ✅ Pass ──┤
         ├─────► mypy ───────────────► ✅ Pass ──┤
         └─────► bandit ─────────────► ✅ Pass ──┤
                                                  │
         ┌────────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│  All Hooks Pass? │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌─────────┐
│  YES   │ │   NO    │
└───┬────┘ └────┬────┘
    │           │
    ▼           ▼
┌────────┐ ┌──────────┐
│ Commit │ │  Abort   │
│   ✅   │ │  Commit  │
└────────┘ │    ❌    │
           │          │
           │ Fix &    │
           │ Retry    │
           └──────────┘
```

## 📋 Workflow Trigger Matrix

```
┌──────────────────────────────────────────────────────────────┐
│                    Workflow Triggers                         │
├──────────────────┬───────────────────────────────────────────┤
│  Workflow        │  Triggers                                 │
├──────────────────┼───────────────────────────────────────────┤
│  ci.yml          │  • Push: main, master, develop,          │
│                  │    docker-fixes                           │
│                  │  • PR: main, master, develop              │
├──────────────────┼───────────────────────────────────────────┤
│  code-quality    │  • PR: opened, sync, reopened             │
│  .yml            │  • Push: main, master                     │
├──────────────────┼───────────────────────────────────────────┤
│  pre-commit      │  • PR: all                                │
│  .yml            │  • Push: main, master, develop            │
├──────────────────┼───────────────────────────────────────────┤
│  status-checks   │  • PR: opened, sync, reopened             │
│  .yml            │  • Push: main, master, develop            │
└──────────────────┴───────────────────────────────────────────┘
```

## 🚀 Developer Workflow

```
┌────────────────┐
│  Local Dev     │
│  Write Code    │
└───────┬────────┘
        │
        ▼
┌────────────────────┐
│ Before Commit:     │
│ ./ci-check.sh      │
└───────┬────────────┘
        │
    ┌───┴───┐
    │       │
    ▼       ▼
┌──────┐ ┌─────────┐
│ Pass │ │  Fail   │
└───┬──┘ └────┬────┘
    │         │
    │         └──► Fix Issues ──┐
    │                           │
    ▼                           │
┌────────────────┐              │
│  git commit    │◄─────────────┘
│  (pre-commit)  │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  git push      │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Create PR     │
└───────┬────────┘
        │
        ▼
┌────────────────────┐
│  CI Runs on        │
│  GitHub Actions    │
└───────┬────────────┘
        │
    ┌───┴────┐
    │        │
    ▼        ▼
┌──────┐ ┌────────┐
│ Pass │ │  Fail  │
└───┬──┘ └────┬───┘
    │         │
    │         └──► Fix & Push ──┐
    │                           │
    ▼                           │
┌────────────┐                  │
│  Review    │◄─────────────────┘
│  Approve   │
└─────┬──────┘
      │
      ▼
┌─────────────┐
│   Merge!    │
└─────────────┘
```

## 🎨 Service Architecture (Test Job)

```
┌───────────────────────────────────────────────────────────┐
│                   GitHub Actions Runner                   │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Test Environment                       │ │
│  │                                                     │ │
│  │  ┌──────────┐   ┌─────────┐   ┌──────────────┐   │ │
│  │  │          │   │         │   │              │   │ │
│  │  │PostgreSQL│   │  Redis  │   │  RabbitMQ    │   │ │
│  │  │    :5432 │   │  :6379  │   │ :5672,:15672 │   │ │
│  │  │          │   │         │   │              │   │ │
│  │  └────┬─────┘   └────┬────┘   └──────┬───────┘   │ │
│  │       │              │               │           │ │
│  │       └──────────────┼───────────────┘           │ │
│  │                      │                           │ │
│  │              ┌───────▼────────┐                  │ │
│  │              │                │                  │ │
│  │              │   Test Suite   │                  │ │
│  │              │    (pytest)    │                  │ │
│  │              │                │                  │ │
│  │              └───────┬────────┘                  │ │
│  │                      │                           │ │
│  │                      ▼                           │ │
│  │              ┌───────────────┐                   │ │
│  │              │   Coverage    │                   │ │
│  │              │   Report      │                   │ │
│  │              │   (≥80%)      │                   │ │
│  │              └───────────────┘                   │ │
│  └─────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────┘
```

## 📊 Coverage Calculation Flow

```
┌─────────────┐
│  Run Tests  │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  pytest-cov      │
│  Instrument Code │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Track Executed  │
│  Lines           │
└──────┬───────────┘
       │
       ▼
┌──────────────────────┐
│  Calculate:          │
│                      │
│  Coverage = (Lines   │
│  Executed / Total    │
│  Lines) * 100        │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Generate Reports:   │
│  • Terminal          │
│  • HTML (detailed)   │
│  • XML (Codecov)     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Check Threshold:    │
│  Coverage >= 80%?    │
└──────┬───────────────┘
       │
   ┌───┴────┐
   │        │
   ▼        ▼
┌──────┐ ┌──────┐
│ PASS │ │ FAIL │
└──────┘ └──────┘
```

## 🔐 Security Check Flow

```
┌──────────────┐
│  Scan Code   │
│   (Bandit)   │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  Check for:      │
│  • Hardcoded     │
│    secrets       │
│  • SQL injection │
│  • XSS risks     │
│  • Known CVEs    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Generate Report │
│  (JSON + Screen) │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Upload Artifact │
│  (30 days)       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Severity:       │
│  • High ⚠️       │
│  • Medium ⚠️     │
│  • Low ℹ️        │
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  Non-blocking    │
│  (Informational) │
└──────────────────┘
```

## 📈 Performance Optimization

```
┌──────────────────┐
│  Cache Strategy  │
└────────┬─────────┘
         │
    ┌────┼─────┐
    │    │     │
    ▼    ▼     ▼
┌───────────┐ ┌──────────┐ ┌─────────────┐
│  Poetry   │ │  Pre-    │ │  Python     │
│  Deps     │ │  commit  │ │  Setup      │
│  Cache    │ │  Cache   │ │  Cache      │
└─────┬─────┘ └────┬─────┘ └──────┬──────┘
      │            │              │
      └────────────┴──────────────┘
                   │
                   ▼
        ┌──────────────────┐
        │  Faster CI Runs  │
        │  • 5-7 min avg   │
        │  • Parallel jobs │
        │  • Smart caching │
        └──────────────────┘
```

## 🎯 Summary

This pipeline provides:

- ✅ **Comprehensive quality checks**
- ✅ **80% minimum coverage enforcement**
- ✅ **Security vulnerability scanning**
- ✅ **Type safety validation**
- ✅ **Automated PR checks**
- ✅ **Local validation tools**
- ✅ **Branch protection integration**

**Average CI Runtime:** 5-7 minutes  
**Coverage Requirement:** 80% minimum  
**Quality Gates:** 7 enforced checks  
**Services:** 3 (PostgreSQL, Redis, RabbitMQ)

---

**Visual Guide Version:** 1.0  
**Last Updated:** 2025-10-12

