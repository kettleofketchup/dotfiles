---
name: gitlab-ci
description: "GitLab CI/CD multi-project orchestration AND CI/CD Catalog component publishing. This skill should be used when writing trigger jobs, cross-pipeline gating, tag cascades, strategy:depend, multi-repo .gitlab-ci.yml patterns, or publishing reusable components to the GitLab CI/CD Catalog."
---

# GitLab CI Multi-Project Pipelines

## Overview

Orchestrate CI/CD pipelines across multiple GitLab projects using trigger jobs,
cross-pipeline dependencies, and pipeline subscriptions. Covers patterns from simple
downstream triggers to complex tag cascade orchestration.

## Trigger Mechanism Decision Tree

```
Need cross-project pipeline orchestration?
├── One repo triggers another's pipeline
│   ├── Fire-and-forget → trigger: (default)
│   └── Wait for completion → trigger: + strategy: depend
├── Repo B depends on Repo A's artifacts
│   └── needs: project: + job: + ref: + artifacts: true
├── Orchestrate multiple repos in sequence
│   └── Orchestrator pattern: parent triggers children via stages
├── Auto-trigger on upstream completion
│   └── Pipeline subscriptions (Settings > CI/CD)
└── Tag/release cascade across repos
    └── Orchestrator with strategy: depend per stage
```

## Core Patterns

### 1. Downstream Trigger (Fire-and-Forget)

```yaml
trigger_downstream:
  stage: deploy
  trigger:
    project: my-group/downstream-project
    branch: main
```

### 2. Synchronous Trigger (Wait for Completion)

```yaml
trigger_downstream:
  stage: deploy
  trigger:
    project: my-group/downstream-project
    branch: main
    strategy: depend  # Parent job status mirrors downstream result
```

### 3. Cross-Project Artifact Dependency

```yaml
# In downstream project - fetch artifacts from upstream
consume_artifacts:
  stage: test
  script: cat artifact.txt
  needs:
    - project: my-group/upstream-project
      job: build_artifacts
      ref: main
      artifacts: true
```

### 4. Conditional Triggers

```yaml
trigger_on_tag:
  stage: deploy
  trigger:
    project: my-group/downstream-project
  rules:
    - if: $CI_COMMIT_TAG
```

### 5. Passing Variables Downstream

```yaml
trigger_with_vars:
  stage: deploy
  variables:
    UPSTREAM_VERSION: $CI_COMMIT_TAG
    UPSTREAM_REF: $CI_COMMIT_SHA
  trigger:
    project: my-group/downstream-project
```

## Pipeline Auto-Cancel and Interruptible Jobs

Cancel redundant pipelines when a new commit is pushed to the same branch.

### Setup

```yaml
workflow:
  auto_cancel:
    on_new_commit: interruptible  # Cancel only interruptible jobs

default:
  interruptible: true  # All jobs interruptible by default
```

### `workflow:auto_cancel:on_new_commit` (GitLab 16.10+)

| Value | Behavior |
|-------|----------|
| `conservative` (default) | Cancel entire pipeline, but only if no `interruptible: false` jobs have started |
| `interruptible` | Cancel only individual jobs with `interruptible: true` |
| `none` | Never auto-cancel |

### `interruptible` keyword

- Set at `default:` level to apply to all jobs
- Override per-job with `interruptible: false` for release-critical jobs (publish, deploy)
- Tag pipelines are unaffected — you don't push new commits to a tag ref
- When `on_new_commit: interruptible`, only jobs marked `interruptible: true` are cancelled; `false` jobs keep running

### Example: Protect only publish jobs

```yaml
default:
  interruptible: true

publish-binary:
  stage: publish
  interruptible: false  # Never cancel mid-upload
  script: curl --upload-file ...
```

## Key Constraints

- Max 1000 downstream pipelines per hierarchy
- Parent-child pipelines: max depth of 2 levels
- Triggering user needs Developer access in downstream project
- `needs: project:` requires GitLab 15.9+ and job token scope allowlist
- Cannot use CI/CD variables in `include:` sections
- Pipeline subscriptions: max 2 per project (self-managed configurable)
- Pipeline subscriptions only trigger on tag pipeline completion

## CI/CD Catalog Component Publishing

Building a reusable catalog component that other projects `include:` is its own
workflow with self-managed-GitLab gotchas (heterogeneous runner fleets,
internal CA trust, the `release:` keyword needing release-cli image, catalog
browse-API vs include-resolution being independent). See
[CI/CD Catalog Publishing Reference](references/cicd-catalog-publishing.md)
for the full pattern: `.gitlab-ci.yml` template, yamllint config, CI variable
setup, the dual-mode-script trick for shell-vs-docker executors, the
SSL_CERT_FILE pattern for org-CA trust, and failure-recovery via force-retag.

Key invariants:

- **Publish job needs `image: registry.gitlab.com/gitlab-org/release-cli:latest`** — the default `docker:latest` lacks release-cli; the `release:` keyword fails with `release-cli: not found` otherwise.
- **Org CA must be trusted by release-cli/glab**, not by writing to `/etc/ssl/certs` (read-only on shell executors) — use a temp bundle + `export SSL_CERT_FILE=<bundle>`. The export survives into the `release:` step.
- **CI variable for the CA must be Type: File** so `$VAR` holds a path and `[ -f "$VAR" ]` checks pass; Protect must match the publishing tag's protection level (usually OFF).
- **Catalog browse API (`/api/v4/ci/catalog/resources`) may 404 on some tiers** without breaking `include: component:` — verify via the lint API (`POST /api/v4/projects/<id>/ci/lint`) instead.

## References

Detailed patterns, templates, and architecture-specific configurations:

- [Multi-Project Trigger Reference](references/multi-project-triggers.md) — all trigger
  mechanisms, variable passing, artifact sharing, pipeline subscriptions
- [Cross-Pipeline Gating Patterns](references/cross-pipeline-gating.md) — orchestrator
  pattern, sequential stage triggers, tag cascade, scheduled rebuilds
- [Edge Infrastructure Templates](references/edge-infra-patterns.md) — ready-to-use
  templates for multi-repo Nix flake architecture with builder/os/k3s-core/services
- [CI/CD Catalog Publishing](references/cicd-catalog-publishing.md) — building +
  publishing reusable components, runner-fleet quirks, CA trust for release-cli, recovery

## External Docs

- [GitLab Downstream Pipelines](https://docs.gitlab.com/ci/pipelines/downstream_pipelines/)
- [Pipeline Architecture](https://docs.gitlab.com/ci/pipelines/pipeline_architectures/)
- [CI/CD Pipelines](https://docs.gitlab.com/ci/pipelines/)
