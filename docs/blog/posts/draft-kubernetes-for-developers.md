---
title: "Kubernetes for people who did not ask for Kubernetes"
date:
  created: 2026-09-19
authors:
  - vivek
categories:
  - Kubernetes
tags:
  - kubernetes
  - onboarding
  - devex
draft: true
---

<!--
DRAFT. Not published while `draft: true` is set. Visible with `mkdocs serve`.
Replace every [bracketed prompt] with your own experience, then remove `draft: true`.
-->

[Opening: a moment where a developer hit a Kubernetes wall that had nothing to do with their code. An error message, a YAML file, a kubectl command they had to learn just to see logs.]

<!-- more -->

## What developers actually needed

[List the two or three things developers really wanted: deploy, see logs, roll back. How far was that from what the cluster asked of them?]

## Where the abstraction leaked

[Specific examples of Kubernetes concepts developers were forced to understand: namespaces, resource limits, ingress, secrets, probes. Which ones caused the most support requests?]

## What we put in front of the cluster

[Helm charts, a CLI wrapper, a template repo, an internal portal? What did it hide, and what did it deliberately not hide?]

## The mistake I made

[Something you got wrong. Over-abstracting? Under-documenting? A default that bit people later?]

## Takeaways

- [One-line lesson]
- [One-line lesson]
